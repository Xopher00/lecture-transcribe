import os

WHISPER_URL = os.environ.get("WHISPER_URL", "http://127.0.0.1:8090")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
CLEANUP_LLM_MODEL = os.environ.get("CLEANUP_LLM_MODEL", "gemma3:4b")

# Never accept a raw filesystem path from the client. whisper-server's /load
# endpoint calls exit(1) on a bad model path, so only these whitelisted,
# pre-validated paths may ever be sent to it.
MODEL_MAP = {
    "small": "/models/ggml-small.bin",
    "medium": "/models/ggml-medium.bin",
}

SESSION_TMP_DIR = os.environ.get("SESSION_TMP_DIR", "/tmp/sessions")

CHUNK_OVERLAP_SECONDS = 1

CLEANUP_SYSTEM_PROMPT = (
    "Your task is to take text provided by the user and improve it for flow and accuracy.\n\n"
    "The text was captured using speech-to-text software from a recorded lecture, "
    "processed in overlapping chunks. You can expect it to contain common "
    "deficiencies of STT-generated text: pause words that were not removed, "
    "missing punctuation, missing paragraphs, and duplicated or near-duplicate "
    "phrases/sentences caused by the chunk overlap. You should fix all of these "
    "for the user.\n\n"
    "You may also be able to infer obvious typos or misheard words. If you "
    "encounter these, you should remediate them.\n\n"
    "In your editing you should:\n"
    "- Preserve the content of the text provided by the user.\n"
    "- Preserve the uniqueness of their voice and perspective.\n\n"
    "In your editing you should not:\n"
    "- Surpass the scope of these editing instructions.\n"
    "- Change the meaning of the text provided by the user or its tone or style.\n\n"
    "Your objective is to take the raw text provided by the user and return it "
    "in an improved and easier to read fashion with defects remedied.\n\n"
    "After applying all these edits you must return the edited text to the "
    "user. Do not add any preface or suffix to the text including friendly "
    "messages. Simply provide the full text in your response without "
    "additional commentary."
)
