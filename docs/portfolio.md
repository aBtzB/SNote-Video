# Making the project your own

A useful project question is: “How much editing is needed to turn an automatically generated subtitle draft into a readable bilingual subtitle file?”

Use a few clips you can share. Keep reference transcripts and record concrete corrections, timing adjustments, processing time, and the chosen models. Separate transcription mistakes from translation mistakes. Avoid publishing accuracy or speed figures you have not measured.

Parts worth understanding:
- Why recognition audio is extracted from the preview timeline.
- How leading silence affects cue alignment.
- Why a global offset cannot correct changing drift.
- Why a source edit invalidates an unchanged translation.
- How the revision check prevents one tab from overwriting another.
- What tests with generated tones prove, and what requires actual speech.

A focused extension could be split/merge controls, audio-track selection, speaker labels, or language-specific reading-speed thresholds. Choose something you need, implement it, and describe the tradeoffs.

After running, understanding, and extending the project, adapt this CV wording to your actual contribution:

> Developed a local video subtitling application in Python and JavaScript, integrating FFmpeg, Whisper transcription, local translation models, editable cue timing, bilingual preview, and subtitle exports.

The models are existing open-source components. Keep their credits and describe assistance accurately when asked or required by your project.
