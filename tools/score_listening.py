"""
Urdu Voice Lab: listening test results.

Downloads all ratings from Supabase, matches each clip to its voice using
the private key (data/listening/key.csv), and summarizes per voice:
  naturalness   average 1-5 (with a 95% margin of error)
  Pakistani %   share of ratings that heard a Pakistani accent
  Indian %      share that heard an Indian accent
  unsure %      share that could not tell
  wrong word %  share where a listener heard a wrong word

Writes results/listening_summary.csv and results/listening_by_category.csv.

Needs SUPABASE_URL and SUPABASE_SECRET_KEY in .env (same as the download script).

Usage (from the repo root):
    python tools/score_listening.py
"""
import csv
import json
import math
import statistics
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = ROOT / "data" / "listening" / "key.csv"
OUT = ROOT / "results"
PILOT = {"L01"}   # researcher's own pilot session: kept on record, not counted in results
VOICE_INFO = {"azure_uzma": "PK female", "azure_asad": "PK male", "azure_gul": "IN female", "azure_salman": "IN male"}


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("SUPABASE_URL", "SUPABASE_SECRET_KEY"):
        if not env.get(k):
            sys.exit(f"{k} is missing in .env")
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_SECRET_KEY"]


def fetch_ratings(base, key, table="ratings"):
    headers = {"apikey": key}
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"select": "*", "order": "id", "limit": "1000", "offset": str(offset)})
        with urllib.request.urlopen(urllib.request.Request(f"{base}/rest/v1/{table}?{q}", headers=headers), timeout=60) as r:
            batch = json.loads(r.read())
        rows += batch
        if len(batch) < 1000:
            return rows
        offset += 1000


def summarize(rows):
    nat = [r["naturalness"] for r in rows]
    n = len(rows)
    sd = statistics.stdev(nat) if n > 1 else 0
    pct = lambda cond: round(100 * sum(cond(r) for r in rows) / n, 1) if n else ""
    return {
        "n": n,
        "naturalness": round(statistics.mean(nat), 2) if n else "",
        "margin": round(1.96 * sd / math.sqrt(n), 2) if n > 1 else "",
        "pakistani_pct": pct(lambda r: r["accent"] == "pk"),
        "indian_pct": pct(lambda r: r["accent"] == "in"),
        "unsure_pct": pct(lambda r: r["accent"] == "unsure"),
        "wrong_word_pct": pct(lambda r: r["wrong_word"]),
    }


def main():
    if not KEY.exists():
        sys.exit("data/listening/key.csv not found. Run tools/prepare_listening.py first.")
    with KEY.open(encoding="utf-8-sig", newline="") as f:
        key = {r["clip_id"]: r for r in csv.DictReader(f)}
    base, secret = load_env()
    ratings = fetch_ratings(base, secret)
    rows = []
    pilot = sum(r["listener_id"] in PILOT for r in ratings)
    for r in ratings:
        k = key.get(r["clip_id"])
        if k and r["listener_id"] not in PILOT:
            rows.append({**r, "voice": k["voice"], "row_id": k["row_id"], "category": k["category"]})
    if not rows:
        sys.exit(f"No ratings yet (pilot ratings not counted: {pilot}).")
    listeners = sorted({r["listener_id"] for r in rows})
    print(f"{len(rows)} ratings from {len(listeners)} listeners ({', '.join(listeners)})"
          f"{f'   [{pilot} pilot ratings from {sorted(PILOT)} not counted]' if pilot else ''}\n")

    voices = sorted({r["voice"] for r in rows}, key=lambda v: list(VOICE_INFO).index(v) if v in VOICE_INFO else 99)
    summary = []
    print(f"{'voice':<14}{'type':<11}{'n':>5}{'natural (1-5)':>16}{'Pakistani%':>12}{'Indian%':>9}{'unsure%':>9}{'wrong word%':>13}")
    print("-" * 89)
    for v in voices:
        s = summarize([r for r in rows if r["voice"] == v])
        summary.append({"voice": v, "type": VOICE_INFO.get(v, ""), **s})
        nat = f"{s['naturalness']} ±{s['margin']}" if s["margin"] != "" else str(s["naturalness"])
        print(f"{v:<14}{VOICE_INFO.get(v, ''):<11}{s['n']:>5}{nat:>16}{s['pakistani_pct']:>12}{s['indian_pct']:>9}"
              f"{s['unsure_pct']:>9}{s['wrong_word_pct']:>13}")

    by_cat = []
    cats = sorted({r["category"] for r in rows})
    print("\nPakistani accent % by category")
    print(f"{'voice':<14}" + "".join(f"{c:>7}" for c in cats))
    print("-" * (14 + 7 * len(cats)))
    for v in voices:
        cells = []
        for c in cats:
            sub = [r for r in rows if r["voice"] == v and r["category"] == c]
            s = summarize(sub) if sub else {"n": 0, "pakistani_pct": ""}
            if sub:
                by_cat.append({"voice": v, "category": c, **s})
            cells.append(f"{str(s['pakistani_pct']):>7}")
        print(f"{v:<14}" + "".join(cells))

    OUT.mkdir(exist_ok=True)
    for path, data in ((OUT / "listening_summary.csv", summary), (OUT / "listening_by_category.csv", by_cat)):
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    try:
        comments = [c for c in fetch_ratings(base, secret, "listener_comments") if c["listener_id"] not in PILOT]
    except Exception:
        comments = []                                   # table not created yet
    if comments:
        with (OUT / "listening_comments.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["listener_id", "comment", "created_at"], extrasaction="ignore")
            w.writeheader()
            w.writerows(comments)
        print(f"\n{len(comments)} listener comment(s) saved to results/listening_comments.csv (open in Excel to read)")

    print("\nnatural: 1 = very machine-like, 5 = fully natural (± = 95% margin of error)")
    print("saved: results/listening_summary.csv, results/listening_by_category.csv")


if __name__ == "__main__":
    main()
