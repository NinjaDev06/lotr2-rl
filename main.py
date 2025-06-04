#!/usr/bin/env python3
import argparse
import yaml
import asyncio
import os
import sys
import webbrowser
import signal
import time
from typing import Optional, Dict, Any
from PIL import Image
from pathlib import Path
from src.utils import hash_image

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Environment variables must be set manually.")

# Global variables for clean shutdown
game_instance = None

def parse_args():
    parser = argparse.ArgumentParser(description="Game Emulation and Evaluation with LLMs")
    
    # Emulator selection (not necessary if config is specified)
    parser.add_argument("--emulator", choices=["dos", "gym"],
                       help="Which emulator to use ('dos' or 'gym'). Overwritten if config is specified.")

    # Common arguments
    parser.add_argument("--headless", action="store_true", 
                       help="Run the emulator without visual display")
    parser.add_argument("--config-folder", type=str, default="configs/",
                       help="Path to the config folder")
    parser.add_argument("--game", type=str, 
                       help="Name or URL of a js-dos game bundle to run or GBA game to load")
    parser.add_argument("--record", action="store_true",
                       help="Record both game and agent monitor screens. TODO: Doesn't do anything right now.")
    parser.add_argument("--record-path", type=str, default=None,
                       help="Path to save the recording (default: recordings/gameplay_TIMESTAMP.mp4)")
    parser.add_argument("--lite", action="store_true", 
                       help="Lite-mode, so not real time. Game pauses between actions.")

    # DOS-specific arguments
    parser.add_argument("--port", type=int, default=8000, 
                       help="Port to run the server")
    parser.add_argument("--url", type=str, default="", 
                       help="The URL to start from")
    parser.add_argument("--website-only", action="store_true", 
                       help="Just open the website without agent interaction ")
    parser.add_argument("--action-delay", default=100, type=int, 
                       help="Delay between actions in milliseconds")
    
    # Evaluation arguments
    parser.add_argument("--max-steps", type=int, default=500, 
                       help="Maximum number of steps to run")
    parser.add_argument("--step-delay", type=float, default=0.1, 
                       help="Delay between steps in seconds (GBA only)")

    return parser.parse_args()

def load_game_config(args):
    """Load game configuration and prompt from the appropriate config folder."""
    # DOS-specific game defaults
    args.press_key_delay = args.action_delay

    if not args.game or not args.config_folder:
        print(f"No game or config folder specified. Exiting.")
        return args

    # Determine config path based on emulator type
    config_base = Path(args.config_folder)
    config_dir = config_base / args.game
    config_file = config_dir / "config.yaml"
    # Try loading checkpoints if they exist
    checkpoint_dir = config_dir / "checkpoints"
    if checkpoint_dir.exists():
        try:
            # Get all image files and sort numerically
            checkpoint_files = sorted(
                [f for f in checkpoint_dir.glob("*.png")],
                key=lambda x: int(x)
            )
            if checkpoint_files:
                checkpoint_hashes = []
                for checkpoint in checkpoint_files:
                    img = Image.open(checkpoint)
                    hash_str = str(hash_image(img))
                    checkpoint_hashes.append(hash_str)
                args.checkpoints = checkpoint_hashes
            else:
                args.checkpoints = None
        except:
            args.checkpoints = None
    else:
        args.checkpoints = None
    
    print(f"Loading config from {config_file}")
    try:
        # Load YAML config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        # Update args with config values, preserving command-line overrides
        for key, value in config.items():
            # Only update if not explicitly set in command line
            if not getattr(args, key, None):
                setattr(args, key, value)
                
        html_file = config_dir / "game.html"
        if html_file.exists():
            with open(html_file, 'r') as f:
                args.custom_html = f.read()
        else:
            args.custom_html = None
                
    except FileNotFoundError:
        print(f"No config file found at {config_file}")
        print(f"Using default configuration for {args.game}")
    except Exception as e:
        print(f"Error loading config: {e}")
        
    return args

def handle_shutdown_signal(sig, frame):
    """Handle shutdown signals for clean exit."""
    print("\nShutdown signal received. Cleaning up...")
        
    # Close any active screen recorder
    if hasattr(game_instance, 'monitor') and game_instance.monitor:
        if game_instance.monitor.screen_recorder:
            game_instance.monitor.screen_recorder.close()
    
    sys.exit(0)

def main():
    """Main async entry point."""
    args = parse_args()
    args = load_game_config(args)

    args.game = args.game or "lotr2"

    if args.emulator == "dos":
        from src.run_dos import run_dos_emulator
        asyncio.run(run_dos_emulator(args))
    elif args.emulator == "gym":
        from src.run_gym import run_gym_emulator
        run_gym_emulator(args)
    else:
        print("No emulator specified. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    # Run the main function
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Cleaning up...")
