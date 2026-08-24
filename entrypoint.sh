#!/usr/bin/env bash
set -euo pipefail

if [ ! -f /models/ggml-small.bin ]; then
  echo "FATAL: /models/ggml-small.bin not found. Mount your whisper.cpp models directory to /models (read-only)." >&2
  echo "Example: -v ~/tools/whisper.cpp/models:/models:ro" >&2
  exit 1
fi

export WHISPER_THREADS="${WHISPER_THREADS:-$(nproc)}"

exec supervisord -c /supervisord.conf
