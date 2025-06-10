import gymnasium as gym

from src.folder_web_server import FolderWebServer
from src.gyms.lotr2_gym import LordsOfTheRealm2Gym

def run_gym_emulator(args):
    folderServer = FolderWebServer('./roms', port=8080)
    folderServer.start()

    # Parallel environments
    env = gym.make("lotr2-rl/LordsOfTheRealm2-v0", render_mode=args.render_mode,)
    
    env.reset()
    done = False

    action_func = None
    if args.action_mode == "random":
        def random_action_func():
            return env.action_space.sample()
        action_func = random_action_func
    elif args.action_mode == "manual":
        def manual_actions():
            action = input(f"Enter action (0-{env.action_space.n}): ")
            return int(action) if action.isdigit() else 0
        action_func = manual_actions

    while not done:
        action = action_func()
        observation, reward, terminated, truncated, info = env.step(action)
        print(f"Action: {action}, Reward: {reward}, Info: {info}")

        done = terminated or truncated

    env.close()
    folderServer.stop()