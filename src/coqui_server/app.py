
import base64
import os
import pathlib
import re
import tempfile
from typing import Optional

import aiofiles
import demoji
import torch
from fastapi import FastAPI, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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

device = "cuda" if torch.cuda.is_available() else "cpu"
tts_client = TTS(
    model_name="tts_models/en/vctk/vits",
    progress_bar=False
).to(device)


def base64_encode(bits: bytes) -> str:
    return str(base64.b64encode(bits), encoding="utf-8")


def detect_markdown_styles(text: str):
    #text_styles = list()
    message = str(text)

    for style in STYLES:
        regex = style["regex"]
        match = re.search(regex, message)

        while match:
            offset = style["offset"]
            group = match.group()
            message = message.replace(group, group[offset:-offset], 1)
            #text_styles.append({"style": style["style"], "start": match.start(), "length": match.end() - match.start() - offset*2})
            match = re.search(regex, message)

    #return {"message": message, "text_styles": text_styles}
    return message


def clean_text_for_tts(text):
    """Cleans text for better TTS output."""

    # Remove empty lines
    text = os.linesep.join([s for s in text.splitlines() if s])

    # Remove emoji
    text = demoji.replace(text, "")

    # Remove Markdown styles
    text = detect_markdown_styles(text)

    #text = text.replace("&", " and ") # Space on both ends to cover cases like Barnes&Noble
    # The TTS models seem to pronounce "&" properly
    text = text.replace("%", " percent")
    text = text.replace("*", "-") # "*" is used by the AI to denote lists and spoken by Coqui
    text = text.replace("  +", "  -") # When preceeded by two spaces, a "+" is used to denote sublists

    #text = text.replace("\n", " ").replace("\r", "").strip()
    text = text.replace("\r", "").strip()
    text = re.sub(" +", " ", text)
    # Avoid replacing newlines with spaces b/c the TTS AI does well with pausing between breaks.
    # The statement above removes all spaces, so when an outline is processed the speech sounds unnatural.

    return text


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/tts", response_class=Response)
async def tts(
    text: str = Form(None, description="Text to convert to speech."),
    speaker_id: int = Form(None, description="VCTK speaker as an integer to use. Note that they're shuffled from the original dataset in Coqui."),
    speed: Optional[float] = Form(1.0, description="Controls the playback speed. Available to tune since some speakers can be VERY fast."),
    encode: Optional[bool] = Form(False, description="Encode the output in base64.")
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

    with tempfile.NamedTemporaryFile() as temp:
        fname = f"{temp.name}.wav"
        fpath = pathlib.Path(fname)
        wav = tts_client.tts_to_file(
            text=clean_text_for_tts(text),
            speaker=f"p{speaker_id}",
            speed=speed,
            file_path=fpath
        )

        async with aiofiles.open(wav, "rb") as audio:
            content = await audio.read()

            if encode:
                content = base64_encode(content)

            return Response(content=content, media_type="audio/wav")
