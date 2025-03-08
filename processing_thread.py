import asyncio
from queue import Queue
from threading import Thread

from config import logger
from frame_processing import process_frame


class ProcessingThread(Thread):
    def __init__(self, result_queue, client):
        super().__init__()
        self.result_queue = result_queue
        self.client = client
        self.frame_queue = Queue()
        self.running = True
        self.daemon = True
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        while self.running:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                try:
                    success = self.loop.run_until_complete(
                        process_frame(frame, self.client, self.result_queue)
                    )
                    if not success:
                        logger.error("Frame processing returned False")
                except Exception as e:
                    logger.error(f"Error in processing thread: {str(e)}")
                    self.result_queue.put(("error", f"Processing error: {str(e)}"))

    def process(self, frame):
        self.frame_queue.put(frame.copy())

    def stop(self):
        logger.info("Stopping processing thread")
        self.running = False
        self.loop.close()
