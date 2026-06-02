import logging
import queue
from logging.handlers import QueueHandler, QueueListener
_log_queue = queue.Queue(-1)
queue_handler = QueueHandler(_log_queue)

def start_queue_listener():
    """
    Call this once at startup (e.g., in wsgi.py/asgi.py) after Django setup.
    """
    root = logging.getLogger()
    handlers = [h for h in root.handlers if not isinstance(h, QueueHandler)]
    listener = QueueListener(_log_queue, *handlers, respect_handler_level=True)
    listener.start()
    return listener