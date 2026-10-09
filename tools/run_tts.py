"""
Urdu Voice Lab: TTS generator.

Synthesizes every agent-side corpus sentence (rows with use = tts or both)
with a text-to-speech voice, and saves the audio to
data/tts/<voice>/<row_id>_<script>.mp3.

Each sentence is generated in its Urdu-script version ("urdu"), and, where
it differs, also in its English-letters version ("mixed"). Comparing the two
shows how each voice handles English words.

Safe to stop (Ctrl+C) and re-run: clips already generated are skipped.
A log of every clip is kept in data/tts/manifest.csv.

Needs in .env (repo root):
    AZURE_SPEECH_KEY=...
    AZURE_SPEECH_REGION=centralindia

Usage (from the repo root):
    python tools/run_tts.py --voice azure_uzma --limit 3     # quick test
    python tools/run_tts.py --voice azure_uzma               # all 323 clips
"""
import argparse
import csv
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus.csv"
TTS_DIR = ROOT / "data" / "tts"                      # audio files are ignored by git (*.mp3)
MANIFEST = TTS_DIR / "manifest.csv"
COLS = ["voice", "row_id", "category", "script", "text", "file", "chars", "latency_ms", "status", "generated_at"]


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


# ---------- voices ----------
def azure_tts(text: str, cfg: dict, env: dict):
    """Azure neural TTS, REST API. Returns (mp3 bytes, milliseconds)."""
    ssml = (f"<speak version='1.0' xml:lang='{cfg['lang']}'>"
            f"<voice name='{cfg['voice']}'>{escape(text)}</voice></speak>")
    req = urllib.request.Request(
        f"https://{env['AZURE_SPEECH_REGION']}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"), method="POST", headers={
            "Ocp-Apim-Subscription-Key": env["AZURE_SPEECH_KEY"],
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
            "User-Agent": "urdu-voice-lab",
        })
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = r.read()
    return audio, round((time.perf_counter() - t0) * 1000)


AZURE_NEEDS = ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]
# name -> function, voice settings, required .env keys, pause between requests (free tier is rate-limited)
VOICES = {
    "azure_uzma":   {"fn": azure_tts, "voice": "ur-PK-UzmaNeural",   "lang": "ur-PK", "needs": AZURE_NEEDS, "pause": 3.1},
    "azure_asad":   {"fn": azure_tts, "voice": "ur-PK-AsadNeural",   "lang": "ur-PK", "needs": AZURE_NEEDS, "pause": 3.1},
    "azure_gul":    {"fn": azure_tts, "voice": "ur-IN-GulNeural",    "lang": "ur-IN", "needs": AZURE_NEEDS, "pause": 3.1},
    "azure_salman": {"fn": azure_tts, "voice": "ur-IN-SalmanNeural", "lang": "ur-IN", "needs": AZURE_NEEDS, "pause": 3.1},
}


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Generate corpus sentences with a TTS voice")
    ap.add_argument("--voice", required=True, choices=sorted(VOICES))
    ap.add_argument("--limit", type=int, help="stop after this many new clips (for testing)")
    args = ap.parse_args()

    cfg = VOICES[args.voice]
    env = load_env()
    missing = [k for k in cfg["needs"] if not env.get(k)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}")

    with CORPUS.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["use"] != "stt"]   # agent-side sentences only
    items = []
    for r in rows:
        items.append((r, "urdu", r["text_urdu"]))
        if r["text_mixed"] != r["text_urdu"]:
            items.append((r, "mixed", r["text_mixed"]))

    out_dir = TTS_DIR / args.voice
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [it for it in items if not (out_dir / f"{it[0]['id']}_{it[1]}.mp3").exists()]
    already = len(items) - len(todo)
    if args.limit:
        todo = todo[:args.limit]
    print(f"{args.voice}: {len(items)} clips, {already} already done, {len(todo)} to generate")

    new_manifest = not MANIFEST.exists()
    ok = fail = 0
    with MANIFEST.open("a", encoding="utf-8-sig" if new_manifest else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if new_manifest:
            w.writeheader()
        for i, (r, script, text) in enumerate(todo, 1):
            name = f"{r['id']}_{script}.mp3"
            status, ms = "Error", ""
            for attempt in range(5):
                try:
                    audio, ms = cfg["fn"](text, cfg, env)
                    if not audio:
                        status = "Empty"
                        break
                    (out_dir / name).write_bytes(audio)
                    status = "Success"
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429:                     # rate limited: wait and retry
                        time.sleep(20 * (attempt + 1))
                        continue
                    if e.code in (401, 403):
                        sys.exit(f"Access denied ({e.code}). Check the key and region in .env.")
                    status = f"HTTP {e.code}"
                    detail = e.read().decode("utf-8", "replace").strip()[:300]
                    print(f"    says: {detail or '(no message)'}")
                    break
                except Exception as e:                    # network hiccup: short wait and retry
                    status = f"Error: {type(e).__name__}"
                    if attempt == 0:
                        print(f"    error: {str(e)[:300]}")
                    time.sleep(5)
            w.writerow({"voice": args.voice, "row_id": r["id"], "category": r["category"], "script": script,
                        "text": text, "file": f"{args.voice}/{name}", "chars": len(text), "latency_ms": ms,
                        "status": status, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            f.flush()
            ok += status == "Success"
            fail += status != "Success"
            print(f"[{i}/{len(todo)}] {name}: {status}{f' ({ms} ms)' if ms != '' else ''}")
            time.sleep(cfg["pause"])

    print(f"done: {ok} generated, {fail} failed -> data/tts/{args.voice}/")
    if fail:
        print("Run the same command again to retry the failed clips.")


if __name__ == "__main__":
    main()
