import os
import queue
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import speech_recognition as sr
import pyttsx3
from openai import OpenAI

# ═══════════════════════════════════════════════
# HAL // NIGHT CITY NEON THEME
# ═══════════════════════════════════════════════

BG = "#070510"          # Near-black midnight violet
PANEL = "#100B20"       # Deep ultraviolet panels
PANEL_ALT = "#19102E"   # Elevated dark purple surfaces

GREEN = "#FF2BD6"       # Hot neon magenta — primary accent
TEAL = "#00F5FF"        # Electric cyber cyan — secondary accent

TEXT = "#F7F0FF"        # Holographic white
MUTED = "#A49ABC"       # Dusty neon lavender
RED = "#FF3864"         # Cyberpunk danger red

BORDER = "#46205F"      # Deep ultraviolet borders
SYSTEM_PROMPT = (
    "You are HAL, a helpful personal desktop AI assistant. "
    "Be clear, conversational, and concise. You can answer questions and help "
    "with everyday tasks, but do not claim to control the computer unless a "
    "supported command actually did so."
)


class HALApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HAL | Personal AI Assistant")
        self.root.geometry("1180x780")
        self.root.minsize(900, 650)
        self.root.configure(bg=BG)

        self.events = queue.Queue()
        self.tts_queue = queue.Queue()
        self.closing = False
        self.busy = False
        self.listening = False
        self.stop_listening_event = threading.Event()
        self.tts_engine_lock = threading.Lock()
        self.conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.voices = []

        self.api_key_var = tk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        # Use a widely available default; the user can change it in Settings.
        self.model_var = tk.StringVar(value=os.getenv("OPENAI_MODEL", " "))
        self.speech_enabled_var = tk.BooleanVar(value=True)
        self.voice_var = tk.StringVar(value="")
        self.rate_var = tk.IntVar(value=175)
        self.volume_var = tk.DoubleVar(value=1.0)
        self.status_var = tk.StringVar(value="READY")
        self.status_detail_var = tk.StringVar(value="Systems online")
        self.input_var = tk.StringVar()

        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.7
        self.recognizer.non_speaking_duration = 0.4

        self._build_styles()
        self._build_ui()
        self._load_voices()
        threading.Thread(target=self._tts_worker, daemon=True, name="HAL-TTS").start()
        self.root.after(80, self._poll_events)
        self.add_message("HAL", "Hello. I'm HAL, your personal AI assistant. How may I help you today?")
        self.set_status("READY", "Systems online")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.input_entry.focus_set()

    def _build_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=GREEN, font=("Segoe UI", 26, "bold"))
        style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=("Consolas", 9))
        style.configure("Status.TLabel", background=BG, foreground=GREEN, font=("Consolas", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(10, 7))
        
        style.configure(
            "Accent.TButton",
            background="#FF2BD6",
            foreground="#070510",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 10),
        )
        style.map(
            "Accent.TButton",
            background=[
                ("active", "#FF70E5"),
                ("disabled", "#54234F"),
            ],
        )
        style.configure(
            "Secondary.TButton",
            background="#19102E",
            foreground="#00F5FF",
            padding=(10, 8),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#302047")],
            foreground=[("active", "#FF2BD6")],
        )

        style.configure("TCheckbutton", background=PANEL, foreground=TEXT)
        style.configure("TCombobox", fieldbackground=PANEL_ALT, background=PANEL_ALT, foreground=TEXT)
        style.configure("Horizontal.TScale", background=PANEL)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        title_box = ttk.Frame(header)
        title_box.pack(side="left", anchor="w")
        ttk.Label(title_box, text="HAL", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="PERSONAL AI ASSISTANT  /  VOICE + INTELLIGENCE",
                  style="Subtitle.TLabel").pack(anchor="w")

        status_box = ttk.Frame(header)
        status_box.pack(side="right", anchor="e")
        self.status_canvas = tk.Canvas(status_box, width=16, height=16, bg=BG, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(0, 7))
        self.status_dot = self.status_canvas.create_oval(3, 3, 13, 13, fill=GREEN, outline="")
        ttk.Label(status_box, textvariable=self.status_var, style="Status.TLabel").pack(anchor="e")
        ttk.Label(status_box, textvariable=self.status_detail_var, style="Muted.TLabel").pack(anchor="e")

        content = ttk.Frame(outer)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3, uniform="panels")
        content.columnconfigure(1, weight=2, uniform="panels")
        content.rowconfigure(0, weight=1)

        left = ttk.Frame(content, style="Panel.TFrame", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = ttk.Frame(content, style="Panel.TFrame", padding=12)
        right.grid(row=0, column=1, sticky="nsew")

        # GRID is intentional here: it reserves rows for the input and action buttons,
        # so the growing transcript cannot push them below the visible window.
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        core_frame = ttk.Frame(left, style="Panel.TFrame")
        core_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.core = tk.Canvas(core_frame, width=112, height=112, bg=PANEL, highlightthickness=0)
        self.core.pack(side="left", padx=(2, 14))
        self._draw_core("READY")
        core_text = ttk.Frame(core_frame, style="Panel.TFrame")
        core_text.pack(side="left", fill="both", expand=True)
        ttk.Label(core_text, text="SYSTEM CORE", style="Panel.TLabel",
                  font=("Consolas", 10, "bold")).pack(anchor="w", pady=(8, 5))
        ttk.Label(core_text, text="Ready when you are.", style="Panel.TLabel",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(core_text, text="Type a message below or use push-to-talk.",
                  style="Panel.TLabel", foreground=MUTED).pack(anchor="w", pady=(6, 0))

        ttk.Label(left, text="CONVERSATION", style="Panel.TLabel",
                  font=("Consolas", 10, "bold")).grid(row=1, column=0, sticky="nw", pady=(0, 6))
        transcript_frame = ttk.Frame(left, style="Panel.TFrame")
        transcript_frame.grid(row=2, column=0, sticky="nsew")
        left.rowconfigure(2, weight=1)
        self.transcript = tk.Text(
            transcript_frame, wrap="word", bg="#091512", fg=TEXT, insertbackground=GREEN,
            selectbackground="#245644", relief="flat", padx=10, pady=10,
            font=("Segoe UI", 10), state="disabled", spacing1=3, spacing3=7
        )
        scroll = ttk.Scrollbar(transcript_frame, orient="vertical", command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scroll.set)
        self.transcript.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.transcript.tag_configure("user_name", foreground=TEAL, font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("hal_name", foreground=GREEN, font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("error_name", foreground=RED, font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("time", foreground=MUTED, font=("Consolas", 8))
        self.transcript.tag_configure("body", foreground=TEXT)

        input_row = ttk.Frame(left, style="Panel.TFrame")
        input_row.grid(row=3, column=0, sticky="ew", pady=(9, 0))
        input_row.columnconfigure(0, weight=1)
        self.input_entry = tk.Entry(
            input_row, textvariable=self.input_var, bg=PANEL_ALT, fg=TEXT,
            insertbackground="#00F5FF", relief="flat", font=("Segoe UI", 11),
            highlightthickness=1, highlightbackground="#46205F", highlightcolor="#00F5FF"
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", ipady=9, padx=(0, 8))
        self.input_entry.bind("<Return>", lambda _event: self.send_typed())
        self.send_button = ttk.Button(input_row, text="SEND", style="Accent.TButton",
                                      command=self.send_typed)
        self.send_button.grid(row=0, column=1, sticky="ew")

        actions = ttk.Frame(left, style="Panel.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.listen_button = ttk.Button(actions, text="MIC / LISTEN",
                                        style="Secondary.TButton", command=self.start_listening)
        self.listen_button.pack(side="left", padx=(0, 6))
        self.stop_button = ttk.Button(actions, text="STOP LISTENING",
                                      style="Secondary.TButton", command=self.stop_listening,
                                      state="disabled")
        self.stop_button.pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="CLEAR CHAT", style="Secondary.TButton",
                   command=self.clear_chat).pack(side="left")
        ttk.Button(actions, text="STOP SPEECH", style="Secondary.TButton",
                   command=self.stop_speech).pack(side="right")

        # Settings panel scrolls if the window is short.
        settings_canvas = tk.Canvas(right, bg=PANEL, highlightthickness=0)
        settings_scroll = ttk.Scrollbar(right, orient="vertical", command=settings_canvas.yview)
        settings_canvas.configure(yscrollcommand=settings_scroll.set)
        settings_scroll.pack(side="right", fill="y")
        settings_canvas.pack(side="left", fill="both", expand=True)
        settings_inner = ttk.Frame(settings_canvas, style="Panel.TFrame", padding=(0, 0, 4, 0))
        settings_window = settings_canvas.create_window((0, 0), window=settings_inner, anchor="nw")

        def update_scroll_region(_event=None):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
            settings_canvas.itemconfigure(settings_window, width=settings_canvas.winfo_width())
        settings_inner.bind("<Configure>", update_scroll_region)
        settings_canvas.bind("<Configure>", update_scroll_region)

        def setting_label(parent, text):
            ttk.Label(parent, text=text, style="Panel.TLabel",
                      font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 5))

        ttk.Label(settings_inner, text="CONFIGURATION", style="Panel.TLabel",
                  font=("Consolas", 10, "bold")).pack(anchor="w", pady=(0, 12))
        setting_label(settings_inner, "OPENAI API KEY")
        self.api_entry = tk.Entry(settings_inner, textvariable=self.api_key_var, show="•",
                                  bg=PANEL_ALT, fg=TEXT, insertbackground=GREEN, relief="flat",
                                  highlightthickness=1, highlightbackground=BORDER)
        self.api_entry.pack(fill="x", ipady=8, pady=(0, 5))
        ttk.Label(settings_inner, text="Kept in memory for this session; OPENAI_API_KEY is supported.",
                  style="Muted.TLabel", wraplength=300).pack(anchor="w", pady=(0, 12))

        setting_label(settings_inner, "MODEL NAME")
        tk.Entry(settings_inner, textvariable=self.model_var, bg=PANEL_ALT, fg=TEXT,
                 insertbackground=GREEN, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER).pack(fill="x", ipady=8, pady=(0, 12))

        setting_label(settings_inner, "TEXT-TO-SPEECH VOICE")
        self.voice_combo = ttk.Combobox(settings_inner, textvariable=self.voice_var, state="readonly")
        self.voice_combo.pack(fill="x", ipady=4, pady=(0, 12))
        ttk.Checkbutton(settings_inner, text="Enable spoken responses",
                        variable=self.speech_enabled_var).pack(anchor="w", pady=(0, 12))

        rate_header = ttk.Frame(settings_inner, style="Panel.TFrame")
        rate_header.pack(fill="x")
        setting_label(rate_header, "SPEECH RATE")
        self.rate_value = ttk.Label(rate_header, text=str(self.rate_var.get()), style="Panel.TLabel")
        self.rate_value.pack(side="right")
        ttk.Scale(settings_inner, from_=120, to=230, variable=self.rate_var,
                  orient="horizontal", command=self._update_rate_label).pack(fill="x", pady=(0, 12))

        volume_header = ttk.Frame(settings_inner, style="Panel.TFrame")
        volume_header.pack(fill="x")
        setting_label(volume_header, "VOLUME")
        self.volume_value = ttk.Label(volume_header, text="100%", style="Panel.TLabel")
        self.volume_value.pack(side="right")
        ttk.Scale(settings_inner, from_=0.0, to=1.0, variable=self.volume_var,
                  orient="horizontal", command=self._update_volume_label).pack(fill="x", pady=(0, 14))

        ttk.Button(settings_inner, text="APPLY SETTINGS", style="Accent.TButton",
                   command=self.apply_settings).pack(fill="x", pady=(0, 14))
        ttk.Separator(settings_inner).pack(fill="x", pady=(0, 12))
        ttk.Label(settings_inner, text="SYSTEM NOTES", style="Panel.TLabel",
                  font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 7))
        notes = ("• Voice recognition requires internet.\n"
                 "• AI requests use your OpenAI API account and may incur charges.\n"
                 "• API keys are not saved to disk.")
        ttk.Label(settings_inner, text=notes, style="Panel.TLabel",
                  justify="left", wraplength=300).pack(anchor="w")

    def _draw_core(self, mode):
            self.core.delete("all")
            cx = cy = 56
            self.core.create_oval(8, 8, 104, 104, outline="#54205F", width=2)
            self.core.create_oval(17, 17, 95, 95, outline="#FF2BD6", width=1)
            self.core.create_oval(26, 26, 86, 86, outline=GREEN if mode != "THINKING" else TEAL, width=2)
            self.core.create_oval(36, 36, 76, 76, fill="#00F5FF", outline=GREEN, width=1)
            self.core.create_text(cx, cy - 1, text="H", fill=GREEN, font=("Consolas", 26, "bold"))
            self.core.create_text(cx, 92, text=mode, fill=MUTED, font=("Consolas", 7, "bold"))
    
    def _load_voices(self):
        try:
            engine = pyttsx3.init()
            self.voices = engine.getProperty("voices") or []
            labels = [f"{i}: {getattr(v, 'name', f'Voice {i + 1}')}" for i, v in enumerate(self.voices)]
            self.voice_combo["values"] = labels
            if labels:
                self.voice_var.set(labels[0])
            engine.stop()
        except Exception as exc:
            self.events.put(("error", f"Could not enumerate TTS voices: {exc}"))

    def _selected_voice_id(self):
        try:
            index = int(self.voice_var.get().split(":", 1)[0])
            return self.voices[index].id
        except (ValueError, IndexError, AttributeError):
            return ""

    def apply_settings(self):
        model = self.model_var.get().strip()
        if not model:
            messagebox.showwarning("HAL Settings", "Enter a model name.")
            return
        self.add_message("HAL", f"Settings applied. Model: {model}. API key remains in memory only.")
        self.set_status("READY", "Settings updated")

    def _update_rate_label(self, _value=None):
        self.rate_value.configure(text=str(int(float(self.rate_var.get()))))

    def _update_volume_label(self, _value=None):
        self.volume_value.configure(text=f"{int(float(self.volume_var.get()) * 100)}%")

    def set_status(self, status, detail=""):
        if self.closing:
            return
        self.status_var.set(status)
        self.status_detail_var.set(detail)
        color = GREEN
        if status == "LISTENING":
            color = TEAL
        elif status in ("THINKING", "SPEAKING"):
            color = "#F0C96A"
        elif status in ("ERROR", "OFFLINE"):
            color = RED
        self.status_canvas.itemconfigure(self.status_dot, fill=color)
        self._draw_core(status)

    def add_message(self, speaker, text):
        if self.closing:
            return
        self.transcript.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = "user_name" if speaker == "YOU" else ("error_name" if speaker == "ERROR" else "hal_name")
        self.transcript.insert("end", f"{speaker}  ", tag)
        self.transcript.insert("end", f"{timestamp}\n", "time")
        self.transcript.insert("end", f"{text}\n\n", "body")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def clear_chat(self):
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")
        self.conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.add_message("HAL", "Conversation cleared. Ready for your next command.")

    def send_typed(self):
        command = self.input_var.get().strip()
        if not command:
            return
        self.input_var.set("")
        self.process_command(command)

    def process_command(self, command, source="typed"):
        if self.closing:
            return
        if self.busy:
            self.add_message("HAL", "I'm still processing the previous request. Please wait.")
            return
        self.add_message("YOU", command)
        self.busy = True
        self.send_button.configure(state="disabled")
        self.listen_button.configure(state="disabled")
        self.set_status("THINKING", "Processing command")
        api_key = self.api_key_var.get().strip() or os.getenv("OPENAI_API_KEY", "").strip()
        model = self.model_var.get().strip()
        # Snapshot conversation on the UI thread.
        history = list(self.conversation)
        threading.Thread(target=self._command_worker,
                         args=(command, api_key, model, history),
                         daemon=True, name="HAL-Command").start()

    def _command_worker(self, command, api_key, model, history):
        normalized = command.lower().strip()
        try:
            if normalized in ("hi", "hello", "hey") or normalized.startswith(("hi ", "hello ", "hey ")):
                response = {"hi": "Hi!", "hello": "Hello!", "hey": "Hey!"}.get(normalized, "Hello! How can I help?")
                self.events.put(("response", response, False, None))
                return
            if normalized in ("open youtube", "open youtube.com"):
                self._open_site("https://youtube.com", "Opening YouTube")
                return
            if normalized in ("open google", "open google.com"):
                self._open_site("https://google.com", "Opening Google")
                return
            if normalized in ("open spotify", "open spotify.com", "play music", "open music"):
                self._open_site("https://open.spotify.com", "Opening Spotify")
                return
            if not api_key:
                self.events.put(("error", "No OpenAI API key found. Enter one in Configuration or set OPENAI_API_KEY."))
                return
            if not model:
                self.events.put(("error", "Enter an OpenAI model name in Configuration."))
                return

            history.append({"role": "user", "content": command})
            self.events.put(("status", "THINKING", "Contacting OpenAI"))
            client = OpenAI(api_key=api_key, timeout=45.0, max_retries=1)
            completion = client.chat.completions.create(model=model, messages=history)
            response = completion.choices[0].message.content or "I received an empty response."
            history.append({"role": "assistant", "content": response})
            self.events.put(("response", response, True, history))
        except Exception as exc:
            self.events.put(("error", self._friendly_error(exc)))

    def _open_site(self, url, response):
        try:
            if webbrowser.open(url, new=2):
                self.events.put(("response", response, False, None))
            else:
                self.events.put(("error", f"Your system did not confirm opening the browser for {url}."))
        except Exception as exc:
            self.events.put(("error", f"Could not open website: {exc}"))

    def _friendly_error(self, exc):
        name = type(exc).__name__
        message = str(exc)
        if name == "AuthenticationError":
            return "OpenAI authentication failed. Check that your API key is correct and active."
        if name == "PermissionDeniedError":
            return "OpenAI denied this request. Check your account and model access."
        if name == "NotFoundError":
            return "The selected model or endpoint was not found. Check the model name and your access."
        if name == "RateLimitError":
            return "OpenAI rate limit or quota reached. Check usage, billing, and rate limits."
        if name in ("APITimeoutError", "Timeout"):
            return "The request timed out. Check your connection and try again."
        if isinstance(exc, sr.UnknownValueError):
            return "I couldn't understand the audio. Please speak clearly and try again."
        if isinstance(exc, sr.RequestError):
            return "Speech recognition service failed. Check your internet connection."
        if isinstance(exc, (OSError, AttributeError)) and "audio" in message.lower():
            return "Microphone/audio error. Check Windows microphone permissions and input device."
        return f"{name}: {message[:300]}"

    def start_listening(self):
        if self.busy or self.listening:
            return
        self.listening = True
        self.stop_listening_event.clear()
        self.listen_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.set_status("LISTENING", "Speak after the prompt")
        threading.Thread(target=self._listen_worker, daemon=True, name="HAL-Microphone").start()

    def _listen_worker(self):
        try:
            with sr.Microphone() as source:
                self.events.put(("status", "LISTENING", "Calibrating microphone"))
                self.recognizer.adjust_for_ambient_noise(source, duration=0.35)
                if self.stop_listening_event.is_set():
                    self.events.put(("listen_done",))
                    return
                self.events.put(("status", "LISTENING", "Listening — speak now"))
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=12)
            if self.stop_listening_event.is_set():
                self.events.put(("listen_done",))
                return
            self.events.put(("status", "THINKING", "Recognizing speech"))
            command = self.recognizer.recognize_google(audio)
            self.events.put(("recognized", command))
        except sr.WaitTimeoutError:
            self.events.put(("error", "No speech detected before the timeout. Click MIC / LISTEN and try again."))
            self.events.put(("listen_done",))
        except Exception as exc:
            self.events.put(("error", self._friendly_error(exc)))
            self.events.put(("listen_done",))

    def stop_listening(self):
        self.stop_listening_event.set()
        self.set_status("READY", "Stopping microphone session")
        self.stop_button.configure(state="disabled")

    def _tts_worker(self):
        engine = None
        while not self.closing:
            try:
                item = self.tts_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if item is None:
                self.tts_queue.task_done()
                break
            text, voice_id, rate, volume = item
            try:
                if engine is None:
                    engine = pyttsx3.init()
                with self.tts_engine_lock:
                    if voice_id:
                        engine.setProperty("voice", voice_id)
                    engine.setProperty("rate", int(rate))
                    engine.setProperty("volume", max(0.0, min(1.0, float(volume))))
                    engine.say(text)
                    self.events.put(("status", "SPEAKING", "HAL is speaking"))
                    engine.runAndWait()
                    self.events.put(("speech_done",))
            except Exception as exc:
                self.events.put(("error", f"Text-to-speech failed: {exc}"))
            finally:
                self.tts_queue.task_done()
        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass

    def stop_speech(self):
        # Clear queued responses. Windows TTS drivers may not interrupt an utterance
        # already inside runAndWait(), so this button is best-effort.
        while True:
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break
        self.add_message("HAL", "Queued speech cleared. An utterance already playing may finish.")

    def _poll_events(self):
        if self.closing:
            return
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "status":
                    self.set_status(event[1], event[2])
                elif kind == "response":
                    response, speak_it, history = event[1], event[2], event[3]
                    self.add_message("HAL", response)
                    if history is not None:
                        self.conversation = history
                    if speak_it and self.speech_enabled_var.get():
                        self.tts_queue.put((response, self._selected_voice_id(),
                                            int(float(self.rate_var.get())),
                                            float(self.volume_var.get())))
                    self.busy = False
                    self.send_button.configure(state="normal")
                    self.listen_button.configure(state="normal")
                    if not self.listening:
                        self.set_status("READY", "Systems online")
                elif kind == "error":
                    self.add_message("ERROR", event[1])
                    self.busy = False
                    self.listening = False
                    self.send_button.configure(state="normal")
                    self.listen_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.set_status("ERROR", "Check message panel")
                elif kind == "recognized":
                    command = event[1]
                    self.listening = False
                    self.listen_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.set_status("READY", "Speech recognized")
                    self.process_command(command, source="voice")
                elif kind == "listen_done":
                    self.listening = False
                    self.listen_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    if not self.busy:
                        self.set_status("READY", "Systems online")
                elif kind == "speech_done":
                    if not self.busy and not self.listening:
                        self.set_status("READY", "Systems online")
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def on_close(self):
        if self.closing:
            return
        self.closing = True
        self.stop_listening_event.set()
        try:
            self.tts_queue.put_nowait(None)
        except queue.Full:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def main():
    root = tk.Tk()
    HALApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
