# Project Brief: AI Helper

## Overview

AI Helper is a real-time computer vision application that uses multiple AI models to analyze and answer questions captured through a camera. It's designed to assist students and educators in quickly verifying answers and getting help with questions.

## Core Requirements

1. Real-time Camera Integration

   - Capture live video feed through webcam/camera device
   - Support frame capture on user command
   - Maintain smooth performance with threading

2. Image Processing & Text Extraction

   - Extract text from captured images using Gemini Vision
   - Support for both multiple choice and open-ended questions
   - Clean text processing for accurate AI model input

3. Multi-Model Analysis

   - Process questions through multiple AI models:
     - Google Gemini Pro
     - DeepSeek Chat
     - Qwen
   - Support for different answer formats (MCQ/open-ended)

4. User Interface
   - Live visual overlay showing status and results
   - Non-blocking UI with asynchronous processing
   - Clear user controls and feedback

## Technical Goals

1. High Performance

   - Efficient frame processing
   - Responsive UI despite AI processing
   - Optimal resource usage

2. Reliability

   - Stable camera connection
   - Error handling for AI model responses
   - Clean shutdown and resource cleanup

3. Accuracy
   - High-quality text extraction
   - Consistent AI model responses
   - Clear result presentation

## Project Scope

- Focus on educational use case
- Support for standard question formats
- Real-time processing and feedback
- Multi-model verification for accuracy
