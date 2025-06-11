import gymnasium as gym

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

from lotr2_rl.folder_web_server import FolderWebServer
from lotr2_rl.gyms.lotr2_gym import LordsOfTheRealm2Gym

def _train_lotr2_gym(args):
    env = make_vec_env("lotr2-rl/LordsOfTheRealm2-v0", n_envs=1, env_kwargs={"render_mode": args.render_mode})
    
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=5000)
    
    obs = env.reset()
    done = False
    
    while not done:
        action, _states = model.predict(obs)
        obs, rewards, done, info = env.step(action)
        print(f"Action: {action}, Reward: {rewards}, Info: {info}")
    
    model.save("lotr2_ppo_model")

    env.close()

def _test_lotr2_gym(args):
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

def run_gym_emulator(args):
    folderServer = FolderWebServer('./roms', port=8080)
    folderServer.start()

    if args.action_mode == "train":
        _train_lotr2_gym(args)
    else:
        _test_lotr2_gym(args)

    folderServer.stop()