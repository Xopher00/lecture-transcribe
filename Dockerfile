# --- Stage 1: build whisper-server from a pinned commit ---
FROM debian:bookworm-slim AS whisper-build

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake make g++ git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone https://github.com/ggerganov/whisper.cpp.git . \
    && git checkout c122757fddf358397bb7f33b6ac3aab24a5bca04
RUN cmake -B build && cmake --build build -j"$(nproc)" --config Release --target whisper-server

# --- Stage 2: runtime ---
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 ca-certificates curl ffmpeg sox python3 python3-venv supervisor zstd \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://ollama.com/install.sh | sh

COPY --from=whisper-build /src/build/bin/whisper-server /usr/local/bin/whisper-server
COPY --from=whisper-build /src/build/bin/*.so* /usr/local/lib/
RUN ldconfig

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY static/ ./static/
COPY supervisord.conf /supervisord.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/models", "/root/.ollama"]
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
