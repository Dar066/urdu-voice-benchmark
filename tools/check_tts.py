"""
Urdu Voice Lab: automatic TTS check (round trip).

Feeds every generated TTS clip (data/tts/<voice>/<row_id>_<script>.mp3)
to local Whisper, then compares what Whisper heard with the sentence the
voice was given. A clip Whisper cannot understand points to unclear or
wrong pronunciation.

This is a relative check between voices, not an absolute score: Whisper
itself makes mistakes, but it makes the same kind of mistakes for every
voice. The listening test remains the main TTS result.

Reports
  by voice and script   Urdu-script input vs English-letters input, on the
                        same sentences (only rows that have both versions)
  by voice and category Urdu-script input, all categories
Writes results/raw/tts_check_<model>.csv (transcripts, resumable),
results/raw/tts_check_scored_<model>.csv (per clip, worst first) and
results/tts_check_summary.csv.

Usage (from the repo root):
    python tools/check_tts.py --limit 5                  # quick test
    python tools/check_tts.py                            # all voices, Whisper large (hours)
    python tools/check_tts.py --voice azure_uzma         # one voice
    python tools/check_tts.py --model turbo              # faster, less accurate judge
"""
import argparse
import csv
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_stt import make_whisper, ROOT          # noqa: E402  (same Whisper setup as the STT benchmark)
from score_stt import normalize, cer, wer, DEVANAGARI   # noqa: E402  (same scoring rules)

CORPUS = ROOT / "data" / "corpus.csv"
TTS_DIR = ROOT / "data" / "tts"
RAW_DIR = ROOT / "results" / "raw"
WAV_DIR = RAW_DIR / "tts_wav16"
SUMMARY = ROOT / "results" / "tts_check_summary.csv"
MODELS = {"large": "models/ggml-large-v3-q5_0.bin", "turbo": "models/ggml-large-v3-turbo-q5_0.bin"}
COLS = ["voice", "row_id", "script", "file", "hypothesis", "status", "latency_ms", "checked_at"]
DONE = {"Success", "NoMatch"}


def to_wav(mp3: Path) -> Path:
    dst = WAV_DIR / mp3.parent.name / (mp3.stem + ".wav")
    if not (dst.exists() and dst.stat().st_mtime >= mp3.stat().st_mtime):
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "16000",
                        "-sample_fmt", "s16", str(dst)], check=True)
    return dst


def load_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def transcribe(args, corpus, voices):
    model = MODELS[args.model]
    if not (ROOT / model).exists():
        sys.exit(f"Model file not found: {model}")
    whisper = make_whisper(model)
    out = RAW_DIR / f"tts_check_{args.model}.csv"
    done = {}
    if out.exists():
        for r in load_csv(out):
            done[(r["voice"], r["file"])] = r
    clips = sorted((v, p) for v in voices for p in (TTS_DIR / v).glob("*.mp3"))
    todo = [(v, p) for v, p in clips if done.get((v, p.name), {}).get("status") not in DONE]
    already = len(clips) - len(todo)
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(clips)} clips in {len(voices)} voice(s), {already} already checked, {len(todo)} to check")

    keep = [r for r in done.values() if r["status"] in DONE]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(keep)
    with out.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        for i, (voice, mp3) in enumerate(todo, 1):
            row_id, script = mp3.stem.rsplit("_", 1)
            try:
                text, status, ms = whisper(to_wav(mp3), {})
            except Exception as e:
                text, status, ms = "", f"Error: {type(e).__name__}", ""
                print(f"    error: {str(e)[:200]}")
            w.writerow({"voice": voice, "row_id": row_id, "script": script, "file": mp3.name, "hypothesis": text,
                        "status": status, "latency_ms": ms,
                        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            f.flush()
            print(f"[{i}/{len(todo)}] {voice}/{mp3.name}: {status}{f' ({ms} ms)' if ms != '' else ''}")
    return out


def score(args, corpus, out):
    scored = []
    for t in load_csv(out):
        c = corpus.get(t["row_id"])
        if not c or t["status"] not in DONE:
            continue
        hyp = normalize(t["hypothesis"])
        best = min((cer(normalize(c[k]), hyp), wer(normalize(c[k]), hyp)) for k in ("text_mixed", "text_urdu"))
        scored.append({"voice": t["voice"], "row_id": t["row_id"], "category": c["category"], "script": t["script"],
                       "cer": round(best[0], 4), "wer": round(best[1], 4),
                       "hindi_script": "yes" if DEVANAGARI.search(t["hypothesis"]) else "no",
                       "given_text": c["text_urdu" if t["script"] == "urdu" else "text_mixed"],
                       "whisper_heard": t["hypothesis"]})
    if not scored:
        sys.exit("Nothing to score yet.")
    scored.sort(key=lambda r: -r["cer"])
    with (RAW_DIR / f"tts_check_scored_{args.model}.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(scored[0]))
        w.writeheader()
        w.writerows(scored)

    pct = lambda xs: round(100 * statistics.mean(xs), 1) if xs else ""
    voices = sorted({r["voice"] for r in scored})
    summary = []

    # 1) Urdu script vs English letters, on the same sentences only
    both = {(r["voice"], r["row_id"]) for r in scored if r["script"] == "mixed"} & \
           {(r["voice"], r["row_id"]) for r in scored if r["script"] == "urdu"}
    print(f"\nBy voice and input script (same {len({k[1] for k in both})} sentences with English words)")
    print(f"{'voice':<15}{'urdu-script CER%':>18}{'english-letters CER%':>22}{'n':>6}")
    print("-" * 61)
    for v in voices:
        u = [r["cer"] for r in scored if r["voice"] == v and r["script"] == "urdu" and (v, r["row_id"]) in both]
        m = [r["cer"] for r in scored if r["voice"] == v and r["script"] == "mixed" and (v, r["row_id"]) in both]
        print(f"{v:<15}{str(pct(u)):>18}{str(pct(m)):>22}{len(u):>6}")
        summary.append({"voice": v, "group": "script", "key": "urdu", "n": len(u), "cer_pct": pct(u)})
        summary.append({"voice": v, "group": "script", "key": "mixed", "n": len(m), "cer_pct": pct(m)})

    # 2) by category, Urdu-script input
    cats = sorted({r["category"] for r in scored})
    print("\nBy voice and category (Urdu-script input), CER%")
    print(f"{'voice':<15}" + "".join(f"{c:>7}" for c in cats) + f"{'ALL':>7}{'unclear':>9}{'hindi':>7}")
    print("-" * (15 + 7 * len(cats) + 23))
    for v in voices:
        rows = [r for r in scored if r["voice"] == v and r["script"] == "urdu"]
        cells = []
        for c in cats:
            val = pct([r["cer"] for r in rows if r["category"] == c])
            cells.append(f"{str(val):>7}")
            summary.append({"voice": v, "group": "category", "key": c, "n": sum(r["category"] == c for r in rows), "cer_pct": val})
        unclear = sum(r["cer"] > 0.5 for r in rows)
        hindi = sum(r["hindi_script"] == "yes" for r in rows)
        print(f"{v:<15}" + "".join(cells) + f"{str(pct([r['cer'] for r in rows])):>7}{unclear:>9}{hindi:>7}")
        summary.append({"voice": v, "group": "category", "key": "ALL", "n": len(rows), "cer_pct": pct([r["cer"] for r in rows])})

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["voice", "group", "key", "n", "cer_pct"])
        w.writeheader()
        w.writerows(summary)
    print(f"\nunclear = clips where Whisper missed more than half the characters (listen to these first)")
    print(f"details, worst first: results/raw/tts_check_scored_{args.model}.csv   summary: {SUMMARY.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description="Round-trip check of TTS clips with local Whisper")
    ap.add_argument("--voice", help="only this voice folder, e.g. azure_uzma")
    ap.add_argument("--model", choices=sorted(MODELS), default="large")
    ap.add_argument("--limit", type=int, help="stop after this many new clips (for testing)")
    ap.add_argument("--score-only", action="store_true", help="skip transcription, just re-score")
    args = ap.parse_args()

    corpus = {r["id"]: r for r in load_csv(CORPUS)}
    voices = [args.voice] if args.voice else sorted(p.name for p in TTS_DIR.iterdir() if p.is_dir() and any(p.glob("*.mp3")))
    if not voices:
        sys.exit("No TTS clips found in data/tts. Run tools/run_tts.py first.")
    out = RAW_DIR / f"tts_check_{args.model}.csv"
    if not args.score_only:
        out = transcribe(args, corpus, voices)
    if out.exists():
        score(args, corpus, out)


if __name__ == "__main__":
    main()
