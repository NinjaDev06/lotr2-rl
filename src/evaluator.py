## Taken from https://github.com/alexzhang13/videogamebench

"""Evaluator for running LLM game interactions on VideoGameBench."""
import asyncio
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod
from src.llm.realtime_agent import WebBrowsingAgent
from src.emulators.dos.website_server import DOSGameServer

class BaseVGBenchEvaluator(ABC):
    """Abstract base class for evaluators that coordinate between game emulators and LLMs."""
    
    def __init__(
        self, 
        max_steps: int = 1000,
        step_delay: float = 0.1,
        metrics: Optional[List[Callable]] = None,
        checkpoints: Optional[List[str]] = None
    ):
        self.max_steps = max_steps
        self.step_delay = step_delay
        self.metrics = metrics or []
        self.checkpoints = checkpoints

    @abstractmethod
    async def run_episode(self, agent) -> Dict[str, Any]:
        """Run an episode of the game."""
        pass


class DOSEvaluator(BaseVGBenchEvaluator):
    """Evaluator class that coordinates between DOS emulators and LLMs."""
    
    def __init__(self, 
            max_steps: int = 1000, 
            step_delay: float = 0.1,
            metrics: Optional[List[Callable]] = None,
            checkpoints: Optional[List[str]] = None):
        super().__init__(max_steps, step_delay, metrics, checkpoints)
        
    async def run_episode(self, dos_agent: WebBrowsingAgent, url: str, server: DOSGameServer) -> Dict[str, Any]:
        """
        Run an episode of a game using JS-DOS with LLM interacting
        in realtime or paused based on if lite mode is on (controlled in agent).

        """
        try:
            # Start the agent
            await dos_agent.start(initial_url=url)

            # await dos_agent.reset(initial_url=url)
            # Execute the task
            await dos_agent.run_episode(checkpoints=self.checkpoints)
            await asyncio.sleep(5)  # Allow time for the agent to initialize
        finally:
            # Stop the agent
            await dos_agent.stop()
            
            # Stop the server if it was started
            if server:
                server.stop()