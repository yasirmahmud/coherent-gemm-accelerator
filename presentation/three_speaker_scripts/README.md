# Three speaker recording plan

These scripts follow the original [GEMM Accelerator Presentation video](../GEMM_Accelerator_Presentation.mp4), which runs **4:57.43** and contains **11 slides**. They adapt [narration_script.md](../narration_script.md). The separate nine-slide schedule in `speaker_notes.md` belongs to the other deck and does not match this video.

## Speaker allocation

An exact third is 1:39.14. Keeping complete slides together gives the following balanced allocation. Speaker numbers are placeholders for whichever teammate takes each part.

| Speaker | Slides | Recording duration | Content |
| --- | --- | --- | --- |
| [Speaker 1](speaker_1.md) | 1–4 | 1:41.0 | Introduction, motivation, architecture, experiments |
| [Speaker 2](speaker_2.md) | 5–8 | 1:48.3 | Wider tiles, latency, cache requests, interface limits |
| [Speaker 3](speaker_3.md) | 9–11 | 1:28.13 | System payoff, proposal comparison, conclusions |

The two handoffs occur at slide boundaries. Speaker 1 introduces the wider-tile idea before Speaker 2 explains it. Speaker 2 ends by connecting local gains to system performance, which Speaker 3 then evaluates. No spoken introductions between speakers are needed.

## Recording instructions

- Read only the quoted narration. Headings, timestamps, and directions are silent.
- Each script uses only **elapsed recording time**, starting at **0:00.0** for that speaker. Every cue has one timestamp. Keep the indicated pauses so the recording stays aligned with the existing visuals.
- Begin speaking at each narration cue and finish before the next cue. These are rehearsal targets, not measured speech durations. Use a calm, consistent pace and pause naturally at sentence boundaries. If a passage overruns, retake it rather than rushing the ending.
- Record while watching the matching section with the original audio muted, using headphones. Keep the same microphone distance and recording level throughout.
- Prefer one WAV file per speaker, mono, 48 kHz, named `speaker_1.wav`, `speaker_2.wav`, and `speaker_3.wav`. Preserve the initial silence relative to recording time zero. Leave about one second of extra quiet before stopping; that extra tail can be trimmed during assembly.
- If recording separate slide takes instead, name them by speaker and slide, such as `speaker_2_slide_05.wav`, and retain a little quiet at both ends. Their recording cues provide placement references within that speaker’s section.
- Say GEMM as “jem,” CPU as “C P U,” RTL as “R T L,” MESI as “messy,” and gem5-Aladdin as “gem five Aladdin.” Read the written-out numbers naturally.

Slide changes were checked against the original video. Cue times use tenths of a second and allow short pauses around the transitions. The last spoken line ends before the final fade. The existing video and its audio have not been changed.

## Content note

Slide 10 of the original video includes work planned for the final report. Speaker 3 retains that statement to match the visible slide. This recording plan follows the original video rather than replacing it with the different completed-study deck.
