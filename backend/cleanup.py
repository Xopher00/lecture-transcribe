import httpx

from . import config


class CleanupError(RuntimeError):
    pass


async def clean_transcript(raw_text: str) -> str:
    payload = {
        "model": config.CLEANUP_LLM_MODEL,
        "messages": [
            {"role": "system", "content": config.CLEANUP_SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(f"{config.OLLAMA_URL}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
            return data["message"]["content"].strip()
    except (httpx.HTTPError, KeyError) as e:
        raise CleanupError(str(e)) from e
