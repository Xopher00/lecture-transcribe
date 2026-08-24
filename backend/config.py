import os

WHISPER_URL = os.environ.get("WHISPER_URL", "http://127.0.0.1:8090")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
CLEANUP_LLM_MODEL = os.environ.get("CLEANUP_LLM_MODEL", "llama3.2:3b")

# Never accept a raw filesystem path from the client. whisper-server's /load
# endpoint calls exit(1) on a bad model path, so only these whitelisted,
# pre-validated paths may ever be sent to it.
MODEL_MAP = {
    "small": "/models/ggml-small.bin",
    "medium": "/models/ggml-medium.bin",
}

SESSION_TMP_DIR = os.environ.get("SESSION_TMP_DIR", "/tmp/sessions")

CHUNK_OVERLAP_SECONDS = 2

CLEANUP_SYSTEM_PROMPT = (
    "You are a transcript editor. Add punctuation and paragraph breaks, remove "
    "filler words (um, uh, like, you know) and false starts. Do NOT change "
    "wording, meaning, facts, or add/remove substantive content. Output ONLY "
    "the cleaned transcript — no preamble, no commentary."
)
