"""
Urdu Voice Lab: STT runner.

Converts each recording in data/audio to 16 kHz mono WAV, sends it to a
speech-to-text provider, and saves the transcript to
results/raw/stt_<provider>.csv. Safe to stop (Ctrl+C) and re-run: files
already transcribed are skipped.

Needs ffmpeg, and provider keys in .env (repo root), e.g.
    AZURE_SPEECH_KEY=...
    AZURE_SPEECH_REGION=centralindia

Usage (from the repo root):
    python tools/run_stt.py --provider azure --limit 3     # quick test
    python tools/run_stt.py --provider azure               # everything
    python tools/run_stt.py --provider azure --speaker S07
    python tools/run_stt.py --provider whisper_turbo        # local, needs models/ggml-large-v3-turbo-q5_0.bin
    python tools/run_stt.py --provider whisper_large        # local, needs models/ggml-large-v3-q5_0.bin
    python tools/run_stt.py --provider elevenlabs           # cloud, needs ELEVENLABS_API_KEY in .env
"""
import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "data" / "audio"
MANIFEST = AUDIO_DIR / "manifest.csv"
RAW_DIR = ROOT / "results" / "raw"          # ignored by git
WAV_DIR = RAW_DIR / "wav16"
OUT_COLS = ["file", "speaker_id", "condition", "row_id", "provider", "hypothesis", "status", "latency_ms", "transcribed_at"]
DONE_STATUSES = {"Success", "NoMatch"}       # anything else is retried on the next run


# ---------- setup helpers ----------
def load_env():
    path = ROOT / ".env"
    if not path.exists():
        sys.exit("No .env file in the repo root.")
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def to_wav(src: Path) -> Path:
    dst = WAV_DIR / src.parent.name / (src.stem + ".wav")
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(dst)]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("ffmpeg not found. Install it and open a new PowerShell window.")
    return dst


# ---------- providers ----------
def azure(wav_path: Path, env: dict):
    """Azure Speech REST API for short audio (up to 60 s). Azure STT has no ur-PK model; ur-IN is its only Urdu."""
    url = (f"https://{env['AZURE_SPEECH_REGION']}.stt.speech.microsoft.com/speech/recognition/"
           "conversation/cognitiveservices/v1?language=ur-IN&format=simple&profanity=raw")
    req = urllib.request.Request(url, data=wav_path.read_bytes(), method="POST", headers={
        "Ocp-Apim-Subscription-Key": env["AZURE_SPEECH_KEY"],
        "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
        "Accept": "application/json",
    })
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=90) as r:
        body = json.loads(r.read())
    ms = round((time.perf_counter() - t0) * 1000)
    status = body.get("RecognitionStatus", "Unknown")
    return (body.get("DisplayText", "") if status == "Success" else ""), status, ms


def elevenlabs(wav_path: Path, env: dict):
    """ElevenLabs Scribe v2 speech-to-text, language Urdu."""
    boundary = uuid.uuid4().hex
    fields = {"model_id": "scribe_v2", "language_code": "urd", "tag_audio_events": "false"}
    body = b"".join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                    for k, v in fields.items())
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{wav_path.name}"\r\n'
             "Content-Type: audio/wav\r\n\r\n").encode() + wav_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST", headers={
        "xi-api-key": env["ELEVENLABS_API_KEY"],
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    ms = round((time.perf_counter() - t0) * 1000)
    text = (data.get("text") or "").strip()
    return text, ("Success" if text else "NoMatch"), ms


WHISPER_TIMEOUT = 180   # seconds per recording; longer means the model is stuck


def make_whisper(model: str):
    """Local Whisper through ffmpeg's built-in whisper filter (whisper.cpp). No internet, no key."""
    def run(wav_path: Path, env: dict):
        rel = wav_path.relative_to(ROOT).as_posix()      # relative paths: no Windows drive colon in filter options
        cmd = ["ffmpeg", "-v", "error", "-i", rel, "-af",
               f"whisper=model={model}:language=ur:queue=60:destination=-:format=text", "-f", "null", "-"]
        t0 = time.perf_counter()
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=WHISPER_TIMEOUT)
        except subprocess.TimeoutExpired:                 # stuck (e.g. repetition loop): stop it and move on
            return "", "Timeout", round((time.perf_counter() - t0) * 1000)
        ms = round((time.perf_counter() - t0) * 1000)
        if p.returncode != 0:
            raise RuntimeError(p.stderr.strip()[-300:])
        text = " ".join(line.strip() for line in p.stdout.splitlines() if line.strip())
        return text, ("Success" if text else "NoMatch"), ms
    return run


# name -> function, required .env keys, pause between requests (seconds; free tiers are rate-limited),
#         local model file (if any)
PROVIDERS = {
    "azure": {"fn": azure, "needs": ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"], "pause": 3.1},
    "elevenlabs": {"fn": elevenlabs, "needs": ["ELEVENLABS_API_KEY"], "pause": 1.0},
    "whisper_turbo": {"fn": make_whisper("models/ggml-large-v3-turbo-q5_0.bin"), "needs": [], "pause": 0,
                      "model": "models/ggml-large-v3-turbo-q5_0.bin"},
    "whisper_large": {"fn": make_whisper("models/ggml-large-v3-q5_0.bin"), "needs": [], "pause": 0,
                      "model": "models/ggml-large-v3-q5_0.bin"},
}


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Transcribe recordings with an STT provider")
    ap.add_argument("--provider", required=True, choices=sorted(PROVIDERS))
    ap.add_argument("--speaker", help="only this speaker, e.g. S07")
    ap.add_argument("--limit", type=int, help="stop after this many new files (for testing)")
    args = ap.parse_args()

    prov = PROVIDERS[args.provider]
    env = load_env()
    missing = [k for k in prov["needs"] if not env.get(k)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}")
    if prov.get("model") and not (ROOT / prov["model"]).exists():
        sys.exit(f"Model file not found: {prov['model']}. Download it into the models folder first.")
    if not MANIFEST.exists():
        sys.exit("data/audio/manifest.csv not found. Run tools/download_recordings.py first.")

    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        items = [r for r in csv.DictReader(f) if r["row_id"] != "CONSENT"]
    if args.speaker:
        items = [r for r in items if r["speaker_id"] == args.speaker]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"stt_{args.provider}.csv"
    done = {}
    if out_path.exists():
        with out_path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                done[r["file"]] = r
    def needs_run(r):
        d = done.get(r["file"])
        if not d or d.get("status") not in DONE_STATUSES:
            return True
        src = AUDIO_DIR / r["speaker_id"] / r["file"]      # re-recorded since the last transcript? run again
        try:
            return src.exists() and src.stat().st_mtime > datetime.fromisoformat(d["transcribed_at"]).timestamp()
        except (KeyError, ValueError):
            return False

    todo = [r for r in items if needs_run(r)]
    already = len(items) - len(todo)
    if args.limit:
        todo = todo[:args.limit]
    print(f"{args.provider}: {len(items)} recordings, {already} already done, {len(todo)} to transcribe")

    # rewrite the file without failed rows, then append as we go (safe to stop any time)
    redo = {r["file"] for r in todo}
    keep = [r for r in done.values() if r.get("status") in DONE_STATUSES and r["file"] not in redo]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(keep)

    ok = fail = 0
    with out_path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        for i, r in enumerate(todo, 1):
            src = AUDIO_DIR / r["speaker_id"] / r["file"]
            if not src.exists():
                print(f"[{i}/{len(todo)}] {r['file']}: audio file missing, skipped")
                continue
            wav = to_wav(src)
            text, status, ms = "", "Error", ""
            for attempt in range(5):
                try:
                    text, status, ms = prov["fn"](wav, env)
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429:                      # rate limited: wait and retry
                        time.sleep(20 * (attempt + 1))
                        continue
                    if e.code in (401, 403):
                        sys.exit(f"Access denied ({e.code}). Check the {args.provider} key and region in .env.")
                    status = f"HTTP {e.code}"
                    detail = e.read().decode("utf-8", "replace").strip()[:300]
                    print(f"    {args.provider} says: {detail or '(no message)'}")
                    break
                except Exception as e:                     # network hiccup / local error: short wait and retry
                    status = f"Error: {type(e).__name__}"
                    if attempt == 0:
                        print(f"    {args.provider} error: {str(e)[:300]}")
                    time.sleep(5)
            w.writerow({"file": r["file"], "speaker_id": r["speaker_id"], "condition": r["condition"],
                        "row_id": r["row_id"], "provider": args.provider, "hypothesis": text,
                        "status": status, "latency_ms": ms,
                        "transcribed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            f.flush()
            if status in DONE_STATUSES:
                ok += 1
            else:
                fail += 1
            print(f"[{i}/{len(todo)}] {r['file']}: {status}{f' ({ms} ms)' if ms != '' else ''}")
            time.sleep(prov["pause"])

    print(f"done: {ok} transcribed, {fail} failed -> {out_path.relative_to(ROOT)}")
    if fail:
        print("Run the same command again to retry the failed files.")


if __name__ == "__main__":
    main()
