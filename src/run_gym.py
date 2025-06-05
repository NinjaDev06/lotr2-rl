import gymnasium as gym

from src.folder_web_server import FolderWebServer
from src.gyms.lotr2_gym import LordsOfTheRealm2Gym

def run_gym_emulator(args):
    folderServer = FolderWebServer('./roms', port=8080)
    folderServer.start()

    # Parallel environments
    env = gym.make("lotr2box/LordsOfTheRealm2-v0")
    
    env.reset()
    done = False

    while not done:
        action = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(action)
        print(f"Action: {action}, Reward: {reward}, Info: {info}")

        done = terminated or truncated

    env.close()
    folderServer.stop()