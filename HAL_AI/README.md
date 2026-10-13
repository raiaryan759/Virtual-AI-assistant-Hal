# HAL — Personal AI Assistant

## Run on Windows

1. Open a terminal in this folder.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run:

   ```bash
   python hal.py
   ```

## Use it

- Type into the message field and press Enter or click **SEND**.
- Click **MIC / LISTEN** to speak.
- Enter your OpenAI API key in Configuration.
- The default model is `gpt-4o-mini`; if your account cannot access it, select a model available to your API account.
- The key is kept in memory for this session and is not saved to disk.

Voice recognition through Google requires an internet connection. Microphone support requires a working input device and PyAudio.

This is a prototype. Stop Listening may not interrupt a recording call immediately, and Stop Speech may not interrupt an utterance already playing on every Windows TTS driver.
