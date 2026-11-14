# A2 Dataset Review Notes (Draft)

`dataset.tsv` contains 50 aligned English/Bangla pairs across categories: `question`, `instruction`, `explanation`, `arithmetic`, `summarise`, `long`.

**Status:** Drafted automatically; **needs student review and approval of EVERY Bangla line** before Stage 8 full run (per spec). Bangla is intended to carry exactly the same meaning as English (no extra/missing detail).

## Pairs I was least sure about
- **43 (long):** English says "visited his grandparents in a small village" without specifying maternal/paternal. Bangla uses "দাদা-দাদী/নানা-নানির" to avoid guessing; this preserves ambiguity but is a phrasing choice to verify.
- **45 (long):** "within a few hours" rendered as "কয়েক ঘণ্টার মধ্যেই" — generally equivalent, but please confirm tone/precision.
- **46 (long):** "mobile devices" rendered as "মোবাইল ডিভাইস" (loan term) vs possible "মোবাইল যন্ত্র"; meaning preserved, style choice to confirm.
- **39 (summarise):** "expect to harvest it after a few months" rendered as "কয়েক মাস পরে তা কাটার আশা করছে" — check that "harvest/cut rice" nuance matches intent.
- **31 (arithmetic):** Units/number phrasing kept explicit; confirm numeral style (Arabic numerals used in Bangla text) is acceptable for your evaluation setup.

Please review all 50 rows, correct any Bangla lines as needed, and reply with approval before I treat the dataset as final.
