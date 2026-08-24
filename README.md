# Lecture Transcribe

A small, personal, fully-local lecture transcription tool. One Docker container runs
[whisper.cpp](https://github.com/ggerganov/whisper.cpp) for speech-to-text and
[Ollama](https://ollama.com) for a local cleanup pass (punctuation, paragraphs, filler-word
removal) — nothing is sent to any third-party API. A browser page provides mic capture, a
model-size toggle, a live transcript, and the cleaned-up result after you hit Stop.

## Run locally

Requires the whisper.cpp `ggml-small.bin` (and optionally `ggml-medium.bin`) model files —
see [whisper.cpp's model download script](https://github.com/ggerganov/whisper.cpp/tree/master/models)
if you don't already have them.

```bash
docker build -t lecture-transcribe .

docker run -d --name lecture-transcribe --restart unless-stopped \
  -p 8080:8080 \
  -v /path/to/your/whisper-models:/models:ro \
  -v lecture-ollama-data:/root/.ollama \
  -e CLEANUP_LLM_MODEL=llama3.2:3b-instruct \
  lecture-transcribe:latest
```

Open `http://localhost:8080`. First boot will take a bit longer while Ollama pulls the cleanup
model — check `curl http://localhost:8080/api/health` until both `whisper` and `ollama` report
`"ready"`.

**Note:** `getUserMedia` (mic access) requires a "secure context." Browsers exempt `localhost`
automatically, so local use works with no extra setup. Any non-local deployment needs HTTPS
before the microphone will work at all — see below.

## Deploying to your own remote server

The container itself has no authentication built in — access control is deliberately kept out
of the app and handled at the infrastructure layer instead, to keep the tool itself small and
focused.

Recommended: **Cloudflare Tunnel + Cloudflare Access**
1. Install `cloudflared` on your server and create a tunnel pointing at `localhost:8080`
   (no inbound port needs to be opened — the tunnel is an outbound-only connection to
   Cloudflare's edge).
2. In the Cloudflare Zero Trust dashboard, create an Access application for the tunnel's
   hostname, with a policy restricted to an explicit allow-list — just your own email address.
   This is default-deny: anyone else who visits gets rejected by the policy before ever
   reaching the app, even if they attempt to log in with their own email.
3. This also solves the HTTPS requirement above — the tunnel terminates TLS for you.

Simpler fallback if you'd rather not depend on Cloudflare: put a reverse proxy (e.g. Caddy) in
front of the container with HTTP Basic Auth and automatic HTTPS. A few lines of Caddyfile
config, no app changes either way.

## Known limitations

- `medium` model may not keep up with live/real-time use under sustained load on modest
  hardware — validated as real-time-safe on a 20-thread machine, `small` is the safer default.
- Cleanup pass may exceed the default cleanup model's context window on very long
  (~90+ minute) recordings.
- Browser mic capture via `MediaRecorder`/WebM is solid in Chrome/Firefox; Safari/iOS support
  is weak.
- Both whisper models in use are multilingual (not the `.en`-only variants) — the cleanup LLM's
  non-English quality hasn't been separately verified.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `WHISPER_THREADS` | `nproc` | threads for whisper-server |
| `CLEANUP_LLM_MODEL` | `llama3.2:3b-instruct` | Ollama model used for the cleanup pass |
