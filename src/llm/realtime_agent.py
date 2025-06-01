## Taken from https://github.com/alexzhang13/videogamebench

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any
from src.utils import is_same_image

from src.emulators.dos.browser_controller import BrowserController
from src.llm.fake_llm_client import FakeLLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Message:
    """Container for a message in the conversation history."""
    
    def __init__(self, role: str, content: Any, has_image: bool = False, tokens: int = 0):
        self.role = role
        self.content = content
        self.has_image = has_image
        self.tokens = tokens  # Approximate token count
        self.timestamp = datetime.now()
        
    def __str__(self):
        if isinstance(self.content, str):
            preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
            return f"{self.role}: {preview}"
        else:
            return f"{self.role}: [Complex content with image={self.has_image}]"

class VideoGameBenchAgent:
    """
    Base class for all VG agents.
    """
    def __init__(self, 
                 game: str, 
                 headless: bool = False, 
                 log_dir: Optional[Path] = None,
                ):
        # Set up logging directory
        if log_dir is None:
            self.log_dir = Path("logs") / f"{game.lower()}" / datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.log_dir = log_dir

        # Set up file logger
        self.file_logger = self._setup_file_logger()
        self.file_logger.info(f"Initializing {self.__class__.__name__}")

        # Initialize LLM client
        self.llm_client = FakeLLMClient(
            log_dir=self.log_dir / "llm",
        )

        # Common attributes
        self.headless = headless # TODO: make this do something
        self.game = game
        
        self.step_count = 0
        
        # Create consolidated log files
        self.reflection_log_file = self.log_dir / "reflections.txt"
        self.reflection_log_file.touch()

        logger.info(f"{self.__class__.__name__} initialized. Logging to: {self.log_dir}")


    def _setup_file_logger(self) -> logging.Logger:
        """Set up a file logger for this session."""
        file_logger = logging.getLogger(f"{self.__class__.__name__.lower()}_{id(self)}")
        file_logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.log_dir / "agent_session.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add handler to logger
        file_logger.addHandler(file_handler)
        
        return file_logger

class WebBrowsingAgent(VideoGameBenchAgent):
    """
    Agent that uses the ReACT method to browse the web and complete tasks.
    """
    def __init__(
        self,
        game: str,
        headless: bool = False,
        lite: bool = False,
        press_key_delay: int = 100,
        log_dir: Optional[Path] = None,
    ):
        """
        Initialize the web browsing agent.
        
        Args:
            model: The LLM model to use
            api_key: The API key for the model provider
            game: The name of the game to play
            headless: Whether to run the browser in headless mode
            temperature: The temperature for LLM generation
            max_tokens: The maximum number of tokens to generate
            max_history_tokens: The maximum number of tokens to keep in history
            context_window: Number of recent timesteps to include
            lite: Whether to run in lite mode with reduced functionality
            log_dir: Optional custom log directory path
            enable_ui: Whether to enable the UI monitor
            record: Whether to record the gameplay session
        """
        super().__init__(
            game=game,
            headless=headless,
            log_dir=log_dir,
        )
        
        # Initialize browser controller
        self.browser = BrowserController(headless=headless)

        # Game-specific settings
        self.press_key_delay = press_key_delay
        
        self.lite = lite
        self.lite_counter = 0

    async def start(self, initial_url: str) -> None:
        """
        Start the agent by initializing the browser.
        """
        self.file_logger.info("Starting browser")
        await self.browser.start()
        
        await self.reset(initial_url)


    async def reset(self, initial_url: str) -> None:
        self.file_logger.info(f"Navigating to URL: {initial_url}")
        
        # Navigate to the initial URL
        start_time = time.time()
        await self.browser.navigate(initial_url)
        load_time = time.time() - start_time
        self.file_logger.info(f"Page loaded in {load_time:.2f}s")

        # Pre-loaded actions based on game
        await self.browser.pre_load(self.game)

    async def stop(self) -> None:
        """
        Stop the agent by closing the browser.
        """
        self.file_logger.info("Stopping browser")
        await self.browser.close()
        
    async def run_episode(self, max_steps: int = 400, checkpoints: Optional[List[str]] = None) -> None:
        """
        Run an episode with the ReACT and memory agent. 
        TODO: Eventually move this into the evaluator.
        
        Args:
            task: The task to execute
            max_steps: The maximum number of steps to take
        """
        # Get initial screenshot
        screenshot = await self.browser.get_screenshot()
        screenshots = [screenshot]
        
        # Save screenshot
        screenshot_dir = self.log_dir / "game_screen"
        monitor_dir = self.log_dir / "monitor"
        screenshot_dir.mkdir(exist_ok=True)
        monitor_dir.mkdir(exist_ok=True)
        screenshot_path = screenshot_dir / f"screenshot_initial.jpg"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot)
        self.file_logger.info(f"Saved initial screenshot to {screenshot_path}")

        if self.lite:
            await self.browser.press_key("Alt+Pause", delay_ms=0)

        for step in range(max_steps):
            self.step_count = step + 1
            self.file_logger.info(f"Step {self.step_count}/{max_steps}")
            logger.info(f"Step {self.step_count}/{max_steps}")
            
            start_time = time.time()
            
            react_response = await self.llm_client.generate_react_response(
                screenshot=screenshots
            )
            response_time = time.time() - start_time
            
            # Log the thought process
            action = react_response.get("action", "")
            action_input = react_response.get("action_input", "")
            
            self.file_logger.info(f"Response time: {response_time:.2f}s")
            self.file_logger.info(f"Action: {action}, Input: {action_input}")
            logger.info(f"Action: {action}, Input: {action_input}")
            
            # Execute the action
            action_start_time = time.time()
            observation, screenshots = await self._execute_action(action, action_input)
            action_time = time.time() - action_start_time
            
            self.file_logger.info(f"Action execution time: {action_time:.2f}s")
            self.file_logger.info(f"Observation: {observation}")
            logger.info(f"Observation: {observation}")
            
            ### NEW ACTION
            # Under real benchmark (not lite), take screenshot here
            if not screenshots or len(screenshots) == 0:
                screenshot = await self.browser.get_screenshot()
                screenshots = [screenshot]
                # Save screenshot
                screenshot_path = screenshot_dir / f"game_screen_step_{self.step_count}.jpg"
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot)
                self.file_logger.info(f"Saved step {self.step_count} screenshot to {screenshot_path}")
            
            # Check if the task is complete
            if checkpoints and is_same_image(observation, checkpoints[-1]):
                self.file_logger.info("Task completed successfully!")
                logger.info("Task completed successfully!")
                break
                
        if step == max_steps - 1:
            self.file_logger.warning("Reached maximum number of steps without completing the task.")
            logger.warning("Reached maximum number of steps without completing the task.")
    
    async def _execute_action(self, action: str, action_input: str) -> str:
        """Execute an action and return the observation."""
        try:
            self.file_logger.info(f"Executing action: {action} with input: {action_input}")
            
            # Execute the action
            result = None
            screenshots = []
            if self.lite:
                self.file_logger.info("Lite mode is enabled, pausing game with Alt+Pause key...")
                await self.browser.press_key("Alt+Pause", delay_ms=0)
                await asyncio.sleep(0.01)

            if action == "nope":
                self.file_logger.info("Agent decided to skip this step.")

            elif action == "click":
                x, y = self.browser.current_mouse_position
                click_options = {}
                if action_input:
                    if "right" in action_input.lower():
                        click_options["button"] = "right"
                    
                    modifiers = []
                    if "shift" in action_input.lower():
                        modifiers.append("Shift")
                    if "ctrl" in action_input.lower():
                        modifiers.append("Control")
                    if "alt" in action_input.lower():
                        modifiers.append("Alt")
                    if modifiers:
                        click_options["modifiers"] = modifiers
                else:
                    click_options = None
                
                self.file_logger.info(f"Clicking at coordinates: ({x}, {y}) with options: {click_options}")
                await self.browser.click(x, y, click_options)
                result = f"Mouse clicked at ({x}, {y}) with options: {click_options}"

            elif action == "move":
                x, y = map(float, action_input.split(","))
                x_start, y_start = self.browser.current_mouse_position
                self.file_logger.info(f"Moving mouse from: ({x_start}, {y_start}) to: ({x}, {y})")
                await self.browser.move_mouse(x, y)
                result = f"Mouse moved to ({x}, {y})"

            elif action == "drag":
                x, y = map(float, action_input.split(","))
                x_start, y_start = self.browser.current_mouse_position
                self.file_logger.info(f"Dragging from: ({x_start}, {y_start}) to: ({x}, {y})")
                await self.browser.drag(x, y)
                result = f"Mouse dragged to ({x}, {y})"

            elif action == "scroll_down":
                amount = int(action_input)
                self.file_logger.info(f"Scrolling down: {amount}px")
                await self.browser.scroll_down(amount)
                result = f"Scrolled down {amount} pixels."

            elif action == "scroll_up":
                amount = int(action_input)
                self.file_logger.info(f"Scrolling up: {amount}px")
                await self.browser.scroll_up(amount)
                result = f"Scrolled up {amount} pixels."

            elif action == "write":
                self.file_logger.info(f"Typing text: {action_input}")
                await self.browser.type_text(action_input)
                result = f"Typed: {action_input}"

            elif action == "press_key":
                self.file_logger.info(f"Pressing key: {action_input}")
                if "," in action_input:
                    keys = action_input.split(",")
                    for key in keys:
                        await self.browser.press_key(key.strip(), lite_mode=self.lite, delay_ms=self.press_key_delay)
                        for _ in range(self.num_screenshots_per_action): 
                            screenshot = await self.browser.get_screenshot()
                            screenshots.append(screenshot)
                            await asyncio.sleep(0.05) 
                    result = f"Pressed keys: {action_input}"
                else:
                    await self.browser.press_key(action_input, lite_mode=self.lite, delay_ms=self.press_key_delay)
                    result = f"Pressed key: {action_input}"

            elif action == "hold_key":
                parts = action_input.split(",")
                key = parts[0]
                duration = float(parts[1]) if len(parts) > 1 else 0.5
                self.file_logger.info(f"Holding key: {key} for {duration}s")
                await self.browser.press_key(key, lite_mode=self.lite, delay_ms=duration)
                result = f"Held key {key} for {duration} seconds"

            elif action == "done":
                self.file_logger.info("Agent marked task as complete")
                result = "Task completed."

            elif action == "error":
                self.file_logger.error(f"Agent reported error: {action_input}")
                result = f"Error occurred: {action_input}"

            else:
                self.file_logger.warning(f"Unknown action: {action}")
                result = f"Unknown action: {action}"

            if self.lite:
                start_time = time.time()
                # Take screenshots for approximately 0.3 seconds
                for _ in range(5):  # 3 * 0.1s = 0.3s
                    screenshot = await self.browser.get_screenshot()
                    screenshots.append(screenshot)
                    await asyncio.sleep(0.05) 

                # Pause game
                await self.browser.press_key("Alt+Pause", delay_ms=0)

                duration = time.time() - start_time

                for i, screenshot in enumerate(screenshots):
                    self.lite_counter += 1
                    screenshot_dir = self.log_dir / "lite_screenshots"
                    monitor_dir = screenshot_dir / "monitor"
                    screenshot_dir.mkdir(exist_ok=True)
                    monitor_dir.mkdir(exist_ok=True)
                    screenshot_path = screenshot_dir / f"screenshot_{self.lite_counter}.jpg"
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot)
                duration = time.time() - start_time

                self.file_logger.info(f"Paused for {duration:.2f}s and took {len(screenshots)} screenshots")

            return result if result else f"Unknown action: {action}", screenshots

        except Exception as e:
            error_msg = f"Error executing action: {str(e)}"
            self.file_logger.error(error_msg)
            logger.error(error_msg)
            
            if self.lite:
                await self.browser.press_key("Alt+Pause", delay_ms=0)
            
            return error_msg, None

    async def capture_screenshots(self):

        screenshot_dir = self.log_dir / "game_screen_cont"
        monitor_dir = self.log_dir / "monitor_cont"
        screenshot_dir.mkdir(exist_ok=True)
        monitor_dir.mkdir(exist_ok=True)
        count = 0
        await asyncio.sleep(10)
        while True:
            try:
                screenshot = await self.browser.get_screenshot()
                # Save screenshot
                screenshot_path = screenshot_dir / f"game_screen_step_{count}.jpg"
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot)
                self.file_logger.info(f"Saved step {count} screenshot to {screenshot_path}")
                count += 1
                await asyncio.sleep(0.1)  # Wait 0.1 seconds before next capture
            except Exception as e:
                self.file_logger.error(f"Error capturing screenshot: {e}")
                await asyncio.sleep(0.1)  # Still wait on error before retrying

    async def start(self, initial_url: str) -> None:
        """
        Start the agent by initializing the browser.
        """
        self.file_logger.info("Starting browser")
        await self.browser.start()
        

        self.file_logger.info(f"Navigating to URL: {initial_url}")
        
        # Navigate to the initial URL
        start_time = time.time()
        await self.browser.navigate(initial_url)
        load_time = time.time() - start_time
        self.file_logger.info(f"Page loaded in {load_time:.2f}s")

        # Pre-loaded actions based on game
        await self.browser.pre_load(self.game)

        # Start the screenshot capture loop
        # asyncio.create_task(self.capture_screenshots())
