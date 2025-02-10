import asyncio


class SharedState:
    def __init__(self):
        self.request_state = {}
        self.request_queue = asyncio.Queue()
        self.state_lock = asyncio.Lock()
