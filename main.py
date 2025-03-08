import cv2
import time
from queue import Queue

from config import (
    logger,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_FPS,
    CAPTURE_COOLDOWN,
)
from drawing import draw_overlay
from processing_thread import ProcessingThread


def main():
    logger.info("Starting application")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

    if not cap.isOpened():
        logger.critical("Failed to open camera")
        return

    result_queue = Queue()
    processing_thread = ProcessingThread(result_queue)
    processing_thread.start()

    status = "Ready"
    is_processing = False
    current_question = ""
    current_ocr = ""
    current_responses = None
    last_capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        while not result_queue.empty():
            update_type, data = result_queue.get()

            if update_type == "question":
                question, options, ocr_text = data
                current_question = f"{question}\n{options}" if options else question
                current_ocr = ocr_text
                status = "Processing responses..."
            elif update_type == "partial" or update_type == "complete":
                current_responses = data
                if update_type == "complete":
                    status = "Ready"
                    is_processing = False
            elif update_type == "error":
                status = f"Error: {data}"
                current_question = data
                current_ocr = ""
                current_responses = None
                is_processing = False

        display_frame = frame.copy()
        draw_overlay(
            display_frame,
            status,
            current_question,
            current_ocr,
            current_responses,
        )
        cv2.imshow("Live Camera Feed", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            current_question = ""
            current_ocr = ""
            current_responses = None
            status = "Ready"
        elif key == ord(" ") and not is_processing:
            current_time = time.time()
            if current_time - last_capture_time >= CAPTURE_COOLDOWN:
                status = "Processing..."
                is_processing = True
                current_question = ""
                current_ocr = ""
                current_responses = None
                last_capture_time = current_time
                processing_thread.process(frame)

    logger.info("Shutting down application")
    processing_thread.stop()
    processing_thread.join()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
