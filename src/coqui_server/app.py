
from typing import Optional

import aiofiles
import torch
from fastapi import FastAPI, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from TTS.api import TTS

app = FastAPI()

origins = ["*", "http://localhost:8000", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

has_gpu = torch.cuda.is_available()
tts_client = TTS(
    model_name="tts_models/en/vctk/vits",
    progress_bar=False,
    gpu=has_gpu
).to("cuda" if has_gpu else "cpu")


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
    speed: Optional[float] = Form(1.0, description="Controls the playback speed. Available to tune since some speakers can be VERY fast.")
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

    wav = tts_client.tts_to_file(
        text=text,
        speaker=f"p{speaker_id}",
        speed=speed,
        file_path="output.wav"
    )

    async with aiofiles.open(wav, "rb") as audio:
        content = await audio.read()
        return Response(content=content, media_type="audio/wav")
