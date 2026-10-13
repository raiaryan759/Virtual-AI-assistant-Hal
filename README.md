# HAL — Virtual AI Assistant

HAL is a Python-based AI assistant featuring a futuristic cyberpunk-inspired GUI, voice recognition, text-to-speech, and AI-powered conversations using OpenAI's API.

## Features

- **Graphical User Interface:** Neon cyberpunk-inspired design.
- **Voice Recognition:** Recognizes spoken commands using SpeechRecognition.
- **Text-to-Speech:** Responds verbally using pyttsx3.
- **AI-Powered Responses:** Answers questions using the OpenAI API.
- **Website Automation:** Opens YouTube, Google, and Spotify.
- **Basic Conversations:** Responds to greetings and simple commands.

## Technologies Used

- Python
- Tkinter / CustomTkinter
- SpeechRecognition
- pyttsx3
- OpenAI API
- Webbrowser

## Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/raiaryan759/Virtual-AI-assistant-Hal.git
   cd Virtual-AI-assistant-Hal
   ```

2. Install the required libraries:

   ```bash
   pip install SpeechRecognition pyttsx3 openai customtkinter
   ```

3. Set your OpenAI API key as an environment variable in PowerShell:

   ```powershell
   $env:OPENAI_API_KEY="your-api-key"
   ```

4. Run the main Python file:

   ```bash
   python main.py
   ```

## Usage

- Launch HAL using the setup instructions above.
- Use the GUI controls to interact with the assistant.
- Speak into your microphone to give voice commands.
- Ask questions to receive AI-powered responses.
- Use supported commands to open websites such as YouTube, Google, and Spotify.

## Security

- Never upload your OpenAI API key to GitHub.
- Keep API keys and other sensitive information private.

---

