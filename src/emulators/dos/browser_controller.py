## Taken from https://github.com/alexzhang13/videogamebench

import asyncio
import base64
import logging
import math
import random
import time
from typing import List, Optional, Tuple, Union
import platform

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrowserController:
    """
    Controller for browser interactions using Playwright.
    Implements human-like mouse movements and interactions.
    """
    def __init__(self, headless: bool = False):
        """
        Initialize the browser controller.
        
        Args:
            headless: Whether to run the browser in headless mode
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_mouse_position = (0, 0)
        self.paused = False
        self.pause_task = None  # Add this to track the pause task
        self.lite = False  # Whether to run in lite mode
    
    def pre_load(self, game: str) -> None:
        """
        Read and execute preload actions from a config file for the specified game.
        
        Args:
            game: Name of the game to preload
        """
        config_path = f"configs/{game}/preload.txt"
        try:
            with open(config_path, 'r') as f:
                actions = f.readlines()
            
            for action in actions:
                action = action.strip()
                if not action or action.startswith('#'):
                    continue
                    
                parts = action.split()
                command = parts[0].lower()
                
                if command == "sleep":
                    seconds = float(parts[1])
                    time.sleep(seconds)
                    print(f"Waited for {seconds} seconds")
                    
                elif command == "move_mouse":
                    x, y = float(parts[1]), float(parts[2])
                    self.move_mouse(x, y)
                    print(f"Moved mouse to ({x}, {y})")
                    
                elif command == "click":
                    x, y = float(parts[1]), float(parts[2])
                    self.click(x, y)
                    print(f"Clicked at ({x}, {y})")
                    
                elif command == "press_key":
                    key = parts[1]
                    self.press_key(key)
                    print(f"Pressed key: {key}")
                    
                else:
                    print(f"Unknown command: {command}")
                    
        except FileNotFoundError:
            print(f"Warning: No preload configuration found at {config_path}")
        except Exception as e:
            print(f"Error executing preload actions: {e}")

    def start(self) -> None:
        """
        Start the browser.
        """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless, args=["--disable-web-security"])

        self.viewport_dimensions = {"width": 640, "height": 400} if platform.system() == "Darwin" else {"width": 700, "height": 475}
        print('viewport_dimensions', self.viewport_dimensions)
        self.context = self.browser.new_context(
            viewport=self.viewport_dimensions,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        )
        self.page = self.context.new_page()
        
        # Set initial mouse position
        self.current_mouse_position = (0, 0)
        
        logger.info("Browser started successfully")
        
    def close(self) -> None:
        """
        Close the browser.
        """
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed successfully")
        
    def navigate(self, url: str) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        self.page.goto(url)
        logger.info(f"Navigated to {url}")
        
    def get_screenshot(self) -> bytes:
        """
        Get a screenshot of the current page.
        
        Returns:
            The screenshot as bytes
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        # Capture screenshot in JPEG format
        screenshot = self.page.screenshot(type="jpeg", quality=100)
        logger.info("Screenshot captured")
        return screenshot
        
    def move_mouse(self, x: float, y: float) -> None:
        """
        Move the mouse to the specified coordinates with human-like movement.
        
        Args:
            x: The x coordinate
            y: The y coordinate
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        # Get current mouse position
        start_x, start_y = self.current_mouse_position
        
        # Generate a human-like path for the mouse movement
        path = self._generate_human_like_path(start_x, start_y, x, y)
        
        # Move the mouse along the path
        for point_x, point_y in path:
            self.page.mouse.move(point_x, point_y)
            # Add a small delay to simulate human movement speed
            time.sleep(random.uniform(0.001, 0.005))
        
        # Update current mouse position
        self.current_mouse_position = (x, y)
        logger.info(f"Mouse moved to ({x}, {y})")

    def move_mouse_right(self) -> None:
        """Move the mouse 10 pixels to the right."""
        x, y = self.current_mouse_position
        self.move_mouse(x + 10, y)

    def move_mouse_left(self) -> None:
        """Move the mouse 10 pixels to the left."""
        x, y = self.current_mouse_position
        self.move_mouse(x - 10, y)

    def move_mouse_up(self) -> None:
        """Move the mouse 10 pixels up."""
        x, y = self.current_mouse_position
        self.move_mouse(x, y - 10)

    def move_mouse_down(self) -> None:
        """Move the mouse 10 pixels down."""
        x, y = self.current_mouse_position
        self.move_mouse(x, y + 10)
        
    def click(self, x: float, y: float, options: dict = None) -> None:
        """
        Click at the specified coordinates with human-like movement.
        
        Args:
            x: The x coordinate
            y: The y coordinate
            options: Dictionary of click options including:
                - button: 'left' (default) or 'right'
                - modifiers: list of modifiers ('Shift', 'Control', 'Alt')
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        # First move the mouse to the target position
        self.move_mouse(x, y)
        
        # Add a small delay before clicking (like a human would)
        asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Apply click options
        # if options:
        #     await self.page.mouse.click(x, y, **options)
        # else:
        #     await self.page.mouse.click(x, y)

        self.page.mouse.down()
        time.sleep(random.uniform(0.05, 0.1))
        self.page.mouse.up()
        
        logger.info(f"Clicked at ({x}, {y}) with options: {options}")
        
    def drag(self, x: float, y: float) -> None:
        """
        Drag from current position to the specified coordinates.
        
        Args:
            x: The x coordinate to drag to
            y: The y coordinate to drag to
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        # Get current mouse position
        start_x, start_y = self.current_mouse_position
        
        # Press mouse button down at current position
        self.page.mouse.down()
        
        # Generate a human-like path for the drag movement
        path = self._generate_human_like_path(start_x, start_y, x, y)
        
        # Move the mouse along the path
        for point_x, point_y in path:
            self.page.mouse.move(point_x, point_y)
            # Add a small delay to simulate human movement speed
            time.sleep(random.uniform(0.005, 0.01))
        
        # Release mouse button at target position
        self.page.mouse.up()
        
        # Update current mouse position
        self.current_mouse_position = (x, y)
        logger.info(f"Dragged from ({start_x}, {start_y}) to ({x}, {y})")
        
    def scroll_down(self, amount: int) -> None:
        """
        Scroll down by the specified amount.
        
        Args:
            amount: The amount to scroll down in pixels
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        self.page.mouse.wheel(0, amount)
        logger.info(f"Scrolled down {amount} pixels")
        
    def scroll_up(self, amount: int) -> None:
        """
        Scroll up by the specified amount.
        
        Args:
            amount: The amount to scroll up in pixels
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        self.page.mouse.wheel(0, -amount)
        logger.info(f"Scrolled up {amount} pixels")
        
    def type_text(self, text: str) -> None:
        """
        Type text with human-like timing.
        
        Args:
            text: The text to type
        """
        if not self.page:
            raise ValueError("Browser not started")
        
        # Type with human-like delays between keystrokes
        for char in text:
            self.page.keyboard.press(char)
            # Add a random delay between keystrokes
            time.sleep(random.uniform(0.05, 0.15))

        logger.info(f"Typed: {text}")
    
    def press_key(self, key: str, 
                        lite_mode: bool = False, 
                        delay_ms: float = 100) -> None:
        """
        Press a specific key or key combination.
        
        Args:
            key: The key to press (e.g., "KeyA", "ArrowLeft", "Shift+KeyA")
            lite_mode: Whether to use lite mode
            delay_ms: The delay in milliseconds when pressing key.
        """
        if not self.page:
            raise ValueError("Browser not started")

        # Handle key combinations like "Shift+KeyA"
        if "," in key:
            logger.info(f"Pressing key: {key}")
            keys = key.split("+")
            
            # Press down all modifier keys first
            for modifier in keys[:-1]:
                self.page.keyboard.down(modifier)
            
            # Press the final key
            self.page.keyboard.press(keys[-1], delay=delay_ms)
            
            # Release all modifier keys in reverse order
            for modifier in reversed(keys[:-1]):
                self.page.keyboard.up(modifier)
        
        # Handle single key press
        else:
            self.page.keyboard.press(key, delay=delay_ms)
        
        logger.info(f"Pressed key: {key}")

    def _generate_human_like_path(
        self, 
        start_x: float, 
        start_y: float, 
        end_x: float, 
        end_y: float, 
        control_points: int = 3
    ) -> List[Tuple[float, float]]:
        """
        Generate a human-like path for mouse movement using Bezier curves.
        
        Args:
            start_x: Starting x coordinate
            start_y: Starting y coordinate
            end_x: Ending x coordinate
            end_y: Ending y coordinate
            control_points: Number of control points for the Bezier curve
            
        Returns:
            A list of (x, y) coordinates representing the path
        """
        # Calculate distance between start and end points
        distance = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
        
        # Determine number of steps based on distance
        steps = max(10, int(distance / 10))
        
        # Generate control points for the Bezier curve
        control_xs = [start_x]
        control_ys = [start_y]
        
        # Add random control points
        for i in range(control_points):
            # Add some randomness to the control points
            # The control points should be closer to the straight line for longer distances
            max_offset = min(100, distance * 0.2)
            
            # Calculate a point along the straight line
            t = (i + 1) / (control_points + 1)
            line_x = start_x + t * (end_x - start_x)
            line_y = start_y + t * (end_y - start_y)
            
            # Add random offset
            control_x = line_x + random.uniform(-max_offset, max_offset)
            control_y = line_y + random.uniform(-max_offset, max_offset)
            
            control_xs.append(control_x)
            control_ys.append(control_y)
        
        # Add end point
        control_xs.append(end_x)
        control_ys.append(end_y)
        
        # Generate points along the Bezier curve
        path = []
        for i in range(steps + 1):
            t = i / steps
            
            if i < steps + 1:
                # Calculate point on the Bezier curve
                x = self._bezier_point(t, control_xs)
                y = self._bezier_point(t, control_ys)
            
            path.append((x, y))
        
        return path
    
    def _bezier_point(self, t: float, control_points: List[float]) -> float:
        """
        Calculate a point on a Bezier curve.
        
        Args:
            t: Parameter between 0 and 1
            control_points: List of control point coordinates
            
        Returns:
            The coordinate of the point on the Bezier curve
        """
        n = len(control_points) - 1
        point = 0
        
        for i in range(n + 1):
            # Calculate binomial coefficient
            binomial = math.comb(n, i)
            
            # Calculate Bernstein polynomial
            bernstein = binomial * (t ** i) * ((1 - t) ** (n - i))
            
            # Add contribution of this control point
            point += control_points[i] * bernstein
        
        return point

    def execute_action(self, action: str, action_input: str) -> str:
        """Execute an action and return the observation."""
        try:
            logger.info(f"Executing action: {action} with input: {action_input}")
            
            # Execute the action
            result = None
            screenshots = []
            if self.lite:
                logger.info("Lite mode is enabled, pausing game with Alt+Pause key...")
                self.press_key("Alt+Pause", delay_ms=0)
                time.sleep(0.01)

            if action == "nope":
                logger.info("Agent decided to skip this step.")

            elif action == "click":
                x, y = self.current_mouse_position
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
                
                logger.info(f"Clicking at coordinates: ({x}, {y}) with options: {click_options}")
                self.click(x, y, click_options)
                result = f"Mouse clicked at ({x}, {y}) with options: {click_options}"

            elif action == "move":
                x, y = map(float, action_input.split(","))
                x_start, y_start = self.current_mouse_position
                logger.info(f"Moving mouse from: ({x_start}, {y_start}) to: ({x}, {y})")
                self.move_mouse(x, y)
                result = f"Mouse moved to ({x}, {y})"

            elif action == "drag":
                x, y = map(float, action_input.split(","))
                x_start, y_start = self.current_mouse_position
                logger.info(f"Dragging from: ({x_start}, {y_start}) to: ({x}, {y})")
                self.drag(x, y)
                result = f"Mouse dragged to ({x}, {y})"

            elif action == "scroll_down":
                amount = int(action_input)
                logger.info(f"Scrolling down: {amount}px")
                self.scroll_down(amount)
                result = f"Scrolled down {amount} pixels."

            elif action == "scroll_up":
                amount = int(action_input)
                logger.info(f"Scrolling up: {amount}px")
                self.scroll_up(amount)
                result = f"Scrolled up {amount} pixels."

            elif action == "write":
                logger.info(f"Typing text: {action_input}")
                self.type_text(action_input)
                result = f"Typed: {action_input}"

            elif action == "press_key":
                logger.info(f"Pressing key: {action_input}")
                if "," in action_input:
                    keys = action_input.split(",")
                    for key in keys:
                        self.press_key(key.strip(), lite_mode=self.lite, delay_ms=self.press_key_delay)
                        for _ in range(self.num_screenshots_per_action): 
                            screenshot = self.get_screenshot()
                            screenshots.append(screenshot)
                            time.sleep(0.05) 
                    result = f"Pressed keys: {action_input}"
                else:
                    self.press_key(action_input, lite_mode=self.lite, delay_ms=self.press_key_delay)
                    result = f"Pressed key: {action_input}"

            elif action == "hold_key":
                parts = action_input.split(",")
                key = parts[0]
                duration = float(parts[1]) if len(parts) > 1 else 0.5
                logger.info(f"Holding key: {key} for {duration}s")
                self.press_key(key, lite_mode=self.lite, delay_ms=duration)
                result = f"Held key {key} for {duration} seconds"

            elif action == "done":
                logger.info("Agent marked task as complete")
                result = "Task completed."

            elif action == "error":
                logger.error(f"Agent reported error: {action_input}")
                result = f"Error occurred: {action_input}"

            else:
                logger.warning(f"Unknown action: {action}")
                result = f"Unknown action: {action}"

            if self.lite:
                start_time = time.time()
                # Take screenshots for approximately 0.3 seconds
                for _ in range(5):  # 3 * 0.1s = 0.3s
                    screenshot = self.get_screenshot()
                    screenshots.append(screenshot)
                    time.sleep(0.05) 

                # Pause game
                self.press_key("Alt+Pause", delay_ms=0)

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

                logger.info(f"Paused for {duration:.2f}s and took {len(screenshots)} screenshots")

            return result if result else f"Unknown action: {action}", screenshots

        except Exception as e:
            error_msg = f"Error executing action: {str(e)}"
            logger.error(error_msg)
            logger.error(error_msg)
            
            if self.lite:
                self.press_key("Alt+Pause", delay_ms=0)
            
            return error_msg, None
