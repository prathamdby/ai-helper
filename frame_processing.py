import os
import time
import cv2

from config import logger, gemini_client, OCR_MODEL
from model_responses import get_all_model_responses


async def process_frame(frame, result_queue):
    filename = f"capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
    logger.info("Starting frame processing")

    try:
        if not cv2.imwrite(filename, frame):
            logger.error("Failed to save captured image")
            result_queue.put(("error", "Failed to save image"))
            return False

        start_time = time.perf_counter()
        try:
            file = gemini_client.files.upload(file=filename)
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            result_queue.put(("error", f"Failed to upload file: {str(e)}"))
            return False

        detected = gemini_client.models.generate_content(
            model=OCR_MODEL,
            contents=[
                """Extract text from this image:
If it's a multiple choice question, format as:
Question: <question>
Options: <options>

If it's a regular question, format as:
Question: <question>

ONLY return a Question: line if you detect an actual question in the image.
If no question is detected, return empty string.""",
                file,
            ],
        ).text.strip()

        if not detected:
            logger.warning("No question detected in image")
            raise Exception("No question detected in image")

        if "Question:" not in detected:
            logger.warning("Text detected but no question structure found")
            raise Exception("No question found in the image")

        question = ""
        options = ""
        for line in detected.split("\n"):
            if line.startswith("Question:"):
                question = line.replace("Question:", "").strip()
            elif line.startswith("Options:"):
                options = line.replace("Options:", "").strip()

        if not question:
            logger.error("Failed to extract question from detected text")
            raise Exception("Failed to extract question")

        result_queue.put(("question", (question, options, detected)))

        await get_all_model_responses(question, options, result_queue)
        total_time = time.perf_counter() - start_time
        logger.info(f"Frame processed successfully in {total_time:.2f}s")
        return True

    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        result_queue.put(("error", str(e)))
        return False

    finally:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file: {str(e)}")
