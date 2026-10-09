import speech_recognition as sr
import pyttsx3
import webbrowser
from openai import OpenAI


recognizer = sr.Recognizer()


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def aiprocess(command):
    client = OpenAI(
        api_key="Drop Your API key Here"
    )

    completion = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a virtual assistant named HAL, "
                    "You are skilled at tasks like Alexa and Google Assistant."
                )
            },
            {
                "role": "user",
                "content": command
            }
        ]
    )

    return completion.choices[0].message.content


if __name__ == "__main__":

    speak("Hello, My name is Hal, How may I help you today?")

    while True:

        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)

        print("Recognising...")

        try:
            command = recognizer.recognize_google(audio)
            print("YOU SAID:", command)

            command = command.lower()

            if "open youtube" in command:
                speak("Opening YouTube")
                webbrowser.open("https://youtube.com")

            elif "hi" in command:
                speak("HI")
                                                                                                
            elif "hello" in command:
                speak("Hello")

            elif "hey" in command:
                speak("Hey")

            elif "open google" in command:
                speak("Opening Google")
                webbrowser.open("https://google.com")

            elif "open spotify" in command or "listen song" in command or "music" in command:
                speak("Got it")
                webbrowser.open("https://open.spotify.com")

            else:
                print("Asking HAL...")
                output = aiprocess(command)
                print("HAL:", output)
                speak(output)

        except Exception as e:
            print("Error:", e)