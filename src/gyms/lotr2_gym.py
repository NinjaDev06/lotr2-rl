import os
import math
import time
import re
import pytesseract
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# from PIL import Image

import numpy as np
import cv2
import gymnasium as gym

from src.emulators.dos.website_server import DOSGameServer
from src.emulators.dos.browser_controller import BrowserController
from src.llm.realtime_agent import WebBrowsingAgent

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LordsOfTheRealm2Gym(gym.Env):

    def __init__(
        self, 
        grid_size: int = 10, 
        enable_drag: bool = False, 
        sleep_second: float = 0.1,
        nb_step_reset: int = 1000,
        render_mode: str = None,
    ):

        # Observations are Box of RBG screen of 480 height and 640 width
        # height = 480
        # width = 640

        self.log_dir = Path("logs") / "lotr2" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.x_min = 85
        self.y_min = 20
        self.game_width = 600 - self.x_min
        self.game_height = 395 - self.y_min
        self.observation_space = gym.spaces.Box(0, 255, shape=(self.game_height, self.game_width, 3), dtype=np.uint8)

        self.grid_size = grid_size
        self.grid_width = math.ceil(self.game_width / grid_size)
        self.grid_height = math.ceil(self.game_height / grid_size)
        self.mouse_action_space = self.grid_width * self.grid_height
        self.enable_drag = enable_drag
        self.nb_step_reset = nb_step_reset

        # Set action space to implemented actions only
        if self.enable_drag:
            self.action_space = gym.spaces.Discrete(self.mouse_action_space + 3) # Action space with press & release
        else:
            self.action_space = gym.spaces.Discrete(self.mouse_action_space + 2) # Action space with click only

        self.last_gold = 0
        self.current_x = 0
        self.current_y = 0
        self.current_x_pixel = 0
        self.current_y_pixel = 0
        self.nb_step = 0

        self.game = "lotr2"
        self.server = DOSGameServer(9000, lite=False)
        self.url = self.server.start("http://localhost:8080/lotr2.jsdos")

        self.browser = BrowserController(
            headless=(render_mode != "human")
        )
        self.browser.start()

        icon_path = "C:\\Users\\egoul\\Documents\\Projects\\lotr2-rl\\src\\gyms\\player_icon.png"
        logger.info('icon found: ', os.path.exists(icon_path))
        self.player_icon_img = cv2.imread(icon_path)

    def _get_obs(self):
        image_bytes = self.browser.get_screenshot()
        # img = Image.frombytes('RGB', (640, 400), image_bytes)
        # img = Image.frombytes('RGB', (self.browser.viewport_dimensions['width'], self.browser.viewport_dimensions['height']), image_bytes)
        # img = img.crop((self.x_min, self.y_min, self.x_min + self.game_width, self.y_min + self.game_height))

        # Convert bytes to NumPy array
        nparr = np.frombuffer(image_bytes, np.uint8)

        # Decode image from array
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        cropped_img = img[:-75, 76:-90] 

        cv2.imwrite(self.log_dir / "obs_1.png", cropped_img)  # Save for debugging
        return cropped_img
    
    def _get_info(self, observation: np.ndarray):
        crowns = self._get_crown(observation)
        return {
            # todo: read resource values in Dosbox memory
            "gold": crowns if crowns is not None else self.last_gold,
        }
    
    def _get_crown(self, image: np.ndarray) -> int:
        """
        Extract the number of crowns from the image.
        
        Args:
            image: The image containing the crowns.
            
        Returns:
            The number of crowns as an integer.
        """
        # Define the region of interest (ROI) for the crowns
        x = 415
        width = 105
        crowns_image = image[0:19, x:x+width] 

        # Extract text
        text = pytesseract.image_to_string(crowns_image, lang="deu_latf")
        logger.info("Text found:", text)

        crowns = None
        # Check if the text contains "rown" because the "C" is readed as "D"
        if "rown" in text:
            text = text.replace("S", "5")
            crowns = int(re.sub(r'\D', '', text))  # Remove non-digit characters
        else:
            logger.warning("No crowns found in the text.")
        return crowns

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)
        
        # Navigate to the initial URL
        self.browser.navigate(self.url)
        self.browser.pre_load(self.game)

        observation = self._get_obs()
        info = self._get_info(observation)
        self.last_gold = info["gold"]
        self.nb_step = 0

        return observation, info
    
    def step(self, action):
        # todo: apply the action into Dosbox emulator
        self._play(action)
        self.nb_step += 1

        observation = self._get_obs()
        is_end_turn = self._is_end_turn_animation(observation)
        while is_end_turn:
            time.sleep(1)
            observation = self._get_obs()
            is_end_turn = self._is_end_turn_animation(observation)
        info = self._get_info(observation)

        terminated = False # todo: get if game is winned or losted
        truncated = True if self.nb_step >= self.nb_step_reset else False # todo: do we want to setup a time limit for episode training?
        reward = max(info["gold"] - self.last_gold, 0) # todo: build a reward function

        if reward > 0:
            logger.info(f"Gained Reward: {reward} (gold: {info['gold']} - last_gold: {self.last_gold})")

        self.last_gold = info["gold"]
        return observation, reward, terminated, truncated, info

    def _is_end_turn_animation(self, observation) -> bool:
        result = cv2.matchTemplate(observation, self.player_icon_img, cv2.TM_CCOEFF_NORMED)

        # Set a threshold: 0.8+ is usually a strong match
        threshold = 0.8
        locations = np.where(result >= threshold)

        # Check if any match was found
        if len(list(zip(*locations[::-1]))) > 0:
            return False
        else:
            return True

    def _play(self, action: int):
        # logger.info(f'Play action {action}')
        
        if action == 0:
            logger.info('Wait action')
            # Wait action
            return

        # if self._is_mouse_button_action(action):
        #     self._play_mouse_button_action(action)

        else:
            delta = 3 if self.enable_drag else 1
            mouse_action = action - delta
            if mouse_action < 0 or mouse_action > self.mouse_action_space * 2:
                raise ValueError(f'Action should be in range of action space [0, {self.mouse_action_space * 2}]')

            # logger.debug(f'Play mouse action {mouse_action}')
            x = (mouse_action % self.mouse_action_space) % self.grid_width + 1
            y = (mouse_action % self.mouse_action_space) // self.grid_width + 1
            # logger.debug(f'grid ({x}, {y})')

            self.current_x = x
            self.current_y = y

            x_pixel = self.grid_to_pixel(x)
            y_pixel = self.grid_to_pixel(y)
            # logger.debug(f'pixel ({x_pixel}, {y_pixel})')

            if self._is_in_excluded_area(x_pixel, y_pixel):
                logger.info(f"Prevent moving inside excluded area: {x_pixel}, {y_pixel}")
                return

            self.current_x_pixel = x_pixel
            self.current_y_pixel = y_pixel

            logger.info(f'mouse_move {mouse_action} : move at grid=({x}, {y}), pixel=({x_pixel}, {y_pixel})')
            self.browser.execute_action("move", f"{self.x_min + x_pixel},{self.y_min + y_pixel}")
            # time.sleep(self.sleep_second)

            # When they is no drag, directly perform a click after moving the mouse
            # This remove the learning of action chain of mouve + press + release to click on a game button
            if not self.enable_drag:
                self.browser.execute_action("click", "")

            
    # def _play_mouse_button(self, button: MouseButtonAction):
    #     if button == MouseButtonAction.Press:
    #         # print(f'mouse_press')
    #         self.client.mouse_press(MouseButton.Left)

    #         # Detect "End turn" to wait until all animation end to see all changes like gold
    #         if self.current_x_pixel >= 480 and self.current_y_pixel >= 460:
    #             print(f'waiting for end turn')
    #             # 8-10 sec for Pentium 60Mhz
    #             # 3.5 sec for Pentium 120Mhz
    #             time.sleep(max(self.sleep_second * 20, 3.5))
    #         else:
    #             time.sleep(self.sleep_second)

    #     elif button == MouseButtonAction.Release:
    #         # print(f'mouse_release')
    #         self.client.mouse_release(MouseButton.Left)
    #         time.sleep(self.sleep_second)

    # def _play_mouse_button_action(self, action: int):
    #     if action == 1:
    #         self._play_mouse_button(MouseButtonAction.Press)

    #     elif action == 2:
    #         self._play_mouse_button(MouseButtonAction.Release)

    #     else:
    #         raise ValueError(f"Not supported action {action} when enable_drag is {self.enable_drag}")

    # def _is_mouse_button_action(self, action: int):
    #     return self.enable_drag and action in [1, 2]
    
    def grid_to_pixel(self, x) -> float:
        return (x * self.grid_size) - (self.grid_size / 2)

    def coordinate_to_action(self, x, y) -> int:
        return (x-1) + self.grid_width * (y-1) + (3 if self.enable_drag else 1)

    def _is_in_excluded_area(self, x: int, y: int) -> bool:
        """
        Check if the coordinates are within the included area.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if within the area, False otherwise
        """
        
        # logger.info(f"area: ({x}, {y}) excluded: ({self.game_width - 126}, 134)")
        # logger.info(f"area: ({x}, {y}) excluded: ({(x >= self.game_width - 126)}, {(134 <= y)})")
        # Exclude minimap area
        if x >= self.game_width - 126 and y <= 114:
            logger.info(f"Move inside exluded area: {x}, {y}")
            return True
        
        # logger.info(f"area: ({x}, {y}) excluded: ({self.game_width - 136}, {self.game_height - 35}, {self.game_height - 10})")
        # logger.info(f"area: ({x}, {y}) excluded: ({(x >= self.game_width - 136)}, {(y >= self.game_height - 35)}, {y <= self.game_height - 10})")
        # Exclude bottom menu area, but not the "end turn" button
        if x >= self.game_width - 126 and y >= self.game_height - 30 and y <= self.game_height - 14:
            logger.info(f"Move inside exluded area: {x}, {y}")
            return True
        return False

gym.register(
    id="lotr2box/LordsOfTheRealm2-v0",
    entry_point=LordsOfTheRealm2Gym,
)
