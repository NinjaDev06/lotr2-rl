"""
VG-Bench interface

This package provides a generic agent that uses the ReACT method to complete tasks on video games
"""

__version__ = "0.1.0"

from gymnasium.envs.registration import register

from lotr2_rl.gyms.lotr2_gym import LordsOfTheRealm2Gym

register(
    id="lotr2-rl/LordsOfTheRealm2-v0",
    entry_point=LordsOfTheRealm2Gym,
)