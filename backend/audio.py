import asyncio

from . import config


class AudioError(RuntimeError):
    pass


async def _run(*args: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise AudioError(f"{args[0]} failed: {stderr.decode(errors='replace')[:500]}")


async def webm_to_wav(webm_path: str, wav_path: str) -> None:
    await _run(
        "ffmpeg", "-y", "-i", webm_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        wav_path,
    )


async def extract_tail(wav_path: str, out_path: str, seconds: int = config.CHUNK_OVERLAP_SECONDS) -> None:
    await _run("sox", wav_path, out_path, "trim", f"-{seconds}")


async def concat(first_path: str, second_path: str, out_path: str) -> None:
    await _run("sox", first_path, second_path, out_path)
