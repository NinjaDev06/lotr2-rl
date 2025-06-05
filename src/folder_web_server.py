import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class FolderWebServer:
    def __init__(self, folder: str, port: int = 8080):
        self.folder = Path(folder)
        self.port = port

        handler = partial(SimpleHTTPRequestHandler, directory=self.folder)
        self.httpd = HTTPServer(('localhost', self.port), handler)

        self._start = threading.Event()
        # call StartIt() here if you want to have started by default
        threading.Thread(name=repr(self), target=self._serve_forever, daemon=True).start()

    def start(self):
        """ Allow the server to serve. """
        self._start.set()

    def _serve_forever(self):
        print(f"Serving HTTP on port {self.port} from {self.folder}...")
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.httpd.server_close()
            print("Server stopped.")

    def stop(self):
        """ Block re-starting and shut down the current server. """
        self._start.clear()
        self.httpd.shutdown()

    def __repr__(self):
        """ A formal string representation of this instance. """
        return f'{self.__class__.__name__}(port={self.port})'