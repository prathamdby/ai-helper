import cv2
import datetime
from google import genai
import os
from queue import Queue
from threading import Thread


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


def draw_overlay(frame, status="Ready", result_text=""):
    height, width = frame.shape[:2]
    keybinds = ["Controls:", "SPACE - Capture & Analyze", "Q - Quit"]

    for i, bind in enumerate(keybinds):
        draw_text(frame, bind, (20, 30 + i * 35), color=(0, 255, 0), scale=0.5)

    status_text = f"Status: {status}"
    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    status_x = width - text_size[0] - 40
    draw_text(frame, status_text, (status_x, 30), color=(255, 255, 0))

    if result_text:
        lines = [line.strip() for line in result_text.split("\n")]
        q_y = height - 150
        q_x = width // 2 - 400
        draw_text(frame, lines[0], (q_x, q_y), color=(255, 255, 255))

        if len(lines) > 1:
            a_y = height - 80
            a_x = width // 2 - 400
            draw_text(frame, lines[1], (a_x, a_y), color=(0, 255, 255))


def process_frame(frame, client):
    filename = f"capture_{datetime.datetime.now():%Y%m%d_%H%M%S}.jpg"

    try:
        if not cv2.imwrite(filename, frame):
            raise Exception("Failed to save image")

        file = client.files.upload(file=filename)
        detected = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=[
                """Extract text from this image:
If it's a multiple choice question, format as:
Question: <question>
Options: <options>

If it's a regular question, format as:
Question: <question>

Important: Always start with 'Question:' even for simple questions.""",
                file,
            ],
        ).text.strip()

        if not detected:
            raise Exception("No question detected in image")

        question = ""
        options = ""
        for line in detected.split("\n"):
            if line.startswith("Question:"):
                question = line.replace("Question:", "").strip()
            elif line.startswith("Options:"):
                options = line.replace("Options:", "").strip()

        if not question:
            raise Exception("Failed to extract question")

        if options:
            prompt = f"""Multiple Choice Question:
{question}
{options}

Instructions:
1. ONLY respond with the letter (A, B, C, or D) of the correct option
2. Do not write the full answer or any explanation
3. Just the letter, nothing else"""
        else:
            prompt = f"""Answer this question with EXACTLY one word:
{question}

Instructions:
1. If it's a factual question (like capitals, dates, names), give the exact correct answer
2. The answer must be a single word - no explanations, articles (a/an/the), or additional text
3. Proper nouns should be capitalized (e.g., Delhi, Paris, Einstein)"""

        answer = (
            client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=[prompt],
            )
            .text.strip()
            .split()[0]
        )

        if not answer:
            raise Exception("Failed to generate answer")

        question_display = f"{question}\n{options}" if options else question
        return True, f"Q: {question_display}\nA: {answer}"

    except Exception as e:
        return False, f"Error: {str(e)}"

    finally:
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass


class ProcessingThread(Thread):
    def __init__(self, result_queue, client):
        super().__init__()
        self.result_queue = result_queue
        self.client = client
        self.frame_queue = Queue()
        self.running = True
        self.daemon = True

    def run(self):
        while self.running:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                success, result = process_frame(frame, self.client)
                self.result_queue.put((success, result))

    def process(self, frame):
        self.frame_queue.put(frame.copy())

    def stop(self):
        self.running = False


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    result_queue = Queue()
    processing_thread = ProcessingThread(result_queue, client)
    processing_thread.start()

    result_text = ""
    status = "Ready"
    is_processing = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if not result_queue.empty():
            success, new_result = result_queue.get()
            status = "Ready" if success else "Error"
            if success:
                result_text = new_result
            is_processing = False

        display_frame = frame.copy()
        draw_overlay(display_frame, status, result_text)
        cv2.imshow("Live Camera Feed", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord(" ") and not is_processing:
            status = "Processing..."
            is_processing = True
            processing_thread.process(frame)

    processing_thread.stop()
    processing_thread.join()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
