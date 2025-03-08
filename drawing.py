import cv2


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
