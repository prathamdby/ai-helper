# AI Helper

A computer vision application that captures images through your camera and uses Google's Gemini AI to analyze and answer questions in real-time. Perfect for students and educators who want to quickly verify answers or get help with questions.

## Features

- Real-time camera feed with OpenCV
- Text extraction from images using Gemini AI
- Support for both multiple choice and open-ended questions
- Live visual overlay with controls and status
- Threading support for smooth performance
- Non-blocking UI with asynchronous processing

## Requirements

- Python 3.11 or higher
- Webcam/Camera device
- Google Gemini API key

## Dependencies

- `google-genai>=1.5.0`: Google Generative AI client library
- `opencv-python>=4.11.0.86`: OpenCV for computer vision
- `python-dotenv>=1.0.1`: Environment variable management

## Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/prathamdby/ai-helper.git
   cd ai-helper
   ```

2. Create a virtual environment:

   ```shell
   python -m venv venv
   ```

3. Activate the virtual environment:

   On Windows:

   ```shell
   venv\Scripts\activate
   ```

   On macOS/Linux:

   ```shell
   source venv/bin/activate
   ```

4. Install dependencies:

   Using pip:

   ```shell
   pip install -r requirements.txt
   ```

   Or using uv (faster):

   ```shell
   uv pip install -r requirements.txt
   ```

## Configuration

1. Create a new .env file:

   On Windows:

   ```shell
   copy .env.example .env
   ```

   On macOS/Linux:

   ```shell
   cp .env.example .env
   ```

2. Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

1. Ensure your camera is connected and accessible

2. Run the application:

   On Windows/macOS:

   ```shell
   python main.py
   ```

   On some Linux systems:

   ```shell
   python3 main.py
   ```

3. Controls:
   - `SPACE` - Capture and analyze the current frame
   - `Q` - Quit the application

## How it Works

1. The application captures video feed from your camera
2. When you press SPACE, it captures the current frame
3. The image is processed to extract text using Gemini AI
4. For multiple choice questions:
   - Returns the correct option letter (A, B, C, or D)
5. For open-ended questions:
   - Returns a concise one-word answer
6. Results are displayed in real-time on the video feed

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
