const CHUNK_MS = 10000;

const modelSelect = document.getElementById("model");
const recordBtn = document.getElementById("record");
const stopBtn = document.getElementById("stop");
const statusEl = document.getElementById("status");
const liveEl = document.getElementById("live");
const cleanedSection = document.getElementById("cleaned-section");
const cleanedEl = document.getElementById("cleaned");

let mediaStream = null;
let currentRecorder = null;
let isRecording = false;
let sessionId = null;
let chunkIndex = 0;
let chunkTimer = null;
let queueTail = Promise.resolve();

function setStatus(text) {
  statusEl.textContent = text;
}

function createRecorder() {
  const rec = new MediaRecorder(mediaStream);
  rec._chunks = [];
  rec.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) rec._chunks.push(e.data);
  };
  return rec;
}

function stopAndCollect(rec) {
  return new Promise((resolve) => {
    rec.addEventListener(
      "stop",
      () => resolve(new Blob(rec._chunks, { type: rec.mimeType || "audio/webm" })),
      { once: true }
    );
    rec.stop();
  });
}

function uploadChunk(blob, idx) {
  queueTail = queueTail.then(async () => {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("chunk_index", String(idx));
    form.append("chunk", blob, `chunk_${idx}.webm`);
    const res = await fetch("/api/chunk", { method: "POST", body: form });
    if (!res.ok) {
      setStatus(`chunk ${idx} failed`);
      return;
    }
    const data = await res.json();
    if (data.text) {
      liveEl.textContent += (liveEl.textContent ? " " : "") + data.text;
      liveEl.scrollTop = liveEl.scrollHeight;
    }
  });
  return queueTail;
}

async function cycleOnce() {
  const rec = currentRecorder;
  currentRecorder = isRecording ? createRecorder() : null;
  if (currentRecorder) currentRecorder.start();
  const blob = await stopAndCollect(rec);
  const idx = chunkIndex++;
  await uploadChunk(blob, idx);
}

function scheduleNextCycle() {
  chunkTimer = setTimeout(async () => {
    await cycleOnce();
    if (isRecording) scheduleNextCycle();
  }, CHUNK_MS);
}

async function loadModel() {
  recordBtn.disabled = true;
  setStatus("loading model...");
  try {
    const res = await fetch("/api/model/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: modelSelect.value }),
    });
    if (!res.ok) throw new Error(await res.text());
    setStatus("");
  } catch (e) {
    setStatus(`model load failed: ${e.message}`);
  } finally {
    recordBtn.disabled = false;
  }
}

async function startRecording() {
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

  const res = await fetch("/api/session/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const data = await res.json();
  sessionId = data.session_id;
  chunkIndex = 0;
  queueTail = Promise.resolve();
  liveEl.textContent = "";
  cleanedSection.hidden = true;

  isRecording = true;
  currentRecorder = createRecorder();
  currentRecorder.start();
  scheduleNextCycle();

  recordBtn.disabled = true;
  stopBtn.disabled = false;
  modelSelect.disabled = true;
  setStatus("recording...");
}

async function stopRecording() {
  isRecording = false;
  clearTimeout(chunkTimer);
  stopBtn.disabled = true;
  setStatus("finishing last chunk...");

  await cycleOnce();
  await queueTail;

  mediaStream.getTracks().forEach((t) => t.stop());

  setStatus("cleaning up transcript...");
  const res = await fetch("/api/session/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  const data = await res.json();

  cleanedSection.hidden = false;
  if (data.cleaned_transcript) {
    cleanedEl.textContent = data.cleaned_transcript;
  } else {
    cleanedEl.textContent = data.raw_transcript;
    setStatus(data.error || "cleanup unavailable, showing raw transcript");
  }
  if (data.cleaned_transcript) setStatus("");

  recordBtn.disabled = false;
  modelSelect.disabled = false;
}

modelSelect.addEventListener("change", loadModel);
recordBtn.addEventListener("click", startRecording);
stopBtn.addEventListener("click", stopRecording);
