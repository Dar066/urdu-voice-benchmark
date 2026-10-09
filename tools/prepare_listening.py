"""
Urdu Voice Lab: prepare the blind listening test.

Takes the 24 selected sentences in each of the 4 Azure voices
(Urdu-script versions from data/tts), and:
  - adds 0.6 s of silence to the end of every clip (so no player cuts the last word)
  - gives every clip a random name, so the file name never reveals the voice
  - writes tools/listen/clips/<clip_id>.mp3      (public: served with the page)
  - writes tools/listen/clips.json               (public: sentences + anonymous clip ids)
  - writes data/listening/key.csv                (private key: clip id -> voice; used only for results)

Safe to re-run: an existing key is reused, so clip ids never change once listening starts.

Usage (from the repo root):
    python tools/prepare_listening.py
"""
import csv
import json
import random
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus.csv"
TTS_DIR = ROOT / "data" / "tts"
OUT_DIR = ROOT / "tools" / "listen"
CLIP_DIR = OUT_DIR / "clips"
KEY = ROOT / "data" / "listening" / "key.csv"

VOICES = ["azure_uzma", "azure_asad", "azure_gul", "azure_salman"]
SENTENCES = [                                   # 24 sentences, no gender-specific verb forms
    "GRT20", "GRT03", "GRT04", "GRT06", "GRT12",            # greetings, Arabic/Persian
    "PUR04", "PUR09", "PUR22",                              # pure Urdu
    "PHN11", "PHN15", "PHN17",                              # Urdu sounds
    "ENG01", "ENG12", "ENG13", "ENG17",                     # English words
    "NUM14", "NUM25", "NUM27",                              # numbers in words
    "BIZ03", "BIZ17", "BIZ24",                              # business
    "OFC05",                                                # office
    "DOM02", "DOM08",                                       # phone agent
]


def main():
    with CORPUS.open(encoding="utf-8-sig", newline="") as f:
        corpus = {r["id"]: r for r in csv.DictReader(f)}
    missing = [s for s in SENTENCES if s not in corpus]
    if missing:
        sys.exit(f"Not in corpus: {missing}")

    # key: reuse if it exists (clip ids must stay fixed once listening starts)
    key = {}
    if KEY.exists():
        with KEY.open(encoding="utf-8-sig", newline="") as f:
            key = {(r["voice"], r["row_id"]): r for r in csv.DictReader(f)}
    slot_order = None
    if key:
        slot_order = [None] * len(VOICES)
        for r in key.values():
            slot_order[int(r["slot"])] = r["voice"]
    else:
        slot_order = VOICES[:]
        random.shuffle(slot_order)               # hidden voice order: slot 0..3

    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    KEY.parent.mkdir(parents=True, exist_ok=True)
    sentences_json = []
    for sid in SENTENCES:
        c = corpus[sid]
        clips = []
        for slot, voice in enumerate(slot_order):
            entry = key.get((voice, sid))
            if not entry:
                entry = {"clip_id": secrets.token_hex(4), "voice": voice, "row_id": sid,
                         "category": c["category"], "slot": str(slot)}
                key[(voice, sid)] = entry
            src = TTS_DIR / voice / f"{sid}_urdu.mp3"
            if not src.exists():
                sys.exit(f"Missing TTS clip: {src.relative_to(ROOT)}. Run tools/run_tts.py --voice {voice}")
            dst = CLIP_DIR / f"{entry['clip_id']}.mp3"
            if not dst.exists():
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", "apad=pad_dur=0.6",
                                "-c:a", "libmp3lame", "-b:a", "64k", str(dst)], check=True)
            clips.append(entry["clip_id"])
        sentences_json.append({"row_id": sid, "text": c["text_urdu"], "clips": clips})

    (OUT_DIR / "clips.json").write_text(
        json.dumps({"voices": len(VOICES), "sentences": sentences_json}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    with KEY.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["clip_id", "voice", "row_id", "category", "slot"])
        w.writeheader()
        w.writerows(sorted(key.values(), key=lambda r: (r["row_id"], r["slot"])))

    n = len(list(CLIP_DIR.glob("*.mp3")))
    print(f"{len(SENTENCES)} sentences x {len(VOICES)} voices = {n} clips in tools/listen/clips/")
    print("public list: tools/listen/clips.json   private key: data/listening/key.csv")


if __name__ == "__main__":
    main()
