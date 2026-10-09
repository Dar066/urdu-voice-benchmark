# Speech-to-Text Results: Pakistani Urdu

**Urdu Voice Lab, Phase 1 (STT)**, October 2026
Engines tested: Azure Speech, Whisper large-v3, Whisper large-v3-turbo
Data: 6 speakers, 547 scored recordings per engine

---

## 1. Summary

Three speech-to-text engines were tested on real Pakistani Urdu as it is spoken day to day: mixed with English, full of Arabic and Persian words, and recorded on ordinary phones on speakerphone.

**Key findings**

1. **A free, open-source engine beats Azure overall.** Whisper large-v3, running locally on a laptop, has the lowest error rate (14.9% CER vs 17.9% for Azure), and it has the lowest or near-lowest error rate **for every one of the 6 speakers**.
2. **Azure is best at natural conversation.** It leads on casual daily speech, English–Urdu code-switching, and greetings, which are the kinds of speech real callers use most.
3. **No engine reads Pakistani phone numbers reliably.** The best engines get only about **6 in 10** phone numbers fully correct. Digits are dropped, groups are swapped, and number words are misheard.
4. **Azure has no Pakistani Urdu speech-to-text model.** Its only Urdu model is Indian Urdu (`ur-IN`). This shows in its output: Indian rupee signs (₹) and decimal times such as "7.5 بجے".
5. **Speakers vary more than engines.** Within a single engine, error rates range by about 8 points from the easiest to the hardest speaker.
6. **Each engine has its own failure modes,** some of them dangerous for a voice agent (Section 6).

---

## 2. Overall results

| | Azure | Whisper turbo | Whisper large |
|---|---|---|---|
| **Character error rate (CER)** | 17.9% | 16.4% | **14.9%** |
| **Word error rate (WER)** | 24.6% | 25.7% | **22.8%** |
| **Phone numbers and codes fully correct** | 56.6% (30/53) | **62.3% (33/53)** | **62.3% (33/53)** |
| Hindi (Devanagari) script in output | 0 | 0 | 0 |
| Where it runs | Microsoft cloud | Laptop processor | Laptop processor |
| Time per recording (median) | ~1.8 s | ~6 s | ~8.5 s |

Lower error rates are better. Timing is **not** a fair speed comparison: Azure was called over a home internet connection, and Whisper ran on a laptop processor without a graphics card. On a server with a graphics card, Whisper would be many times faster.

---

## 3. Results by category

Character error rate per corpus category. **Bold** = best in that row.

| Category | What it tests | n | Azure | Whisper turbo | Whisper large |
|---|---|---|---|---|---|
| CON | Plain daily caller speech | 39 | **3.0%** | 7.2% | 4.1% |
| MIX | Pakistani English–Urdu code-switching | 39 | **7.4%** | 8.2% | 9.1% |
| GRT | Arabic/Persian greetings and courtesy | 39 | **6.7%** | 10.5% | 8.3% |
| OFC | Office and official speech | 63 | **7.2%** | 7.8% | 7.7% |
| PUR | Urdu words that have Hindi equivalents | 43 | 6.9% | 9.2% | **6.5%** |
| PHN | Urdu sounds (ق خ غ ز ف ع) | 39 | 5.2% | 4.8% | **2.3%** |
| BIZ | Business and customer service | 67 | 11.1% | 8.1% | **6.4%** |
| ENG | Everyday English words in Urdu | 45 | 11.2% | 12.3% | **10.8%** |
| NUM | Numbers, amounts, times, dates | 162 | 41.5% | 34.8% | **33.3%** |

**About the NUM row:** these error rates are inflated by format. When a speaker says "صفر تین سو" and an engine writes "0300", the number is correct but many characters differ. For numbers, the **phone/code accuracy** in Section 2 is the meaningful measure.

---

## 4. Results by speaker

Character error rate per speaker (phone/code accuracy in brackets, out of 9; 8 for S06).

| Speaker | Reading set | Azure | Whisper turbo | Whisper large |
|---|---|---|---|---|
| S07 | A | 17.1% (6/9) | 12.9% (8/9) | **11.0%** (6/9) |
| S05 | B | 16.7% (4/9) | 14.9% (4/9) | **12.3%** (4/9) |
| S08 | B | 15.6% (4/9) | 15.2% (5/9) | **14.6%** (6/9) |
| S03 | C | 18.1% (5/9) | **16.3%** (5/9) | 16.4% (7/9) |
| S09 | C | 19.2% (7/9) | 19.9% (7/9) | **16.4%** (7/9) |
| S06 | C | 20.8% (4/8) | 19.9% (4/8) | **19.4%** (3/8) |

Whisper large has the lowest error rate for 5 of 6 speakers, and is within 0.1 points of the best for the sixth (S03). On the hardest speaker (S06), all three engines perform about equally.

---

## 5. Phone numbers

Phone numbers are the most important single piece of information in a booking call, and the weakest area for every engine.

| Error type | Example (said → written) | Engine |
|---|---|---|
| Digit dropped or merged | صفر تین **صفر صفر**… → 0301-234567 | Whisper large |
| **Groups swapped** | 0345 6789012 → **6789012 0345** | Whisper large, Whisper turbo |
| Digits lost in "+92" format | plus nine two, three zero zero… → digits missing | Azure |
| "Double" not applied | …ڈبل فائیو… → a single 5 | Azure |
| Sound-alike word | **صفر** (zero) → **سفر** (journey) | Whisper large |
| Number word misheard | نواسی (89) → نمازی (worshipper) | Whisper large |

Swapped groups are the most dangerous: every digit is correct, but the number is wrong, and nothing in the transcript looks suspicious.

---

## 6. Failure modes by engine

**Azure (Indian Urdu model, `ur-IN`)**
- **Indian rupee sign (₹)** instead of روپے, in 10 of the first 184 transcripts.
- **Urdu time words written as decimals:** ساڑھے سات → "7.5 بجے", سوا پانچ → "5.25 بجے". An agent can easily misread these.
- **Homograph confusion:** بہتر (better) → "72" (بہتر also means seventy-two).
- **Clinic words misheard:** فیس → "فی", stress test → "شریس / ڈریس ٹیس", مریض → "بریج".
- **Arabic/Persian phrases:** معذرت → "مادھو" (an Indian name), خدا نخواستہ → "خدا نے خاصا".

**Whisper (turbo and large)**
- **"موسیقی" (music) on silent audio.** Whisper invents this word when a recording contains no speech.
- **Language drift:** one Urdu sentence was transcribed as Icelandic ("able haft ekkert vaktir").
- **Repetition:** a sentence written twice in one transcript.
- **Formalizing casual speech:** "تھینک یو سو مچ، آپ نے بہت ہیلپ کی" → "آپ نے بہت سارا مدد کیا". Pakistani-style English mixing is lost.
- **Spelling variants of English loanwords** (پراپرلی → پاپلی, ٹینشن → ٹینچن). These count as errors but usually keep the meaning.
- **Getting stuck:** on one recording, the model looped until stopped (handled in the runner with a 3-minute limit).

---

## 7. Method

**Corpus.** 238 sentences in daily-use Pakistani Urdu, in 10 categories designed around observed failures of an Azure-based Urdu voice agent: English mixing, Hindi-leaning accent and vocabulary, numbers, Arabic/Persian words, and general recognition. Each sentence exists in two scripts: English words in English letters (`text_mixed`) and English words in Urdu script (`text_urdu`).

**Speakers and recording.** 6 adult speakers (S03, S05, S06, S07, S08, S09). Each read one of three balanced reading sets (A: S07; B: S05, S08; C: S03, S06, S09), plus all 27 number sentences and 3 free-speech items. Recordings were made with each speaker's phone on a table at about arm's length (speakerphone condition), using a web recorder with per-speaker secret links.

**Scored items.** 547 per engine. Not scored: consent recordings, and the free-speech item FREE03 (no reference text). For FREE01 and FREE02 (made-up phone number, date and time), only phone accuracy is scored.

**Engines.**
- **Azure Speech**, REST API for short audio, free tier, language `ur-IN`. Azure offers no `ur-PK` speech-to-text model.
- **Whisper large-v3** and **Whisper large-v3-turbo** (OpenAI, open source), as quantized whisper.cpp models (`q5_0`) through ffmpeg's built-in whisper filter, language `ur`, on an Intel Core i5-1145G7 laptop processor.

All audio was converted to 16 kHz mono WAV before transcription.

**Scoring.**
- **Normalization** before comparison: Arabic and Urdu letter variants unified (ي/ی, ك/ک, ه/ہ), diacritics, punctuation and zero-width characters removed, Urdu and Arabic digits converted to 0–9, thousands separators removed.
- **CER** (character error rate, spaces ignored, because Urdu word spacing is inconsistent) and **WER** (word error rate).
- **Script-agnostic:** each transcript is scored against both script versions of the sentence, and the better match is used, so writing "appointment" as اپائنٹمنٹ is not counted as an error.
- **Phone/code accuracy:** correct only if the exact digit sequence appears in the transcript, as digits or as single spoken digit words (including the English-digit spellings engines produce in Urdu script).
- **Hindi script:** any Devanagari character in a transcript is flagged.

---

## 8. Data quality and exclusions

| Issue | Action |
|---|---|
| 3 silent takes (S07 BIZ16, S07 NUM04, S09 GRT03), found because Azure returned nothing and Whisper wrote "موسیقی" | Re-recorded by the same speakers |
| S03's first session: 42 empty takes (button tapped twice) | S03's session discarded and fully re-recorded |
| S06 FREE01: silent take | Excluded (1 of 547 items) |
| S08 FREE03: not recorded | No effect (FREE03 is not scored) |

After these issues, the recorder was improved: takes shorter than 1 second or without detectable voice cannot be saved, accidental double-taps are ignored, and all speaker-facing buttons and hints are in Urdu.

---

## 9. Limitations

- **6 speakers.** The overall ranking has stayed the same since the first 2 speakers, but small differences (for example 1–3 phone numbers) are not meaningful.
- **Unbalanced reading sets:** set A has 1 speaker, set B 2, set C 3.
- **Speakerphone only.** The planned close-microphone comparison has not been recorded yet.
- **CER counts harmless differences as errors:** loanword spelling variants and digits-vs-words formatting. A meaning-level score is planned.
- **Grouped Urdu numbers** (e.g. "تین سو بارہ" = 312) are not converted by the phone scorer, so a correct grouped transcription can be marked wrong. In the cases checked, the failures were real errors.
- **Timing is not comparable** across engines (cloud over home internet vs laptop processor).

---

## 10. Recommendations for the HAPS voice agent

1. **Never rely on speech recognition for phone numbers.** Ask callers to type the number on the keypad, or read it back in groups and ask for confirmation. This applies whichever engine is used.
2. **Engine choice for live calls:**
   - **Short term: keep Azure.** It is fast, it is best at casual speech and code-switching, and it never produced Hindi script.
   - **Clean Azure's output before the AI reads it:** ₹ → روپے, decimal times → clock times (7.5 → 7:30, 5.25 → 5:15).
   - **Test Azure's phrase-list feature** with clinic terms (فیس، اسٹریس ٹیسٹ، ای سی جی، ایکو) to reduce the misheard clinic words.
3. **Medium term: evaluate Whisper on a server with a graphics card.** Whisper large is the most accurate engine overall but too slow on a laptop for live calls. A fine-tuned Whisper turbo (Phase 3) is the most practical path to a fast, accurate Pakistani Urdu engine.
4. **If Whisper is used live:** filter silence before transcription (to avoid "موسیقی"), and watch for repetition and language drift.
5. **Instruct the agent's AI to accept spelling variants** of English loanwords in Urdu script, since they usually keep the meaning.

---

## 11. Next steps

- **TTS track:** generate the corpus with Azure (Uzma, Asad), ElevenLabs v3 and other Urdu voices, and run a blind listening test with Pakistani listeners.
- **Scorer v2:** a meaning-level judge (harmless spelling vs meaning changed), format-neutral number scoring, and a timeout count.
- **More speakers,** especially for reading set A, and the close-microphone condition.
- **Optional extra STT engines:** ElevenLabs Scribe (plug-in ready), Google, Groq.
