## Taken from https://github.com/alexzhang13/videogamebench

import asyncio
import sys

async def run_dos_emulator(args):
    """Run the DOS emulator with the given arguments."""
    # Import required modules
    # WebBrowsingAgent, GAME_URL_MAP, DOSGameServer, DOSEvaluator = import_dos_modules()
    
    try:
        from src.llm.realtime_agent import WebBrowsingAgent
        from src.consts import GAME_URL_MAP
        from src.emulators.dos.website_server import DOSGameServer
        from src.evaluator import DOSEvaluator
    except ImportError as e:
        print(f"Error importing DOS modules: {e}")
        print("Make sure you have installed the required dependencies for DOS emulation.")
        sys.exit(1)
    
    # Set up variables
    url = args.url
    headless = args.headless
    dos_name = args.game
    website_only = args.website_only
    
    # Start a local server for DOS games if specified
    server = None
    if dos_name:
        server = DOSGameServer(args.port, lite=args.lite)
        
        # Use custom HTML if provided, otherwise fall back to GAME_URL_MAP
        if hasattr(args, 'custom_html') and args.custom_html:
            url = server.start(dos_name, args.custom_html)
        elif dos_name in GAME_URL_MAP:
            dos_game = GAME_URL_MAP[dos_name]
            url = server.start(dos_game)
        else:
            print(f"Error: No configuration found for game {dos_name}")
            return

    # Website-only mode - open the browser and keep server running
    if website_only:
        if url:
            print(f"Opening {url} in Chromium browser...")
            
            # Use Playwright to open in Chromium instead of system default browser
            await server.open_in_chromium(headless=headless)
            
            # Keep the server running until interrupted
            print("Press Ctrl+C to stop the server and exit.")
            try:
                # Wait indefinitely until interrupted
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                print("\nShutting down server...")
            finally:
                if server:
                    server.stop()
            return
        else:
            print("Error: No URL specified for website-only mode.")
            if server:
                server.stop()
            return
    
    # Create the agent for interactive mode
    agent = WebBrowsingAgent(
        game=dos_name,
        headless=headless,
        lite=args.lite,
        press_key_delay=args.press_key_delay,
    )

    evaluator = DOSEvaluator(
        max_steps=args.max_steps, 
        step_delay=args.step_delay, 
        checkpoints=args.checkpoints,
    )

    await evaluator.run_episode(agent, url, server)
    