"""
Urdu Voice Lab: download recordings from Supabase into data/audio.

Downloads only the FINAL take of each sentence, saves it as
data/audio/S07/S07_NUM26_spk.webm (take number dropped), and writes
data/audio/manifest.csv. Safe to re-run: files already downloaded are
skipped, and a sentence that was re-recorded is downloaded again.

Needs a .env file in the repo root (never commit it):
    SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
    SUPABASE_SECRET_KEY=sb_secret_...

Usage (from the repo root):
    python tools/download_recordings.py              # all speakers
    python tools/download_recordings.py --speaker S07
"""
import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "data" / "audio"
STATE_FILE = AUDIO_DIR / ".downloaded.json"
MANIFEST = AUDIO_DIR / "manifest.csv"
BUCKET = "recordings"
PAGE = 1000

MANIFEST_COLS = ["file", "speaker_id", "condition", "row_id", "take", "category", "text_read",
                 "entity", "duration_s", "retakes", "clipped", "created_at", "remote_path"]


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        sys.exit("No .env file in the repo root. Create it with SUPABASE_URL and SUPABASE_SECRET_KEY.")
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("SUPABASE_URL", "SUPABASE_SECRET_KEY"):
        if not env.get(k):
            sys.exit(f"{k} is missing in .env")
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SECRET_KEY"]


def headers(key):
    h = {"apikey": key}
    if key.startswith("eyJ"):            # legacy service_role key (JWT) also needs Authorization
        h["Authorization"] = f"Bearer {key}"
    return h


def get(url, key):
    req = urllib.request.Request(url, headers=headers(key))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit(f"Access denied ({e.code}). Check SUPABASE_SECRET_KEY in .env (use the secret key, not the publishable one).")
        raise


def fetch_final_rows(base, key, speaker):
    rows, offset = [], 0
    while True:
        q = {"select": "*", "is_final": "eq.true", "order": "speaker_id,condition,row_id",
             "limit": str(PAGE), "offset": str(offset)}
        if speaker:
            q["speaker_id"] = f"eq.{speaker}"
        batch = json.loads(get(f"{base}/rest/v1/recordings?{urllib.parse.urlencode(q)}", key))
        rows += batch
        if len(batch) < PAGE:
            return rows
        offset += PAGE


def local_name(r):
    ext = r["file_path"].rsplit(".", 1)[-1]
    return f'{r["speaker_id"]}_{r["row_id"]}_{r["condition"]}.{ext}'


def main():
    ap = argparse.ArgumentParser(description="Download final takes from Supabase")
    ap.add_argument("--speaker", help="only this speaker, e.g. S07")
    args = ap.parse_args()

    base, key = load_env()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}

    rows = fetch_final_rows(base, key, args.speaker)
    print(f"{len(rows)} final takes on Supabase")

    new = skipped = failed = 0
    for r in rows:
        name = local_name(r)
        dest = AUDIO_DIR / r["speaker_id"] / name
        if dest.exists() and state.get(name) == r["file_path"]:
            skipped += 1
            continue
        try:
            path = urllib.parse.quote(r["file_path"])
            data = get(f"{base}/storage/v1/object/{BUCKET}/{path}", key)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            state[name] = r["file_path"]
            new += 1
        except Exception as e:
            failed += 1
            print(f"  failed: {r['file_path']} ({e})")
    STATE_FILE.write_text(json.dumps(state, indent=1), encoding="utf-8")

    # manifest: merge with existing rows so a --speaker run keeps other speakers
    existing = {}
    if MANIFEST.exists():
        with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
            existing = {row["file"]: row for row in csv.DictReader(f)}
    for r in rows:
        name = local_name(r)
        if (AUDIO_DIR / r["speaker_id"] / name).exists():
            existing[name] = {c: r.get(c, "") for c in MANIFEST_COLS if c not in ("file", "remote_path")} | {
                "file": name, "remote_path": r["file_path"]}
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS)
        w.writeheader()
        for name in sorted(existing):
            w.writerow(existing[name])

    print(f"downloaded {new}, already had {skipped}, failed {failed}")
    counts = {}
    for row in existing.values():
        k = f'{row["speaker_id"]} {row["condition"]}'
        counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        print(f"  {k}: {counts[k]} files")
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")
    if failed:
        print("Some files failed. Run the script again to retry them.")


if __name__ == "__main__":
    main()
