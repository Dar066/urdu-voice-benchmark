# Text-to-Speech Results: Pakistani Urdu

**Urdu Voice Lab, Phase 1 (TTS)**, October 2026
Voices tested: Azure Uzma and Asad (`ur-PK`), Azure Gul and Salman (`ur-IN`)
Data: 1,292 generated clips, 192 blind ratings from 8 Pakistani listeners

---

## 1. Summary

Four Azure Urdu voices were tested in two ways: an automatic check (can a speech recognizer understand every clip?) and a blind listening test (how do Pakistani listeners judge naturalness, accent, and pronunciation?).

**Key findings**

1. **Male voices sound more natural than female voices.** Asad (3.50 / 5) and Salman (3.33) are rated above Uzma (3.17) and Gul (3.12). This held at every stage of the test, from 3 listeners to 8.
2. **Uzma, the Pakistani female voice, is the weakest voice:** the fewest "Pakistani accent" answers, the most "Indian" and "unsure" answers, and a wrong word in more than 1 in 4 clips.
3. **Listeners cannot tell Azure's Pakistani and Indian Urdu voices apart.** Only 6 of 192 ratings (3%) heard an Indian accent, and **5 of those 6 went to the Pakistani voices** (Uzma 3, Asad 2). The `ur-PK` label does not make a voice sound more Pakistani.
4. **The real problem is specific words, not the voice as a whole.** About 1 in 5 clips contains a word listeners hear as wrong, and the same words come up again and again (Section 5).
5. **Spelling controls pronunciation.** Every voice is clearer when English loanwords are written in Urdu script, and a loanword's Urdu spelling decides its vowels: اپائنٹمنٹ is read "apaa-intment", while اپوائنٹمنٹ gives the Pakistani "apwaintment".
6. **Times written as digits are read wrongly by every voice:** "7:30 بجے" becomes "سات بج کر تیس منٹ بجے". Phone numbers written as digits are read correctly.

---

## 2. Listening test results

8 listeners, 24 clips each, 192 ratings in total (48 per voice). Listeners did not know which voice they were hearing.

| Voice | Type | Naturalness (1–5) | Pakistani | Indian | Unsure | Wrong word |
|---|---|---|---|---|---|---|
| **Asad** | PK male | **3.50** ±0.27 | 79.2% | 4.2% | 16.7% | 18.8% |
| **Salman** | IN male | 3.33 ±0.22 | **83.3%** | 2.1% | **14.6%** | **16.7%** |
| Uzma | PK female | 3.17 ±0.28 | 68.8% | 6.2% | 25.0% | 27.1% |
| Gul | IN female | 3.12 ±0.25 | 79.2% | 0.0% | 20.8% | 16.7% |
| **All voices** | | | **77.6%** | **3.1%** | **19.3%** | **19.8%** |

Naturalness scale: 1 = very machine-like, 5 = fully natural. ± = 95% margin of error. The margins still overlap slightly, so the ranking is a consistent trend rather than a proven gap.

**Male vs female:** the two male voices average 3.42, the two female voices 3.15.

**Listeners differ.** Five listeners heard almost every clip as Pakistani. Two listeners (L05, L06) were "unsure" in 10 and 20 of their 24 clips. Two listeners (L02, L04) gave the only "Indian" answers, 3 each. Nobody rated every clip identically: each listener used 2–4 different naturalness scores.

---

## 3. Listener comments

Free-text comments at the end of the test, plus comments given directly to the researcher:

| Listener | Comment |
|---|---|
| L16 | "All is well" |
| L06 | "Appointment word was not correctly said" |
| L02 | "80% ok". Also reported that "یا" was heard as "naa", and that the last words of sentences were clipped or very faint |
| (verbal) | "The male voice is much better" |
| (verbal) | "The female voice sounds like an English woman speaking Urdu" |

The last comment suggests that what listeners notice in the female voices is a **foreign** quality rather than an **Indian** accent. The accent question offered only Pakistani / Indian / not sure, so this kind of answer had no matching option. This likely explains part of the high "unsure" share.

---

## 4. Automatic check

Every generated clip was transcribed by Whisper large-v3 (the most accurate engine in the STT benchmark) and compared with the sentence the voice was given. A clip Whisper cannot understand points to unclear pronunciation. This is a relative check between voices: Whisper makes mistakes, but the same kind for every voice.

### Urdu script vs English letters

The same 125 sentences containing English words, generated twice per voice: once with English words in Urdu script (اپوائنٹمنٹ، پیمنٹ) and once in English letters (appointment, payment).

| Voice | Urdu script CER | English letters CER |
|---|---|---|
| Asad | **5.5%** | 9.5% |
| Uzma | **5.8%** | 9.7% |
| Salman | **5.8%** | 10.2% |
| Gul | **7.3%** | 11.5% |

**Every voice is clearer with Urdu script,** by about 4 points.

### By category (Urdu-script input)

| Voice | BIZ | DOM | ENG | GRT | NUM | OFC | PHN | PUR | **All** |
|---|---|---|---|---|---|---|---|---|---|
| Uzma | 2.5 | 5.8 | 2.4 | 3.0 | 26.5 | 1.7 | 2.7 | 1.8 | **6.0** |
| Salman | 2.9 | 5.0 | 3.4 | 2.8 | 26.9 | 2.8 | 1.3 | 1.4 | **6.1** |
| Asad | 2.2 | 6.7 | 2.4 | 3.0 | 28.1 | 2.0 | 2.1 | 2.9 | **6.3** |
| Gul | 3.9 | 8.1 | 3.8 | 4.8 | 31.1 | 2.7 | 5.0 | 2.9 | **7.9** |

Character error rate (%). No clip contained Hindi (Devanagari) script.

**About the NUM column:** the high values come mostly from format. The voices read "12,500 روپے" correctly as "بارہ ہزار پانچ سو روپے", but Whisper then writes some numbers as digits, which counts as a difference. Of the 34 clips flagged as unclear, most were this kind of format difference. Listening confirmed that **all four voices read phone numbers correctly**; apparent extra digits were Whisper's mistakes.

---

## 5. Word-level problems

Found by the researcher's pilot session, confirmed or added by listeners, and by the automatic check.

| # | Word or text | What the voice says | Should be | Reported by | Cause |
|---|---|---|---|---|---|
| 1 | یا (or) | "aa" / "naa" | "yaa" | Researcher + L02 | Voice. **Changes meaning:** "کارڈ یا بینک ٹرانسفر" becomes unclear |
| 2 | جزاک اللہ | "jazak-ullah" | "jazak Allah" | Researcher | Voice (Arabic phrase) |
| 3 | ت / ٹ | mixed up | kept distinct | Researcher | Voice (Urdu sounds) |
| 4 | پلاٹ (plot) | "pee-laat" | "plaat" | Researcher | Voice (extra vowel in English loanword) |
| 5 | اپائنٹمنٹ (appointment) | "apaa-intment" | "apwaintment" | Researcher + L06 | **Spelling.** Correct spelling: **اپوائنٹمنٹ** |
| 6 | Sentence endings | last words faint or clipped | clear to the end | L02 | Voice (not yet measured) |
| 7 | "7:30 بجے" | "سات بج کر تیس منٹ بجے" | "ساڑھے سات بجے" | Automatic check, all 4 voices | **Text format** |
| 8 | "HAPS-4721" | "ہیپس سنتالیس اکیس" (47-21) | four separate digits | Automatic check | **Text format** |

Problems 5, 7 and 8 come from **how the text is written**, and can be fixed for free by changing what the agent writes. Problems 1–4 and 6 come from the **voice**, and need pronunciation rules or a different voice.

---

## 6. Method

**Voices.** Azure neural TTS, REST API, free tier (F0), region Central India, output MP3 24 kHz mono. `ur-PK-UzmaNeural`, `ur-PK-AsadNeural`, `ur-IN-GulNeural`, `ur-IN-SalmanNeural`.

**Generated clips.** The 198 agent-side corpus sentences (all categories except caller-only CON and MIX). Each sentence in its Urdu-script version, and the 125 sentences containing English words also in their English-letters version: 323 clips per voice, 1,292 in total.

**Automatic check.** Each clip converted to 16 kHz mono WAV and transcribed with Whisper large-v3 (whisper.cpp, `q5_0`, language `ur`). Scored with the same normalization and character error rate as the STT benchmark, against the better-matching script version of the sentence.

**Listening test.**
- **Sentences:** 24, chosen across greetings, pure Urdu, Urdu sounds, English words, numbers in words, business, office, and phone-agent lines, from several business types. Only sentences without gender-specific verb forms, so female voices were not penalized for masculine grammar. Urdu-script versions only.
- **Clips:** 24 sentences × 4 voices = 96. Each clip padded with 0.6 s of silence so no player could cut the last word, and given a random file name so the name never revealed the voice. The key linking clips to voices was kept private and never published.
- **Design:** each listener heard all 24 sentences once, in a random order, with the voice rotating by listener, so every listener heard each voice exactly 6 times.
- **Questions** (Urdu, one tap each): naturalness (5 levels), accent (Pakistani / Indian / not sure), any wrong word (yes / no). Questions unlocked only after the clip had played completely once.
- **Listeners:** 8 Pakistani listeners, each with a personal link. Ratings stored anonymously by listener code. The researcher's own pilot session (L01) was kept on record but excluded from all results.

---

## 7. Limitations

- **8 listeners.** Enough for the main trends, which stayed stable from 3 to 8 listeners. Small differences between voices are not statistically certain.
- **Listener background not recorded** (age, gender, city). The listener group may not represent all Pakistani callers.
- **The accent question had no "foreign" option.** Listener comments show some heard a foreign rather than Indian accent; their answers went to "not sure".
- **Only Azure voices.** Other providers (ElevenLabs, Uplift and others) are planned for round 2.
- **Corpus spelling.** The corpus used اپائنٹمنٹ, so the "appointment" problem was partly caused by the test text itself. It is reported as a finding about spelling.
- **The automatic check is relative.** Whisper's own errors affect all voices similarly, but its numbers are not absolute measures of pronunciation quality.
- **Sentence-ending loudness** was reported by one listener but not yet measured.

---

## 8. Recommendations for the HAPS voice agent

1. **Use a male voice: Asad.** He has the best naturalness and fits the `ur-PK` setting. Salman is an equally good fallback. Avoid Uzma.
2. **Write English loanwords in Urdu script, with Pakistani spelling.** Above all **اپوائنٹمنٹ** (not اپائنٹمنٹ), and likewise پیمنٹ، کنفرم، بکنگ.
3. **Write times as Urdu words:** "ساڑھے سات بجے", "سوا پانچ بجے", "پونے سات بجے". Never "7:30 بجے".
4. **Write IDs and codes as separate digit words:** "چار سات دو ایک", not "4721".
5. **Add custom pronunciation rules** (Azure SSML) for the voice-level problems: یا، جزاک اللہ، پلاٹ, and test that they sound right before going live.
6. **Check sentence endings on a real phone call.** If the last word fades, end key sentences with a short closing word or confirmation question, so important information is never in the faintest position.

Recommendations 2–4 cost nothing: they only change the instructions given to the agent's AI.

---

## 9. Next steps (round 2)

- **Bilingual labels** (Urdu + English) on all questions and buttons.
- **A fourth accent option:** غیر ملکی / انگریز جیسا · Foreign / English-like.
- **Reference clips:** a clearly Pakistani and a clearly foreign-accented sample, to check that listeners can hear a difference.
- **More voices:** ElevenLabs v3, Uplift, and others.
- **Azure with corrected pronunciations,** to measure whether the fixes in Section 8 work.
- **A loanword spelling test:** common English words in two Urdu spellings each, rated by listeners, to build a Pakistani loanword spelling guide for Urdu TTS.
- **Measure sentence-ending loudness** for every voice.
