# BolChaal AI — Day-by-Day Build Plan

**Project:** Upload PDF/notes/photo → get it explained back as spoken audio in English, Hindi, or Gujarati
**Time budget:** 2 hours/day
**Total duration:** 10 working days (buffer included)
**Cost:** ₹0 — all free tools/APIs

Rule: Finish each day's task fully before moving to the next. If a day runs long, stop at a clean checkpoint and continue same task next day — don't rush into the next day's task.

---

## Phase 1: Core Pipeline (Text-PDF → LLM Explain → Voice, English only)

### Day 1 — Environment Setup + PDF Text Extraction
- Set up Python environment (venv), install libraries: `pdfplumber`, `edge-tts`, `groq`, `flask`
- Get free Groq API key
- Write a script that takes a text-based PDF and extracts raw text using `pdfplumber`
- Test: print extracted text from one of your existing cheat sheet PDFs to confirm extraction works
- **Checkpoint:** You can run a script and see clean extracted text from a PDF in your terminal

### Day 2 — LLM Explanation Layer
- Write the Groq API call that takes extracted text and returns a "tutor-style explanation" (English only for now)
- Design and test your prompt (e.g., "Explain this like a friendly tutor, simply, with examples")
- Test with 2-3 different PDF sections to see explanation quality
- **Checkpoint:** Script takes PDF → prints an LLM-generated explanation in terminal

### Day 3 — Text-to-Speech Integration
- Add `edge-tts` to convert the LLM's explanation text into an audio file (English voice)
- Play/save the audio file, confirm it sounds natural
- Connect all 3 pieces: PDF → extract → LLM explain → TTS audio
- **Checkpoint:** Full pipeline working end-to-end for English — this is your first fully working MVP

---

## Phase 2: Multilingual Support

### Day 4 — Hindi + Gujarati Language Selection
- Update LLM prompt to accept a language parameter (English/Hindi/Gujarati) and generate explanation directly in that language
- Map each language to the correct edge-tts voice (e.g., `hi-IN-SwaraNeural`, `gu-IN-DhwaniNeural`)
- Test the same PDF explained in all 3 languages
- **Checkpoint:** You can pick a language and get both correct text + correct voice output

### Day 5 — Testing & Refinement
- Test with different types of notes (your SQL cheat sheet, ML notes, Excel notes)
- Fix any awkward phrasing, voice mismatches, or prompt issues
- Buffer day if Day 4 ran long
- **Checkpoint:** Pipeline reliably works across multiple documents and all 3 languages

---

## Phase 3: Camera/Image Input (OCR)

### Day 6 — Image Preprocessing
- Install OpenCV, write preprocessing functions: deskew, denoise, contrast enhancement
- Test on a photo of a printed page and a photo of handwritten notes — compare before/after
- **Checkpoint:** You have a "cleaned" image ready for OCR, with visible before/after improvement

### Day 7 — OCR Integration
- Install Tesseract + language packs (English, Hindi, Gujarati)
- Run OCR on preprocessed images, extract text
- Compare accuracy: printed text vs handwritten, and across the 3 languages
- Note down accuracy observations honestly (this becomes a good talking point later)
- **Checkpoint:** Image → cleaned → OCR text extracted, feeding into the same LLM+TTS pipeline from Phase 1/2

### Day 8 — Full Pipeline Integration (Buffer Day)
- Connect image path fully into the main pipeline (same LLM explain + TTS steps as PDFs)
- Test end-to-end: photo in → spoken explanation out, any language
- Use this as buffer if Day 6/7 ran long
- **Checkpoint:** One unified pipeline handles both PDF and photo inputs

---

## Phase 4: Polish & Presentation

### Day 9 — Simple Web Interface
- Build a basic Flask page: upload button (PDF or photo), language dropdown, "Explain" button, audio player
- Wire it to your existing pipeline
- **Checkpoint:** You can use the tool through a browser instead of terminal commands

### Day 10 — Final Testing, README, Demo Recording
- Test full flow multiple times, fix any bugs
- Write a clear README (problem, tech stack, DS vs AI role, limitations, future work)
- Record a short screen-demo video (upload PDF → hear explanation; upload photo → hear explanation)
- Optional: deploy to Render free tier for a live link
- **Checkpoint:** Project is complete, documented, and demo-ready for your portfolio/resume

---

## Notes
- If OCR/handwriting (Days 6-7) proves too unreliable, it's fine to ship without it — Phase 1+2 alone (PDF → voice, 3 languages) is already a complete, demoable project.
- Keep a running note of any limitations you discover (OCR accuracy, voice naturalness) — these make your README and interview answers stronger, not weaker.
