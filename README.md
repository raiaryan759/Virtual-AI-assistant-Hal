# HAL — Virtual AI Assistant

A Python-based personal AI assistant with voice interaction, AI-powered conversations, text-to-speech, and a graphical user interface with a futuristic cyberpunk-inspired design.

HAL is a desktop assistant project inspired by AI systems from science fiction, Alexa, and Google Assistant. It combines speech recognition, natural-sounding spoken responses, OpenAI's API, and Python automation in a single application.

## Features

- **Graphical User Interface:** A custom desktop GUI with a dark, neon-inspired cyberpunk aesthetic.
- **Voice Recognition:** Recognizes spoken commands using `SpeechRecognition`.
- **Text-to-Speech:** Responds verbally using `pyttsx3`.
- **AI-Powered Conversations:** Uses the OpenAI API to process questions and generate intelligent responses.
- **Website Automation:** Opens websites such as YouTube, Google, and Spotify through voice commands.
- **Basic Conversations:** Handles greetings such as "Hi", "Hello", and "Hey".
- **Python Automation:** Combines AI, voice interaction, and browser automation in a Python application.

## Technologies Used

- **Python** — Core application logic
- **Tkinter / CustomTkinter** — Graphical user interface
- **SpeechRecognition** — Speech input processing
- **pyttsx3** — Text-to-speech
- **OpenAI API** — AI-powered responses
- **Webbrowser** — Website launching

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Virtual-AI-assistant-Hal.git
cd Virtual-AI-assistant-Hal
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Install Dependencies

Install the libraries used by your project:

```bash
pip install SpeechRecognition pyttsx3 openai
```

If your GUI uses CustomTkinter, install it as well:

```bash
pip install customtkinter
```

Depending on your microphone setup, you may also need to install the appropriate audio input dependencies.

### 3. Configure Your OpenAI API Key

Store your API key in an environment variable instead of hardcoding it in your source code.

For Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-api-key"
```

Ensure your Python application reads the key securely from the environment.

### 4. Run HAL

Run the main Python file used by your project:

```bash
python main.py
```

Replace `main.py` with your actual entry-point filename if it differs.

Grant microphone access if prompted, then interact with HAL through the available GUI and voice controls.

## Security

- Never commit your OpenAI API key or other credentials to GitHub.
- Use environment variables to manage API keys securely.
- Keep private configuration files out of version control using `.gitignore`.

## Project Goals

HAL is a personal project exploring the development of a desktop AI assistant through:

- Graphical user interface design
- Voice recognition and speech synthesis
- AI integration using the OpenAI API
- Python-based automation
- Interactive desktop application development

The long-term goal is to evolve HAL into a more capable personal assistant with an improved interface, responsive voice interactions, and additional desktop utilities.

---

*Built with Python, curiosity, and inspiration from science-fiction AI systems.*
