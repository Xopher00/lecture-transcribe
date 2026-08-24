import httpx

from . import config


async def health() -> str:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{config.WHISPER_URL}/health")
            if r.status_code == 200:
                return "ready"
            return "loading"
    except httpx.HTTPError:
        return "down"


async def load_model(model_path: str) -> None:
    """Raises httpx.HTTPStatusError on failure. Caller must have already
    whitelisted model_path via config.MODEL_MAP — this function will happily
    send whatever path it's given."""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{config.WHISPER_URL}/load",
            files={"model": (None, model_path)},
        )
        r.raise_for_status()


async def transcribe(wav_path: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        with open(wav_path, "rb") as f:
            r = await client.post(
                f"{config.WHISPER_URL}/inference",
                files={"file": (wav_path, f, "audio/wav")},
                data={"response_format": "text"},
            )
        r.raise_for_status()
        return r.text
