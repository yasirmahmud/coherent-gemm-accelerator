# Completed coherent-GEMM framework and tradeoff study

- [Editable PowerPoint](project_presentation.pptx), with embedded narration and source references.
- [Vector PDF](project_presentation.pdf).
- [Timed narration](speaker_notes.md).

Present **slides 1–9 in 5:00**. Slides 10–12 are technical Q&A backups.

The talk begins with the performance–resource tradeoff, defines the symbols graphically, presents the implemented framework and completed experiment coverage, then shows measured design choices. It concludes with findings from the completed study. No progress, remaining-task, report-preparation, or course-submission content appears in the talk or narration.

The implementation is described as the complete **project-specific framework built on gem5-Aladdin**: kernels, host harnesses, queue/retry integration, passive instrumentation, experiment automation, validation, and analysis. The upstream simulator is credited explicitly.

The main results include both positive and negative outcomes:

- At N=32, width 4 reduces offload time by 25.1% and increases modeled total area by 27.7%, relative to width 1.
- At N=24, width 4 is faster and slightly smaller in the main comparison.
- In the separate N=24 unchanged-input repeated-call diagnostic, width 4 reduces first-call offload time by 11.9%, but increases second-call offload time from 819 ns to 838 ns (2.3%). This is an observed diagnostic reversal; it is not a claim that increasing width slows the main single-invocation sweep.
- Memory-interface capacity changes the width benefit, and whole-program improvements are much smaller than datapath improvements.

All numerical results use the validated fresh suite selected by `paper/experiment_data.json`. The 107 executions cover different experiment families and include expected input-boundary failures; they are not 107 repetitions. Area remains a pre-RTL model estimate. Technical measurement and trace-model details are available in the backup slides.

The white academic theme uses Arial, dark text, a muted blue accent, ruled tables, and native editable diagrams and charts. `content.json` holds narration and sources; `build_deck.py` defines layouts and reads selected experiment summaries.

Regenerate from the repository root using Python 3.8+:

```bash
python3.11 -m venv /tmp/gemm-deck-env
/tmp/gemm-deck-env/bin/python -m pip install -r presentation/requirements.txt
/tmp/gemm-deck-env/bin/python presentation/build_deck.py
```

PowerPoint uses Arial. The PDF embeds the metrically similar FreeSans font from `/usr/share/fonts/gnu-free/`; adjust `FONT_ROOT` for another machine. The PDF uses the same drawing commands and content; it is not an Office export. `layout_audit.json` records text positions, sizes, and line counts. Bounds, text intersections, numerical sources, and the narration schedule are checked; the PDF layouts are visually reviewed.
