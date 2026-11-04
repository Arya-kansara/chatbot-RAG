
import asyncio
import edge_tts
import re

def clean_for_speech(text):
    text = re.sub(r'```.*?```', ' The code example is shown on screen. ', text, flags=re.S)
    text = re.sub(r'^[\s|:\-]{3,}$', '', text, flags=re.M)   # table divider rows
    text = re.sub(r'^\s*[-+]\s+', '', text, flags=re.M)        # bullet markers
    text = re.sub(r'[*_`#>|]+', ' ', text)                     # markdown symbols
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()



# English VOICE_MAP
VOICE_MAP = {
    ("English", "Male"): "en-US-GuyNeural",
    ("English", "Female"): "en-US-AriaNeural",
    ("Hindi", "Male"): "hi-IN-MadhurNeural",
    ("Hindi", "Female"): "hi-IN-SwaraNeural",
    ("Gujarati", "Male"): "gu-IN-NiranjanNeural",
    ("Gujarati", "Female"): "gu-IN-DhwaniNeural"
}


async def text_to_speech_bytes(text, language="English", gender="Male"):
    voice = VOICE_MAP.get((language, gender), VOICE_MAP[("English", "Male")])

    spoken = clean_for_speech(text)
    if not spoken:
        raise ValueError("Nothing to read aloud.")

    communicate = edge_tts.Communicate(spoken, voice)
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    if not audio_chunks:
        raise RuntimeError("No audio received from the voice service.")

    return b"".join(audio_chunks)

if __name__ == "__main__":
    with open("explanation_output.txt", "r", encoding="utf-8") as f:
        explanation_text = f.read()

    print("Generating speech audio...")

    audio_bytes = asyncio.run(
        text_to_speech_bytes(
            explanation_text,
            language="English"
        )
    )

    print(f"Audio generated successfully: {len(audio_bytes)} bytes")
