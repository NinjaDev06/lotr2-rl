import base64
import os
import platform
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Literal
import re

import random
import asyncio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_client")

class FakeLLMClient:
    """
    Client for interacting with language models using litellm.
    """
    def __init__(
        self, 
        log_dir: Optional[Path] = None,
    ):
        """
        Initialize the LLM client.
        
        Args:
            log_dir: Optional custom log directory path
        """
        
        # Set up logging directory
        if log_dir is None:
            self.log_dir = Path("logs") / "dos" / datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.log_dir = log_dir
            
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up file logger
        self.file_logger = self._setup_file_logger()
        self.step_count = 0
        
        self.provider = "fake"
        self.has_moved = False
        
        self.file_logger.info(f"Initialized LLMClient: provider: {self.provider}")
        self.file_logger.info(f"Logging to: {self.log_dir}")
        logger.info(f"LLMClient logging to: {self.log_dir}")
        
        
        # screen_width = 640
        # screen_height = 400

        # viewport_dimensions = {"width": 640, "height": 400} if platform.system() == "Darwin" else {"width": 700, "height": 475}
        # screen_width = viewport_dimensions['width']
        # screen_height = viewport_dimensions['height']

        # global_padding = 2
        
        self.x_min = 85
        self.y_min = 20
        self.game_width = 600 - self.x_min
        self.game_height = 395 - self.y_min

    def _setup_file_logger(self) -> logging.Logger:
        """Set up a file logger for this session."""
        file_logger = logging.getLogger(f"llm_client_{id(self)}")
        file_logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.log_dir / "llm_session.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add handler to logger
        file_logger.addHandler(file_handler)
        
        return file_logger
        
    async def generate_response(
        self, 
        image_data: Optional[bytes | List[bytes]] = None
    ) -> str:
        """
        Generate a response from the language model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            image_data: Optional screenshot data to include in the prompt
            
        Returns:
            The generated response text
        """
        self.step_count += 1
        self.file_logger.info(f"Step {self.step_count} - Generating response")

        response = await self.generate_react_response(
            task='no task', 
            screenshot=image_data
        )

        return 'actions [{0}]'.format(json.dumps(response, indent=2))

    async def generate_react_response(
        self, 
        screenshot: Optional[bytes | List[bytes]] = None
    ) -> Dict[str, Any]:
        """
        Generate a ReACT (Reasoning, Action, Observation) response.
        
        Args:
            task: The task description
            history: The conversation history
            screenshot: Optional screenshot data
            
        Returns:
            A dictionary containing thought, action, and action_input
        """
        self.file_logger.info(f"Step {self.step_count} - Generating ReACT response")
        
        # await asyncio.sleep(1)
        response = {
            "thought": "I have no clue what I'm doing",
            "action": "",
            "action_input": "",
            "memory": "I'm a red fish"
        }

        # Base simulation
        # response['action'] = random.choice(['click', 'move', 'drag'])
        # if response['action'] == 'click':
        #     response['action_input'] = random.choice(['', 'right', 'shift', 'ctrl', 'alt'])
        # elif response['action'] == 'move' or response['action'] == 'drag':
        #     response['action_input'] = f"{random.randint(0, 640)},{random.randint(0, 400)}"

        # Only auto click
        if self.has_moved:
            response['action'] = 'click'
            self.has_moved = False
        else:
            x = random.randint(0, self.game_width)
            y = random.randint(0, self.game_height)

            # x = self.game_width - 5
            # y = 114 ## self.game_height - 14

            if self._is_in_excluded_area(x, y):
                response['action'] = 'nope'
                response['action_input'] = '0,0'
            else:
                self.has_moved = True
                response['action'] = 'move'
                response['action_input'] = str(self.x_min + x) + "," + str(self.y_min + y)

        return response
    
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
