# Technical Context: AI Helper

## Development Environment

1. Language & Version

   - Python 3.11 or higher
   - Type checking: No
   - Code style: PEP 8

2. Operating System Support

   - Windows
   - macOS
   - Linux

3. Hardware Requirements
   - Webcam/Camera device
   - Internet connection for API access
   - Sufficient RAM for image processing

## Dependencies

1. Core Libraries

   ```toml
   google-genai>=1.5.0     # Google Generative AI
   opencv-python>=4.11.0.86 # Computer vision
   python-dotenv>=1.0.1     # Environment management
   openai>=1.12.0          # OpenRouter API client
   ```

2. API Dependencies

   - Google Gemini API
     - Vision API for text extraction
     - Pro API for text processing
   - OpenRouter API
     - DeepSeek model access
     - Qwen model access

3. Development Tools
   - Virtual environment management
   - Package management (pip/uv)
   - Version control (git)

## Technical Constraints

1. Performance Bounds

   - Camera frame rate: Configurable (CAMERA_FPS)
   - Frame dimensions: Configurable (CAMERA_WIDTH, CAMERA_HEIGHT)
   - Capture cooldown: Required between processes

2. API Limitations

   - Rate limits on API calls
   - Token limits per request
   - Cost considerations per call

3. Resource Management
   - Memory usage for frame buffers
   - Temporary file cleanup
   - Thread management

## Configuration

1. Environment Variables

   ```env
   GEMINI_API_KEY=       # Google Gemini API key
   OPENROUTER_API_KEY=   # OpenRouter API key
   ```

2. Constants (`config.py`)

   - Camera settings
   - Processing parameters
   - UI configurations

3. Error Handling
   - Graceful degradation
   - User-friendly error messages
   - Logging system

## Build & Deployment

1. Installation

   ```bash
   # Virtual environment
   python -m venv venv
   source venv/bin/activate  # Unix
   venv\Scripts\activate     # Windows

   # Dependencies
   pip install -r requirements.txt
   # or
   uv pip install -r requirements.txt
   ```

2. Configuration Setup

   ```bash
   # Unix
   cp .env.example .env
   # Windows
   copy .env.example .env
   ```

3. Execution
   ```bash
   python main.py     # Windows/macOS
   python3 main.py    # Some Linux systems
   ```

## Security Considerations

1. API Key Management

   - Keys stored in .env file
   - File excluded from version control
   - Example file provided for reference

2. Data Handling

   - Temporary files cleaned up
   - No persistent storage of processed images
   - Secure API communication

3. System Access
   - Camera access permissions required
   - Local-only operation
   - No network exposure

## Monitoring & Debugging

1. Logging System

   - Informational logging
   - Error tracking
   - Debug information

2. Status Indicators

   - Real-time UI feedback
   - Error state display
   - Processing status updates

3. Development Aids
   - Frame capture debugging
   - API response inspection
   - Performance monitoring
