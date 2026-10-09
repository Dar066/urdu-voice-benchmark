"""
Urdu Voice Lab: STT scorer.

Compares every transcript in results/raw/stt_<provider>.csv with the
corpus and prints a results table per provider and category.

Metrics
  CER   character error rate (spaces ignored; Urdu word spacing is inconsistent)
  WER   word error rate
        Both are "script-agnostic": scored against the English-letters version
        (text_mixed) and the Urdu-script version (text_urdu) of each sentence,
        and the better match is used, so writing "appointment" vs "اپائنٹمنٹ"
        is not counted as an error.
  Phone/code accuracy
        phone numbers and short codes: correct if the exact digits appear in
        the transcript (as digits, or as single spoken digit words).
  Hindi script
        transcripts containing any Devanagari (Hindi) characters.

Writes results/raw/stt_scored_<provider>.csv (per recording, with the
reference and the transcript side by side), results/raw/errors_<provider>.html
(error report: open in a browser), and results/stt_summary.csv (summary table).

Usage (from the repo root):
    python tools/score_stt.py
"""
import csv
import difflib
import html
import re
import statistics
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus.csv"
MANIFEST = ROOT / "data" / "audio" / "manifest.csv"
RAW_DIR = ROOT / "results" / "raw"
SUMMARY = ROOT / "results" / "stt_summary.csv"
BY_SPEAKER = ROOT / "results" / "stt_by_speaker.csv"
AUDIO_DIR = ROOT / "data" / "audio"

UNSCORED = {"CONSENT", "FREE03"}          # no reference text

# ---------- text normalization ----------
CHAR_MAP = str.maketrans({
    "\u064A": "\u06CC", "\u0649": "\u06CC",           # Arabic yeh / alef maksura -> Urdu yeh
    "\u0643": "\u06A9",                               # Arabic kaf -> Urdu kaf
    "\u0647": "\u06C1",                               # Arabic heh -> Urdu heh goal
    "\u06C0": "\u06C1\u0654",                         # heh with hamza (decomposed form)
    "\u200C": "", "\u200D": "", "\u0640": "",         # zero-width joiners, tatweel
    **{chr(0x06F0 + i): str(i) for i in range(10)},  # Urdu digits -> 0-9
    **{chr(0x0660 + i): str(i) for i in range(10)},  # Arabic-Indic digits -> 0-9
})
DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")
NON_WORD = re.compile(r"[^\w\s]|_")
DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").translate(CHAR_MAP)
    s = DIACRITICS.sub("", s).lower()
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)          # 15,000 -> 15000
    s = NON_WORD.sub(" ", s)
    return " ".join(s.split())


def levenshtein(a, b) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    r, h = ref.replace(" ", ""), hyp.replace(" ", "")
    return levenshtein(r, h) / max(len(r), 1)


def wer(ref: str, hyp: str) -> float:
    r, h = ref.split(), hyp.split()
    return levenshtein(r, h) / max(len(r), 1)


# ---------- digits in a transcript ----------
DIGIT_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "صفر": "0", "زیرو": "0", "ایک": "1", "دو": "2", "تین": "3", "چار": "4",
    "پانچ": "5", "چھ": "6", "چھے": "6", "سات": "7", "آٹھ": "8", "نو": "9",
    "ون": "1", "ٹو": "2", "تھری": "3", "فور": "4", "فائیو": "5", "سکس": "6",
    "سیون": "7", "ایٹ": "8", "نائن": "9",
    "تری": "3", "توو": "2", "انے": "1", "سک": "6", "اٹھ": "8",   # spellings seen in Azure output
}
DOUBLE = {"double", "ڈبل"}
PHONE = re.compile(r"^(0\d{10}|92\d{10})$")
CODE = re.compile(r"^\d{4}$")                     # only on rows marked as a code (not 4-digit amounts)


def digits_in(norm_text: str) -> str:
    out, double = [], False
    for tok in norm_text.split():
        d = tok if tok.isdigit() else DIGIT_WORDS.get(tok)
        if tok in DOUBLE:
            double = True
            continue
        if d is not None:
            out.append(d * 2 if double and len(d) == 1 else d)
        double = False
    return "".join(out)


# ---------- error report (HTML) ----------
NUM_RUN = re.compile(r"\d+(?: \d+)+")


def ltr_numbers(text: str) -> str:
    """Keep multi-part numbers (0300 1234567, 7 30) left-to-right inside Urdu text."""
    return NUM_RUN.sub(lambda m: f'<span dir="ltr" style="unicode-bidi:isolate">{m.group(0)}</span>', text)


def word_diff(ref: str, hyp: str):
    """Mark differences between normalized reference and transcript, word by word."""
    r, h = normalize(ref).split(), normalize(hyp).split()
    ref_out, hyp_out = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, r, h, autojunk=False).get_opcodes():
        rs, hs = ltr_numbers(html.escape(" ".join(r[i1:i2]))), ltr_numbers(html.escape(" ".join(h[j1:j2])))
        if op == "equal":
            ref_out.append(rs); hyp_out.append(hs)
        else:
            if rs: ref_out.append(f'<span class="{ "miss" if op == "delete" else "sub" }">{rs}</span>')
            if hs: hyp_out.append(f'<span class="{ "add" if op == "insert" else "sub" }">{hs}</span>')
    return " ".join(ref_out), " ".join(hyp_out)


def write_error_report(provider, scored):
    bad = [r for r in scored if (r["cer"] not in ("", 0, 0.0)) or r["phone_code_ok"] == "no"]
    cats = {}
    for r in bad:
        cats.setdefault(r["category"], []).append(r)
    avg = lambda rows: statistics.mean([r["cer"] for r in rows if r["cer"] != ""] or [0])
    parts = []
    for cat in sorted(cats, key=lambda c: -avg(cats[c])):
        rows = sorted(cats[cat], key=lambda r: -(r["cer"] if r["cer"] != "" else 1))
        trs = []
        for r in rows:
            ref_html, hyp_html = word_diff(r["reference"], r["hypothesis"]) if r["cer"] != "" else (
                html.escape(r["reference"]), html.escape(r["hypothesis"]))
            cer_txt = f'{100 * r["cer"]:.0f}%' if r["cer"] != "" else ""
            phone = {"yes": "✅", "no": "❌"}.get(r["phone_code_ok"], "")
            trs.append(f'<tr><td class="id">{html.escape(r["row_id"])}<br><small>{html.escape(r["speaker_id"])}</small></td>'
                       f'<td class="num">{cer_txt} {phone}</td><td class="u">{ref_html}</td><td class="u">{hyp_html}</td></tr>')
        parts.append(f'<h2>{html.escape(cat)} <small>{len(rows)} with errors, average CER {100 * avg(rows):.0f}%</small></h2>'
                     f'<table><tr><th>Row</th><th>CER</th><th>What was said (corpus)</th><th>What {html.escape(provider)} wrote</th></tr>'
                     + "".join(trs) + "</table>")
    page = f"""<!doctype html><html lang="ur"><head><meta charset="utf-8"><title>STT errors: {html.escape(provider)}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
<style>
body{{font-family:system-ui,sans-serif;margin:24px;color:#1b2433;background:#fbfcfa}}
h1{{font-size:1.4rem}} h2{{font-size:1.1rem;margin-top:2em}} h2 small{{color:#5b6575;font-weight:400}}
table{{border-collapse:collapse;width:100%}} th,td{{border-bottom:1px solid #d6dcd5;padding:6px 10px;vertical-align:top;text-align:left}}
th{{background:#f0f3ef;font-size:.85rem}} td.id,td.num{{white-space:nowrap;font-size:.85rem}}
td.u{{direction:rtl;text-align:right;font-family:"Noto Nastaliq Urdu","Jameel Noori Nastaleeq",serif;font-size:1.15rem;line-height:2.3;width:42%}}
.miss{{background:#f6c9c4}} .add{{background:#cfe3f7}} .sub{{background:#f7e3a8}}
.key span{{padding:0 6px;border-radius:3px}}
</style></head><body>
<h1>STT error report: {html.escape(provider)}</h1>
<p class="key">Compared after normalization (spelling variants, diacritics and punctuation removed).
<span class="miss">missing word</span> <span class="sub">different word</span> <span class="add">extra word</span>
&nbsp; ✅/❌ = phone number or code correct</p>
{"".join(parts) or "<p>No errors.</p>"}
</body></html>"""
    (RAW_DIR / f"errors_{provider}.html").write_text(page, encoding="utf-8")


# ---------- main ----------
def load_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    corpus = {r["id"]: r for r in load_csv(CORPUS)}
    manifest = {r["file"]: r for r in load_csv(MANIFEST)} if MANIFEST.exists() else {}
    files = sorted(RAW_DIR.glob("stt_*.csv"))
    files = [p for p in files if not p.name.startswith("stt_scored_")]
    if not files:
        sys.exit("No transcripts found in results/raw. Run tools/run_stt.py first.")

    summary, by_speaker = [], []
    for path in files:
        provider = path.stem[4:]
        scored = []
        for t in load_csv(path):
            rid = t["row_id"]
            if rid in UNSCORED or t["status"] not in ("Success", "NoMatch"):
                continue
            if not (AUDIO_DIR / t["speaker_id"] / t["file"]).exists():   # stale: audio was deleted or replaced
                continue
            hyp = normalize(t["hypothesis"])
            row = {"file": t["file"], "speaker_id": t["speaker_id"], "condition": t["condition"],
                   "row_id": rid, "category": "", "cer": "", "wer": "", "ref_script": "",
                   "phone_code_ok": "", "hindi_script": "yes" if DEVANAGARI.search(t["hypothesis"]) else "no",
                   "latency_ms": t["latency_ms"], "reference": "", "hypothesis": t["hypothesis"]}
            if rid in corpus:
                c = corpus[rid]
                row["category"] = c["category"]
                options = [(cer(normalize(c[k]), hyp), wer(normalize(c[k]), hyp), name)
                           for k, name in (("text_mixed", "mixed"), ("text_urdu", "urdu"))]
                best = min(options)
                row["cer"], row["wer"], row["ref_script"] = round(best[0], 4), round(best[1], 4), best[2]
                row["reference"] = c["text_mixed" if best[2] == "mixed" else "text_urdu"]
                entity = c["entity"]
                is_code = bool(CODE.match(entity)) and "code" in c["check_words"]
            else:                                         # FREE01 / FREE02: entity from the manifest
                row["category"] = "FREE"
                entity = manifest.get(t["file"], {}).get("entity", "")
                row["reference"] = f"[{entity}]"
                is_code = False
            if PHONE.match(entity or "") or is_code:
                row["phone_code_ok"] = "yes" if entity in digits_in(hyp) else "no"
            scored.append(row)

        with (RAW_DIR / f"stt_scored_{provider}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(scored[0]) if scored else ["file"])
            w.writeheader()
            w.writerows(scored)
        write_error_report(provider, scored)

        def block(name, rows):
            c = [r["cer"] for r in rows if r["cer"] != ""]
            wv = [r["wer"] for r in rows if r["wer"] != ""]
            pc = [r["phone_code_ok"] for r in rows if r["phone_code_ok"]]
            lat = [float(r["latency_ms"]) for r in rows if r["latency_ms"] not in ("", None)]
            return {"provider": provider, "category": name, "n": len(rows),
                    "cer_pct": round(100 * statistics.mean(c), 1) if c else "",
                    "wer_pct": round(100 * statistics.mean(wv), 1) if wv else "",
                    "phone_code_acc_pct": round(100 * pc.count("yes") / len(pc), 1) if pc else "",
                    "phone_code_n": len(pc) or "",
                    "hindi_script": sum(r["hindi_script"] == "yes" for r in rows),
                    "median_latency_ms": round(statistics.median(lat)) if lat else ""}

        cats = sorted({r["category"] for r in scored})
        summary += [block(cat, [r for r in scored if r["category"] == cat]) for cat in cats]
        summary.append(block("ALL", scored))
        for sp in sorted({r["speaker_id"] for r in scored}):
            b = block("ALL", [r for r in scored if r["speaker_id"] == sp])
            by_speaker.append({"speaker": sp, **b})

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    cols = ["provider", "category", "n", "cer_pct", "wer_pct", "phone_code_acc_pct", "phone_code_n", "hindi_script", "median_latency_ms"]
    with SUMMARY.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(summary)

    pw = max([len("provider")] + [len(x["provider"]) for x in summary]) + 2   # column fits the longest name
    head = f"{'provider':<{pw}}{'category':<9}{'n':>5}{'CER%':>8}{'WER%':>8}{'phone/code%':>13}{'hindi':>7}{'latency':>9}"
    print(head)
    print("-" * len(head))
    for s in summary:
        pc = f"{s['phone_code_acc_pct']} ({s['phone_code_n']})" if s["phone_code_n"] else ""
        print(f"{s['provider']:<{pw}}{s['category']:<9}{s['n']:>5}{str(s['cer_pct']):>8}{str(s['wer_pct']):>8}"
              f"{pc:>13}{s['hindi_script']:>7}{str(s['median_latency_ms']):>9}")
    bcols = ["provider", "speaker", "n", "cer_pct", "wer_pct", "phone_code_acc_pct", "phone_code_n", "hindi_script"]
    with BY_SPEAKER.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=bcols, extrasaction="ignore")
        w.writeheader()
        w.writerows(by_speaker)
    print(f"\n{'provider':<{pw}}{'speaker':<9}{'n':>5}{'CER%':>8}{'WER%':>8}{'phone/code%':>13}")
    print("-" * (pw + 43))
    for b in by_speaker:
        pc = f"{b['phone_code_acc_pct']} ({b['phone_code_n']})" if b["phone_code_n"] else ""
        print(f"{b['provider']:<{pw}}{b['speaker']:<9}{b['n']:>5}{str(b['cer_pct']):>8}{str(b['wer_pct']):>8}{pc:>13}")

    print(f"\nsummary: {SUMMARY.relative_to(ROOT)}   by speaker: {BY_SPEAKER.relative_to(ROOT)}   details: results/raw/stt_scored_<provider>.csv")
    print("error report: results/raw/errors_<provider>.html (open in a browser)")
    print("Lower CER/WER is better. Phone/code % = exact digits correct.")


if __name__ == "__main__":
    main()
