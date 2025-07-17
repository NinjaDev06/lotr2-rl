## Taken from https://github.com/alexzhang13/videogamebench

import http.server
import socketserver
import logging
import threading
import asyncio
from pathlib import Path
import platform

from playwright.async_api import async_playwright

from lotr2_rl.async_utils import run_async

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DOSGameServer:
    """
    Simple HTTP server for hosting js-dos games.
    """
    def __init__(self, port: int = 8000, lite: bool = False):
        """
        Initialize the DOS game server.
        
        Args:
            port: The port to run the server on
        """
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.lite_mode = lite

    def start(self, game_url: str, custom_html: str = None) -> str:
        """
        Start the server with the specified game.
        
        Args:
            game_url: URL to the js-dos game bundle
            
        Returns:
            The URL to access the game
        """
        if self.is_running:
            logger.warning("Server is already running")
            return f"http://localhost:{self.port}"
            
        # Create a custom request handler with the game URL
        handler = self._create_request_handler(game_url, custom_html, self.lite_mode)
        
        # Create and start the server
        print(f"Starting server on port {self.port}...")
        self.server = socketserver.TCPServer(("", self.port), handler)
        self.is_running = True
        
        # Run the server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        logger.info(f"Server started at http://localhost:{self.port}")
        return f"http://localhost:{self.port}"
        
    def stop(self) -> None:
        """
        Stop the server.
        """
        if not self.is_running:
            logger.warning("Server is not running")
            return
            
        # Close browser if open
        if self.browser:
            self._close_browser()
        
        # Stop server    
        self.server.shutdown()
        self.server.server_close()
        self.is_running = False
        logger.info("Server stopped")
    
    def _close_browser(self) -> None:
        """
        Close the browser if it's open.
        """
        if self.browser:
            run_async(self.browser.close())
            self.browser = None
        
        if self.playwright:
            run_async(self.playwright.stop())
            self.playwright = None
        
        logger.info("Browser closed successfully")
        
    def _create_request_handler(self, 
                                game_url: str, 
                                custom_html: str = None, 
                                lite_mode: bool = False):
        """
        Create a custom request handler with the game URL.
        
        Args:
            game_url: URL to the js-dos game bundle
            
        Returns:
            A request handler class
        """
        class DOSGameHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                # Serve the index.html page for the root path
                if self.path == "/" or self.path == "/index.html":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    
                    # Create the HTML content with the specified game URL
                    from lotr2_rl.consts import DOS_GAME_HTML_TEMPLATE, DOS_GAME_LITE_HTML_TEMPLATE

                    if custom_html:
                        html_content = custom_html
                    elif lite_mode:
                        html_content = DOS_GAME_LITE_HTML_TEMPLATE.format(game_url=game_url)
                    else:
                        html_content = DOS_GAME_HTML_TEMPLATE.format(game_url=game_url)
                    
                    self.wfile.write(html_content.encode())
                # Add handler for dosbox.conf
                elif self.path == "/dosbox.conf":
                    # Get the path to the dosbox.conf file
                    dosbox_conf_path = Path("src/dos/dosbox.conf")
                    
                    if dosbox_conf_path.exists():
                        self.send_response(200)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        
                        # Read and serve the dosbox.conf file
                        with open(dosbox_conf_path, 'rb') as f:
                            self.wfile.write(f.read())
                    else:
                        # If the file doesn't exist, return 404
                        self.send_response(404)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"dosbox.conf file not found")
                        logger.error(f"dosbox.conf file not found at {dosbox_conf_path.absolute()}")
                else:
                    # For other paths, use the default behavior
                    super().do_GET()
                    
            def log_message(self, format, *args):
                # Customize logging to use our logger
                logger.debug(format % args)
                
        return DOSGameHandler 
