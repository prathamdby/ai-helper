import asyncio
import logging
import os
import time
from queue import Queue
from threading import Thread
from typing import Dict, Tuple

import cv2
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

logger = logging.getLogger("ai-helper")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)

MODELS = [
    "deepseek/deepseek-chat:free",
    "qwen/qwq-32b:free",
    "google/gemini-2.0-pro-exp-02-05:free",
]


async def get_model_response(
    question: str, options: str, model: str
) -> Tuple[bool, str, float]:
    MAX_RETRIES = 2
    start_time = time.perf_counter()
    logger.info(f"Getting response from model: {model}")

    def validate_answer(ans: str, is_mcq: bool) -> bool:
        if not ans:
            return False
        if is_mcq:
            return len(ans.strip()) == 1 and ans.strip().upper() in ["A", "B", "C", "D"]
        return len(ans.split()) > 0

    try:
        for attempt in range(MAX_RETRIES + 1):
            if options:
                prompt = f"""Multiple Choice Question:
{question}
{options}

Instructions:
1. ONLY respond with the letter (A, B, C, or D) of the correct option
2. Do not write the full answer or any explanation
3. Just the letter, nothing else

You must respond with just A, B, C, or D."""
            else:
                prompt = f"""Answer this question concisely:
{question}

Instructions:
1. If it's a factual question (like capitals, dates, names), give the exact correct answer
2. The answer must be brief and to the point - avoid explanations or unnecessary words
3. Proper nouns should be capitalized (e.g., Delhi, Paris, Einstein)
4. Keep your response very short and focused

Your response must be clear and concise."""

            try:
                logger.debug(
                    f"Attempt {attempt + 1}/{MAX_RETRIES + 1} for model {model}"
                )
                completion = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a precise answering system that follows instructions exactly.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                    ),
                )
                answer = completion.choices[0].message.content.strip()

                if validate_answer(answer, bool(options)):
                    elapsed_time = time.perf_counter() - start_time
                    logger.info(f"Valid response from {model} in {elapsed_time:.2f}s")
                    return True, answer.upper() if options else answer, elapsed_time

                if attempt < MAX_RETRIES:
                    continue

                return True, "Invalid response" if options else "Unknown", elapsed_time

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {model}: {str(e)}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1)
                    continue
                raise e
    except Exception as e:
        elapsed_time = time.perf_counter() - start_time
        logger.error(f"All attempts failed for {model}: {str(e)}")
        return False, f"Error ({model.split('/')[-1]}): {str(e)}", elapsed_time


async def get_all_model_responses(
    question: str, options: str, result_queue: Queue
) -> None:
    # Initialize responses with "-" for all models
    responses = {model: ("-", 0.0) for model in MODELS}
    result_queue.put(("partial", responses.copy()))

    async def process_model(model):
        result = await get_model_response(question, options, model)
        if isinstance(result, tuple) and result[0]:
            responses[model] = (result[1], result[2])
        elif isinstance(result, Exception):
            responses[model] = (f"Error: {str(result)}", 0.0)
        else:
            responses[model] = (f"Error: Failed to get response", 0.0)
        # Send incremental update
        result_queue.put(("partial", responses.copy()))

    # Create tasks for each model
    tasks = [process_model(model) for model in MODELS]
    await asyncio.gather(*tasks)
    # Send final update
    result_queue.put(("complete", responses))


def draw_text(frame, text, position, color=(255, 255, 255), scale=0.7):
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    padding = 10

    for i, line in enumerate(text.split("\n")):
        y = position[1] + i * int(30 * scale)
        (text_width, text_height) = cv2.getTextSize(line, font, scale, thickness)[0]

        cv2.rectangle(
            frame,
            (position[0] - padding, y - text_height - padding),
            (position[0] + text_width + padding, y + padding),
            (0, 0, 0),
            -1,
        )

        cv2.putText(frame, line, (position[0], y), font, scale, color, thickness)


def draw_overlay(frame, status="Ready", question="", ocr_text="", model_responses=None):
    height, width = frame.shape[:2]
    keybinds = [
        "Controls:",
        "SPACE - Capture & Analyze",
        "C - Clear Results",
        "Q - Quit",
    ]

    for i, bind in enumerate(keybinds):
        draw_text(frame, bind, (20, 30 + i * 35), color=(0, 255, 0), scale=0.5)

    status_text = f"Status: {status}"
    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    status_x = width - text_size[0] - 40
    draw_text(frame, status_text, (status_x, 30), color=(255, 255, 0))

    if question:
        ocr_y = height - 200
        draw_text(
            frame, f"OCR: {ocr_text}", (20, ocr_y), scale=0.4, color=(128, 128, 128)
        )

        q_y = height - 150
        q_x = 20
        draw_text(frame, f"Q: {question}", (q_x, q_y), color=(255, 255, 255))

        if model_responses:
            for i, (model, (answer, time_taken)) in enumerate(model_responses.items()):
                model_name = model.split("/")[0]
                a_y = height - 100 + (i * 30)
                # Use different colors and styles for different states (BGR format)
                if answer == "-":
                    color = (71, 177, 255)  # Orange for processing (BGR)
                    time_text = " (Processing...)"
                elif answer.startswith("Error"):
                    color = (0, 0, 255)  # Red for errors (BGR)
                    time_text = ""
                else:
                    color = (255, 255, 102)  # Light cyan for successful responses (BGR)
                    time_text = f" ({time_taken:.2f}s)"

                draw_text(
                    frame,
                    f"{model_name}: {answer}{time_text}",
                    (q_x, a_y),
                    color=color,
                    scale=0.6,
                )


async def process_frame(frame, client, result_queue):
    filename = f"capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
    logger.info("Starting frame processing")

    try:
        if not cv2.imwrite(filename, frame):
            logger.error("Failed to save captured image")
            result_queue.put(("error", "Failed to save image"))
            return False

        start_time = time.perf_counter()
        try:
            file = client.files.upload(file=filename)
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            result_queue.put(("error", f"Failed to upload file: {str(e)}"))
            return False
        detected = client.models.generate_content(
            model="gemini-2.0-flash-001",
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

        # Send initial update with question and OCR text
        result_queue.put(("question", (question, options, detected)))

        # Start processing model responses
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


class ProcessingThread(Thread):
    def __init__(self, result_queue, client):
        super().__init__()
        self.result_queue = result_queue
        self.client = client
        self.frame_queue = Queue()
        self.running = True
        self.daemon = True
        self.loop = asyncio.new_event_loop()
        logger.debug("ProcessingThread initialized")

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


def main():
    logger.info("Starting application")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        logger.critical("Failed to open camera")
        return

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    result_queue = Queue()
    processing_thread = ProcessingThread(result_queue, client)
    processing_thread.start()

    status = "Ready"
    is_processing = False
    current_question = ""
    current_ocr = ""
    current_responses = None
    last_capture_time = 0
    CAPTURE_COOLDOWN = 1.0

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
