import re
from os import linesep
from typing import Optional

import aiofiles
import demoji
from fastapi import FastAPI, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pyflac import FileEncoder as AudioEncoder
from torch import cuda
from TTS.api import TTS

STYLES = [
    {"style": "BOLD", "regex": r"\*\*(.*?)\*\*", "offset": 2},
    {"style": "ITALIC", "regex": r"\*(.*?)\*", "offset": 1}
]

app = FastAPI()
origins = ["*", "http://localhost:8000", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = "cuda" if cuda.is_available() else "cpu"
tts_client = TTS(
    model_name="tts_models/en/vctk/vits",
    progress_bar=False
).to(device)


def remove_markdown_styles(text: str):
    #text_styles = list()
    message = str(text)

    for style in STYLES:
        regex = style["regex"]
        offset = style["offset"]
        match = re.search(regex, message)

        while match:
            group = match.group()
            message = message.replace(group, group[offset:-offset], 1)
            #text_styles.append({"style": style["style"], "start": match.start(), "length": match.end() - match.start() - offset*2})
            match = re.search(regex, message)

    #return {"message": message, "text_styles": text_styles}
    return message


def replace_asterisk_with_times(expression):
    # This pattern matches an asterisk that is:
    # - preceded by either a digit or a closing bracket
    # - followed by either a digit or an opening bracket
    # This keeps Markdown bullet points (e.g., "* Item") unchanged.
    pattern = r'(?<=[\d\)\}\]$])\*(?=[\d\(\{\[$])'
    return re.sub(pattern, ' times ', expression)


def clean_text_for_tts(text):
    """Cleans text for better TTS output."""

    text = linesep.join([s for s in text.splitlines() if s]) # Remove empty lines
    text = demoji.replace(text, "") # Remove emoji
    text = remove_markdown_styles(text)
    text = text.replace(" %", "percent").replace("%", " percent")
    text = replace_asterisk_with_times(text.replace("·", "*")).replace("*", "-") # An "*" is spoken as "asterisk" by Coqui, so we don't want any in the text.
    text = text.replace("  +", "  -") # When preceeded by two spaces, a "+" is used to denote list items
    text = text.replace("\r", "").strip() # Avoid replacing newlines with spaces b/c the TTS AI does well with pausing between breaks.
    text = re.sub(" +", " ", text) # Remove all excess whitespace, so when an outline is spoken the speech sounds more natural.

    # Update all temperatures
    text = text.replace("°F", "° Fahrenheit")
    text = text.replace("°C", "° Celsius")
    text = text.replace("°K", "° Kelvin")

    return text


@app.get("/")
async def read_root():
    return {"device": device}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/tts")
async def tts(
    text: str = Form(None, description="Text to convert to speech."),
    speaker_id: int = Form(None, description="VCTK speaker as an integer to use. Note that they're shuffled from the original dataset in Coqui."),
    speed: Optional[float] = Form(1.0, description="Controls the playback speed. Available to tune since some speakers can be VERY fast."),
    compress: Optional[bool] = Form(True, description="Compress the audio into FLAC.")
):
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text to convert into speech must be provided.",
        )

    if not speaker_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Speaker ID must be provided.",
        )

    async with aiofiles.tempfile.NamedTemporaryFile(mode="w+t", delete=True) as output_wav:
        wav_file = tts_client.tts_to_file(
            text=clean_text_for_tts(text),
            speaker=f"p{speaker_id}",
            speed=speed,
            file_path=output_wav.name
        )

        if compress:
            async with aiofiles.tempfile.NamedTemporaryFile(mode="w+t", delete=True) as output_flac:
                flac_file = output_flac.name
                encoder = AudioEncoder(input_file=wav_file, output_file=flac_file)
                encoder.process()
                encoder.finish()

                async with aiofiles.open(flac_file, "rb") as flac:
                    content = await flac.read()
                    return Response(content=content, media_type="audio/flac")

        async with aiofiles.open(wav_file, "rb") as audio:
            content = await audio.read()
            return Response(content=content, media_type="audio/wav")
