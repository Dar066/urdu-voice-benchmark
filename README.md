# Urdu Voice Benchmark

**How well do speech engines understand and speak Pakistani Urdu, as people actually use it?**

Pakistani Urdu on the phone is not textbook Urdu. It mixes in English words ("appointment confirm ہو گئی ہے"), uses Arabic and Persian phrases (جزاک اللہ، خدا حافظ), and is full of phone numbers, prices and times. This benchmark tests speech-to-text (STT) and text-to-speech (TTS) engines on exactly that kind of speech, recorded on ordinary phones on speakerphone.

It started when a Pakistani clinic's Urdu voice agent kept failing: Hindi-sounding pronunciation, mispronounced English and Arabic words, and wrong phone numbers. Instead of guessing which engine was better, this lab measures it.

---

## Key findings

### Speech-to-text (6 speakers, 547 recordings per engine)

| | Azure (`ur-IN`) | Whisper large-v3 | Whisper turbo |
|---|---|---|---|
| Character error rate | 17.9% | **14.9%** | 16.4% |
| Phone numbers fully correct | 57% | **62%** | **62%** |
| Runs where | Microsoft cloud | Laptop, free | Laptop, free |

- **A free, open-source engine (Whisper large-v3) is the most accurate overall,** for 5 of 6 speakers.
- **Azure is best at casual conversation and English–Urdu mixing.**
- **No engine reads Pakistani phone numbers reliably:** about 4 in 10 come out wrong (dropped digits, swapped groups, misheard number words).
- **Azure has no Pakistani Urdu speech-to-text model.** Its Indian Urdu model shows it: ₹ signs and times like "7.5 بجے".

### Text-to-speech (4 Azure voices, 8 listeners, 192 blind ratings)

| Voice | Naturalness (1–5) | Heard as Pakistani | Wrong word heard |
|---|---|---|---|
| Asad (PK male) | **3.50** | 79% | 19% |
| Salman (IN male) | 3.33 | **83%** | **17%** |
| Uzma (PK female) | 3.17 | 69% | 27% |
| Gul (IN female) | 3.12 | 79% | **17%** |

- **Male voices sound more natural than female voices.**
- **Listeners cannot tell Azure's Pakistani and Indian Urdu voices apart.** Only 3% of ratings heard an Indian accent, mostly on the *Pakistani* voices.
- **The problems are specific words,** such as یا, جزاک اللہ, پلاٹ.
- **Spelling controls pronunciation:** write English loanwords in Urdu script with Pakistani spelling (**اپوائنٹمنٹ**, not اپائنٹمنٹ), and write times as words (**ساڑھے سات بجے**, not "7:30 بجے").

Full results, method and limitations:
- [STT results](docs/stt-results.md)
- [TTS results](docs/tts-results.md)

---

## What's inside

```
data/corpus.csv                 238 test sentences in daily-use Pakistani Urdu, 10 categories
docs/                           recording guide and full results reports
tools/recorder.html             phone-friendly recording page (secret link per speaker)
tools/download_recordings.py    download recordings from Supabase
tools/run_stt.py                run STT engines: Azure, ElevenLabs, local Whisper
tools/score_stt.py              score transcripts: CER, WER, phone-number accuracy, error report
tools/run_tts.py                generate corpus sentences with TTS voices
tools/check_tts.py              automatic TTS check (transcribe the voices back with Whisper)
tools/prepare_listening.py      build a blind listening test
tools/listen/index.html         Urdu listening-test page
tools/score_listening.py        listening-test results
supabase/                       database setup and the two server functions (uploads, ratings)
```

### The corpus

| Category | Tests |
|---|---|
| GRT | Arabic/Persian greetings and courtesy |
| PUR | Urdu words that have Hindi equivalents |
| PHN | Urdu sounds (ق خ غ ز ف ع) |
| ENG | Everyday English words in Urdu |
| MIX | Natural English–Urdu code-switching |
| NUM | Phone numbers, prices, times, dates |
| CON | Plain daily caller speech |
| DOM | Phone-agent lines |
| BIZ | Business and customer service |
| OFC | Office and official speech |

Every sentence comes in two versions: English words in English letters, and English words in Urdu script.

---

## Run it yourself

You need Python 3, ffmpeg, a free Supabase project, a Vercel (or any static) host, and keys for the engines you want to test.

1. **Configure.** Copy `.env.example` to `.env` and fill in your keys. Replace `YOUR_PROJECT_REF` and `YOUR-SITE` in `tools/recorder.html`, `tools/listen/index.html`, `supabase/functions/*/index.ts` and `supabase/*.sql` with your Supabase project and website address.
2. **Set up Supabase.** Run `supabase/setup.sql` in the SQL editor, and deploy `supabase/functions/recorder` (JWT verification off: the secret link code is the check).
3. **Record.** Host the repo, send each speaker their link from the links query in `setup.sql`. Follow `docs/recording-guide.md`.
4. **Transcribe and score:**
   ```
   python tools/download_recordings.py
   python tools/run_stt.py --provider azure
   python tools/run_stt.py --provider whisper_large
   python tools/score_stt.py
   ```
   Local Whisper needs a whisper.cpp model in `models/` (for example `ggml-large-v3-q5_0.bin`).
5. **TTS:** `python tools/run_tts.py --voice azure_asad`, then `python tools/check_tts.py`. For a listening test, run `supabase/listening.sql`, deploy `supabase/functions/listen`, and `python tools/prepare_listening.py`.

---

## Privacy

- **No recordings are in this repository.** Speakers were promised their voices would never be made public. They stay in private storage.
- Listener ratings are anonymous (listener codes only) and are not included.
- Run your own recordings under your own consent terms. The consent text used here is in `docs/recording-guide.md`.

---

## License

- **Code:** [MIT](LICENSE.md)
- **Corpus, documentation and results:** [CC BY 4.0](LICENSE-DATA.md)

**Free for everyone, including commercial use.** Please give credit: "Urdu Voice Benchmark by Adnan (github.com/Dar066)".

---

## Pakistani Urdu speech model

A speech-to-text model fine-tuned for Pakistani Urdu is in development, measured against this benchmark. It will be available through a paid API.

For early access, custom testing on your own callers, or Urdu voice agents for your business, contact **dar9435@gmail.com**.

---

## Credit

Created by Adnan ([@Dar066](https://github.com/Dar066)), Lahore, Pakistan.

If you use this benchmark, please cite it:

> Adnan. *Urdu Voice Benchmark: Pakistani Urdu speech-to-text and text-to-speech evaluation.* 2026. https://github.com/Dar066/urdu-voice-benchmark
