import asyncio
import threading

_event_loop = None
_event_lock = threading.Lock()

def run_async(coro):
    """await a coroutine from a synchronous function/method."""

    global _event_loop

    if not _event_loop:
        with _event_lock:
            if not _event_loop:
                _event_loop = asyncio.new_event_loop()
                threading.Thread(target=_event_loop.run_forever,
                                 name="Async Runner",
                                 daemon=True
                                 ).start()
    
    return asyncio.run_coroutine_threadsafe(coro, _event_loop).result()


