import asyncio
import edge_tts

# English VOICE_MAP
VOICE_MAP = {
    ("English" , "Male") : "en-US-GuyNeural",
    ("English" , "Female") : "en-US-AriaNeural",
    ("Hindi" , "Male") : "hi-IN-MadhurNeural",
    ("Hindi" , "Female") : "hi-IN-SwaraNeural",
    ("Gujarati" , "Male") : "gu-IN-NiranjanNeural",
    ("Gujarati" , "Female") : "gu-IN-DhwaniNeural"
}


async def text_to_speech(text, output_file = "output_audio.mp3" , language = "English", gender = "Male"):
    """
    Convert text into audio file using edge-tts,
    selecting the voice based on the specified language.
    """
    voice = VOICE_MAP.get((language, gender), VOICE_MAP[("English", "Male")])
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    print(f"Audio saved to {output_file} (voice: {voice})")

if __name__ == "__main__":
    with open("explanation_output.txt", "r", encoding="utf-8") as f:
        explanation_text = f.read()

    print("Generating Speech Audio... (this may take a few seconds)")

    asyncio.run(text_to_speech(explanation_text , language = "English"))

    print("done play audio output_audio.mp3 to hear the explanation")