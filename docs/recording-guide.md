# Speaker Recording Guide

This guide explains how to collect the real speech recordings used to test STT (speech-to-text) providers. Every recording maps to a row in `data/corpus.csv`, so the scripts can score each provider automatically.

---

## 1. Speakers

Record **12 speakers**:

| | 18–30 | 31–50 | 51+ |
|---|---|---|---|
| Male | 2 | 2 | 2 |
| Female | 2 | 2 | 2 |

- **Accents:** about 8 speakers with a Lahori/Punjabi accent (the main caller base), plus 4 from other backgrounds (e.g. Karachi, Pashto-influenced, Saraiki, Potohari). This shows whether a provider works only for one accent.
- **Include older speakers.** People aged 51+ are a large share of clinic callers and are often where STT fails first.
- Speakers should talk the way they normally do on the phone, not like newsreaders.

---

## 2. What each speaker reads

Only rows with `use` = `stt` or `both` are recorded. The 20 `DOM` rows are TTS-only and are skipped.

Each speaker reads three parts:

1. **All 27 `NUM` rows.** Digit recognition is the key failure, so every speaker records them.
2. **One reading set (A, B, or C)** from the remaining rows.
3. **3 free-speech items** (see section 4).

**Reading set rule:** within each category, take the row number from the ID (e.g. `PUR07` → 7):

| Set | Rows | Count |
|---|---|---|
| A | number 1, 4, 7, 10… | 67 |
| B | number 2, 5, 8, 11… | 65 |
| C | number 3, 6, 9, 12… | 59 |

**Speaker assignment** (each set gets a balanced mix of men, women, and ages):

| Set | Speakers |
|---|---|
| A | S01, S04, S07, S10 |
| B | S02, S05, S08, S11 |
| C | S03, S06, S09, S12 |

Assign speaker IDs so each set has 2 men and 2 women across different ages.

**Per speaker:** about 95 items, roughly 25–30 minutes including re-takes.

Speakers read the **`text_mixed`** column. English words appear in English letters there, which is easier to read naturally.

---

## 3. Recording setup

The goal is to sound like a real caller, not a studio.

- **Main condition: speakerphone (`spk`).** Place the phone flat on a table about **50 cm** (arm's length) from the speaker, in a normal room. A normal background is fine (distant traffic, a ceiling fan). Avoid a TV or a loud generator right next to the phone.
- **Clean baseline (`cln`).** Two speakers (one man, one woman) also record their full items again with the phone held close, about 10–15 cm from the mouth, in a quiet room. This separates "the provider can't understand Urdu" from "the provider can't handle speakerphone audio."
- **Device:** the speaker's own phone. Mixing devices is realistic. Note the phone model in `speakers.csv`.
- **Method:** the lab's recording page (the next build step) shows one sentence at a time and saves each file with the correct name automatically. If recording manually with a voice recorder app, make **one file per sentence** and name it as in section 5.
- **Format:** any common format (m4a, mp3, wav) is fine. The scripts convert everything to a standard format, and the phone-line effect (8 kHz) is added later in software.

---

## 4. Free-speech items

Scripted reading never fully matches real calls, so each speaker records 3 unscripted items:

| ID | Instruction to speaker | Ground truth |
|---|---|---|
| `FREE01` | Read out the phone number on your card **in your own normal way** | number on the card |
| `FREE02` | Say the date and time on your card as if booking an appointment | date and time on the card |
| `FREE03` | Describe a problem as if calling a company's helpline (any topic, 15–30 seconds) | transcribed by hand afterwards |

**Use made-up numbers only.** Give each speaker a card with a fictional mobile number (format `03XX-XXXXXXX`) and a date/time. Never record anyone's real phone number or CNIC.

---

## 5. File naming

```
S{speaker}_{row_id}_{condition}.{ext}
```

| Part | Values | Example |
|---|---|---|
| speaker | `S01`–`S12` | `S03` |
| row_id | corpus ID or `FREE01`–`FREE03` | `NUM26` |
| condition | `spk` (speakerphone) or `cln` (close mic) | `spk` |

Examples:
```
S03_NUM26_spk.m4a
S07_PUR10_spk.wav
S01_FREE03_cln.m4a
```

**Folder layout** (audio stays on your computer; `.gitignore` keeps it out of GitHub):
```
data/audio/S01/S01_GRT01_spk.m4a
data/audio/S01/S01_NUM01_spk.m4a
...
```

---

## 6. Instructions to read to each speaker

> - Read each sentence once, naturally, at your normal speaking speed, as if you are talking on a phone call.
> - Don't over-pronounce or try to sound formal.
> - Say English words the way you normally say them in daily conversation.
> - Read numbers the way the sentence says them. In the free items, say them your own way.
> - If you make a mistake, stop and record that sentence again. Don't continue in the same file.
> - Leave about one second of silence before and after each sentence.

---

## 7. Speaker information (`data/speakers.csv`)

Record details without names:

```
speaker_id,gender,age_band,region,mother_tongue,phone_model,reading_set,cln_recorded,consent_date
S01,M,18-30,Lahore,Punjabi,Samsung A15,A,no,2026-10-05
```

Keep real names (if needed at all) in a separate file **outside the repo**, never in `speakers.csv`.

---

## 8. Consent

Read this to each speaker, or give it to them, before recording. Record their agreement (a verbal "yes" at the start of their first file is enough) and the date in `speakers.csv`.

**اردو:**

> یہ recordings صرف اس بات کو test کرنے کے لیے ہیں کہ مختلف voice systems اردو کو کتنا اچھی طرح سمجھتے ہیں۔ آپ کا نام کسی recording کے ساتھ نہیں لکھا جائے گا۔ آپ کی recordings (آواز) کسی بھی social media جیسے WhatsApp، YouTube، Instagram، Facebook وغیرہ پر، یا کسی بھی public website پر شیئر یا پوسٹ نہیں کی جائیں گی۔ یہ ایک محفوظ اور private storage میں رکھی جائیں گی، اور صرف testing کے لیے speech technology systems سے چیک کی جائیں گی۔ آپ جب چاہیں منع کر سکتے ہیں، اور آپ کی recordings delete کر دی جائیں گی۔ کیا آپ اس کی اجازت دیتے ہیں؟

**English:**

> These recordings are only used to test how well different voice systems understand Urdu. Your name will not be attached to any recording. Your recordings (voice) will not be shared or posted on any social media platform (such as WhatsApp, YouTube, Instagram, Facebook) or on any public website. They are kept in secure, private storage and are processed only by speech technology systems for testing. You can withdraw at any time, and your recordings will be deleted. Do you agree?

If you ever want to publish any recordings (e.g. when the repo goes public), ask the speakers for separate, explicit permission first.

---

## 9. Quality check after each speaker

- [ ] Listen to the first 3 files: voice clear, not distorted, not too quiet.
- [ ] File count matches: 27 NUM + set rows + 3 FREE (+ the same again for `cln` speakers).
- [ ] Every file name follows section 5. A wrong name means a missing result.
- [ ] Note any sentence where the speaker said something different from the text. That row's ground truth must be corrected for that speaker.
- [ ] `speakers.csv` row filled in, including consent date.
