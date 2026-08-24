import os
import time

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import audio, cleanup, config, session, whisper_client

app = FastAPI()

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


class ModelLoadRequest(BaseModel):
    model: str


class SessionStopRequest(BaseModel):
    session_id: str


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/health")
async def api_health():
    whisper_status = await whisper_client.health()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{config.OLLAMA_URL}/api/tags")
            ollama_status = "ready" if r.status_code == 200 else "down"
    except httpx.HTTPError:
        ollama_status = "down"
    return {"whisper": whisper_status, "ollama": ollama_status}


@app.post("/api/model/load")
async def api_model_load(req: ModelLoadRequest):
    model_path = config.MODEL_MAP.get(req.model)
    if model_path is None:
        raise HTTPException(400, f"unknown model '{req.model}'")
    try:
        await whisper_client.load_model(model_path)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"model load failed: {e}") from e
    return {"model": req.model, "status": "loaded"}


@app.post("/api/session/start")
async def api_session_start():
    state = session.create_session()
    return {"session_id": state.session_id}


@app.post("/api/chunk")
async def api_chunk(
    session_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = None,
):
    state = session.get_session(session_id)
    if state is None:
        raise HTTPException(400, "unknown session_id")

    t_start = time.monotonic()
    webm_path = os.path.join(state.tmp_dir, f"chunk_{chunk_index}.webm")
    wav_path = os.path.join(state.tmp_dir, f"chunk_{chunk_index}.wav")
    combined_path = os.path.join(state.tmp_dir, f"combined_{chunk_index}.wav")
    new_tail_path = os.path.join(state.tmp_dir, f"tail_{chunk_index}.wav")

    with open(webm_path, "wb") as f:
        f.write(await chunk.read())

    try:
        await audio.webm_to_wav(webm_path, wav_path)

        audio_in = wav_path
        if state.prev_tail_wav is not None:
            await audio.concat(state.prev_tail_wav, wav_path, combined_path)
            audio_in = combined_path

        try:
            raw_text = await whisper_client.transcribe(audio_in)
        except httpx.HTTPError as e:
            raise HTTPException(502, f"transcription failed: {e}") from e

        from .overlap import trim_overlap
        new_text = trim_overlap(state.tail_words, raw_text)
        session.record_chunk_text(state, new_text)

        await audio.extract_tail(wav_path, new_tail_path)
        if state.prev_tail_wav and os.path.exists(state.prev_tail_wav):
            os.remove(state.prev_tail_wav)
        state.prev_tail_wav = new_tail_path

    finally:
        for p in (webm_path, wav_path, combined_path):
            if os.path.exists(p):
                os.remove(p)

    state.chunk_count += 1
    elapsed_ms = int((time.monotonic() - t_start) * 1000)
    return {"chunk_index": chunk_index, "text": new_text, "elapsed_ms": elapsed_ms}


@app.post("/api/session/stop")
async def api_session_stop(req: SessionStopRequest):
    state = session.get_session(req.session_id)
    if state is None:
        raise HTTPException(400, "unknown session_id")

    raw_transcript = " ".join(state.full_transcript)
    session.end_session(req.session_id)

    try:
        cleaned = await cleanup.clean_transcript(raw_transcript)
        return {
            "session_id": req.session_id,
            "raw_transcript": raw_transcript,
            "cleaned_transcript": cleaned,
        }
    except cleanup.CleanupError as e:
        return {
            "session_id": req.session_id,
            "raw_transcript": raw_transcript,
            "cleaned_transcript": None,
            "error": f"cleanup LLM unavailable: {e}",
        }
