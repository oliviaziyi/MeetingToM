# MeetingToM

**MeetingToM: Evaluating Multimodal LLMs on Theory-of-Mind Reasoning in Multi-Party Meetings**

[Paper](https://arxiv.org/abs/2607.19235) · [Hugging Face](https://huggingface.co/datasets/OliviaWang1101/MeetingToM) · [Project Page](https://oliviaziyi.github.io/MeetingToM-Project-Page/)

MeetingToM is a multimodal benchmark for evaluating **Theory-of-Mind (ToM) reasoning in multi-party meetings**.

Rather than focusing only on visual recognition or transcript understanding, MeetingToM evaluates whether multimodal large language models can reason about the evolving mental and social states of participants in realistic group interactions.

The benchmark covers three complementary levels of social reasoning:

- **Individual level:** how a participant's mental state changes over time.
- **Interpersonal level:** who a speaker is addressing and what stance a participant expresses.
- **Group level:** whether genuine consensus has emerged and whether a participant shows dissent or weak commitment.

MeetingToM is constructed from meeting sessions in the **AMI Meeting Corpus**.

> **Important:** MeetingToM does not redistribute AMI-derived video or audio.  
> Users must obtain authorized access to the AMI Meeting Corpus separately and reconstruct benchmark media locally using the released metadata and reconstruction scripts.

---

## Benchmark Overview

MeetingToM contains three tasks:

| Task | Source bundles | Evaluation records | Questions | Gold answers |
|---|---:|---:|---|---:|
| **STATE** | 300 | 600 | Q1: Mental state | 600 |
| **YOU** | 300 | 300 | Q1: Addressee; Q2: Conversational stance | 600 |
| **CONSENSUS** | 300 | 300 | Q1: Consensus quality; Q2: Dissenter | 600 |

The complete benchmark contains **900 source bundles**, expanded into **1,200 evaluation records** with **1,800 gold answers**.

For STATE, each source bundle contributes two independently evaluated 5-second clips. The same mental-state question is asked for both clips, and each released STATE record contains a single `Q1` answer.

---

## Tasks

### STATE — Individual Mental-State Reasoning

STATE evaluates whether a model can infer the mental state of a target participant from a short meeting clip.

Each STATE evaluation record contains an independently evaluated **5-second clip** of the target participant together with the corresponding meeting audio.

The model answers one mental-state question (`Q1`) for each record.

Each source bundle contributes two independent STATE evaluation records, producing **600 STATE records** in total.

### YOU — Addressee and Stance Reasoning

YOU evaluates interpersonal reasoning between participants.

#### Q1 — Addressee

The model determines who the current speaker appears to be addressing.

Q1 uses the AMI **Corner** camera view.

#### Q2 — Conversational Stance

The model determines the stance expressed by the relevant participant.

Q2 uses a **2×2 close-up mosaic** containing the four participant close-up views.

Q1 and Q2 refer to the same underlying temporal window.

### CONSENSUS — Group Consensus and Dissent

CONSENSUS evaluates group-level social reasoning.

#### Q1 — Consensus Quality

The model determines the quality of consensus currently displayed by the group.

#### Q2 — Dissenter

The model identifies the participant showing weak buy-in or hidden disagreement when appropriate.

Both questions use the same **2×2 close-up mosaic** and refer to the same temporal window.

---

## Repository Structure

```text
MeetingToM/

├── README.md
├── LICENSE-CODE

├── LICENSE-DATA

├── data/
│   ├── state.jsonl
│   ├── you.jsonl
│   └── consensus.jsonl

├── metadata/
│   ├── reconstruction.jsonl
│   └── reconstruction_summary.json

├── scripts/
│   ├── reconstruct.py
│   └── build_mosaic.py

├── evaluation/
│   └── evaluate.py

├── docs/
│   ├── annotation_guidelines.md
│   └── generation_protocol.md

└── prompts/
    ├── question_generation.md
    └── evaluation.md
```

The release is organized into the following components:

- `data/` contains the final benchmark annotations, including benchmark questions, answer options, and adjudicated reference labels.

- `metadata/` contains reconstruction specifications required to locally reproduce benchmark media from an authorized copy of the AMI Meeting Corpus.

- `scripts/` contains utilities for benchmark media reconstruction and visual input preparation.

- `evaluation/` contains the official benchmark evaluator.

- `docs/` provides documentation describing annotation procedures and benchmark construction methodology.

- `prompts/` provides the prompts used for benchmark question generation and model evaluation.
---

## Documentation

The MeetingToM release provides additional documentation describing benchmark construction, annotation procedures, and question generation.

- [Annotation Guidelines](docs/annotation_guidelines.md)
  Detailed annotation guidelines for the three benchmark tasks, including label definitions, decision criteria, annotation principles, and common edge cases.

- [Generation Protocol](docs/generation_protocol.md)
  Documentation of the benchmark construction process, including question formulation, annotation workflow, validation, and quality control procedures.

- [Question Generation Prompts](prompts/question_generation.md)
  Prompts used during benchmark question construction.

- [Evaluation Prompts](prompts/evaluation.md)
  Prompts used for model evaluation experiments.
## Benchmark Data

The final benchmark annotations are stored in:

```text
data/state.jsonl
data/you.jsonl
data/consensus.jsonl
```

The released files contain:

- `data/state.jsonl`: **600 independent evaluation records**
- `data/you.jsonl`: **300 evaluation records**
- `data/consensus.jsonl`: **300 evaluation records**

These JSONL files define the canonical MeetingToM benchmark annotations and are mirrored on Hugging Face for dataset access and Dataset Viewer support.

Each record includes the benchmark question text and valid answer options under `questions`, while `answers` contains the adjudicated reference labels.

### STATE Example

```json
{
  "id": "state:ES2002a_state0004_w0",
  "task": "state",
  "bundle_name": "ES2002a_state0004_w0",
  "source_bundle_name": "ES2002a_state0004",
  "session_id": "ES2002a",
  "window_index": 0,
  "answers": {
    "Q1": "COGNITIVE_CONFLICT"
  },
  "questions": {
    "Q1": {
      "text": "What is participant A's state in the given video?",
      "options": [
        "DISENGAGED_WITHDRAWAL",
        "HESITATION",
        "CONFUSED_BEWILDERMENT",
        "COGNITIVE_CONFLICT",
        "SUPPORTIVE_ENDORSEMENT",
        "FOCUSED_LISTENING",
        "ACTIVE_ENGAGEMENT"
      ]
    }
  }
}
```

### YOU Example

```json
{
  "id": "you:ES2002a_you0002",
  "task": "you",
  "bundle_name": "ES2002a_you0002",
  "session_id": "ES2002a",
  "answers": {
    "Q1": "MULTIPLE",
    "Q2": "NEUTRAL"
  },
  "questions": {
    "Q1": {
      "text": "In this clip, when B says 'you' around 15.0s, who specifically is B referring to?",
      "options": [
        "A",
        "B",
        "C",
        "D",
        "MULTIPLE",
        "UNKNOWN"
      ]
    },
    "Q2": {
      "text": "What is MULTIPLE's attitude toward B's statement?",
      "options": [
        "SUPPORT",
        "OPPOSE",
        "NEUTRAL",
        "UNCERTAIN"
      ]
    }
  }
}
```

### CONSENSUS Example

```json
{
  "id": "consensus:ES2002a_consensus0009",
  "task": "consensus",
  "bundle_name": "ES2002a_consensus0009",
  "session_id": "ES2002a",
  "answers": {
    "Q1": "TRUE_CONSENSUS",
    "Q2": "NONE"
  },
  "questions": {
    "Q1": {
      "text": "What is the quality of group consensus at this moment?",
      "options": [
        "TRUE_CONSENSUS",
        "PSEUDO_CONSENSUS",
        "NO_CONSENSUS",
        "UNCERTAIN"
      ]
    },
    "Q2": {
      "text": "If pseudo-consensus, who appears to have weak buy-in or hidden disagreement?",
      "options": [
        "A",
        "B",
        "C",
        "D",
        "NONE"
      ]
    }
  }
}
```

---

## Data Integrity

The final benchmark contains:

```text
Source bundles
STATE         300
YOU           300
CONSENSUS     300
-----------------
Total         900

Evaluation records
STATE         600
YOU           300
CONSENSUS     300
-----------------
Total       1,200

Gold answers
STATE         600
YOU           600
CONSENSUS     600
-----------------
Total       1,800
```

Evaluation IDs were checked against the released reconstruction metadata:

```text
Evaluation records       1,200
Unique evaluation IDs    1,200
Reconstruction entries   1,200
Missing reconstruction       0
Extra reconstruction         0
```

Every released evaluation record therefore has exactly one corresponding reconstruction specification.

---

## Reconstruction Metadata

Because AMI media cannot be redistributed with MeetingToM, the repository includes:

```text
metadata/reconstruction.jsonl
metadata/reconstruction_summary.json
```

`reconstruction.jsonl` provides the information required to reconstruct each evaluation record from an authorized local copy of the AMI Meeting Corpus.

The reconstruction metadata is aligned one-to-one with the released evaluation records and contains information such as:

- task,
- benchmark bundle identity,
- AMI session,
- source time window,
- required camera view,
- participant/view mapping,
- media construction parameters.

The reconstruction metadata does **not** contain gold benchmark answers.

`reconstruction_summary.json` provides a compact summary of the reconstruction specification and media layout.

---

## Source Media

MeetingToM is built from the **AMI Meeting Corpus**.

MeetingToM does not distribute, mirror, or re-host AMI video or audio files.

Users must obtain authorized access to AMI separately and use the source media in accordance with the applicable AMI terms.

Aligned transcript context used in MeetingToM is derived from the official AMI manual annotations. MeetingToM does not redistribute AMI transcripts as a separate artifact. To reproduce transcript-conditioned inputs, users should obtain the AMI manual annotations from the official AMI Corpus release and align them to the released `session_id` and `source_window` fields.

A typical local AMI layout expected by the reconstruction pipeline is:

```text
AMI_ROOT/
└── ES2002a/
    └── video/
        ├── ES2002a.Closeup1.avi
        ├── ES2002a.Closeup2.avi
        ├── ES2002a.Closeup3.avi
        ├── ES2002a.Closeup4.avi
        └── ES2002a.Corner.avi
```

Meeting audio is expected separately, for example:

```text
AUDIO_ROOT/
└── ES2002a.Mix-Headset.wav
```

When both standard AMI camera files and `_orig` variants are present, the reconstruction scripts prefer the standard non-`_orig` files.

---

## Media Construction

### STATE

Each released STATE record reconstructs one independent 5-second clip using the target participant's close-up view.

Two records originate from each source bundle:

- `window_index = 0`: first 5 seconds of the original source window.
- `window_index = 1`: last 5 seconds of the original source window.
- **Question:** the same `Q1` mental-state question for both records.
- **Audio:** corresponding `Mix-Headset` audio.

### YOU

- **Q1:** AMI Corner view with `Mix-Headset` audio.
- **Q2:** 2×2 close-up mosaic with `Mix-Headset` audio.
- Q1 and Q2 share the same source time window and corresponding audio.

### CONSENSUS

- **Q1 and Q2:** same 2×2 close-up mosaic.
- **Audio:** corresponding `Mix-Headset` audio.
- Both questions share the same source time window.

---

## Mosaic Layout

For YOU-Q2 and CONSENSUS, the four close-up views are combined in the following fixed layout:

```text
+----------------+----------------+
|    Closeup1    |    Closeup2    |
|   top-left     |   top-right    |
+----------------+----------------+
|    Closeup3    |    Closeup4    |
|  bottom-left   | bottom-right   |
+----------------+----------------+
```

Participant identities associated with `Closeup1`–`Closeup4` vary across AMI sessions.

The correct session-specific mapping is stored in the reconstruction metadata and is applied automatically during reconstruction.

---

## Reconstruction

The reconstruction utilities are:

```text
scripts/reconstruct.py
scripts/build_mosaic.py
```

The reconstruction pipeline requires:

- Python 3,
- FFmpeg-compatible media tools,
- an authorized local copy of the AMI Meeting Corpus,
- the corresponding AMI `Mix-Headset` audio files where audio is required.

To inspect the available options:

```bash
python scripts/reconstruct.py --help
```

and:

```bash
python scripts/build_mosaic.py --help
```

The reconstruction scripts use:

```text
metadata/reconstruction.jsonl
```

as the public reconstruction specification.

Reconstructed AMI-derived media should remain local and should not be redistributed as part of MeetingToM.

---

## Reconstruction Reproducibility

The public reconstruction pipeline was validated against representative benchmark media used during benchmark construction.

Validation covered:

- STATE,
- YOU,
- CONSENSUS.

Representative reconstructed videos matched the canonical benchmark media within the expected tolerance introduced by video re-encoding.

For validated audio-bearing samples, reconstructed audio matched the benchmark audio content.

The released reconstruction metadata and scripts contain no internal project paths.

---

# Evaluation

The official evaluator is:

```text
evaluation/evaluate.py
```

It uses only the Python standard library and does not require `scikit-learn` or `pandas`.

The released evaluator preserves the scoring semantics used in the benchmark experiments.

---

## Running Evaluation

From the repository root:

```bash
python evaluation/evaluate.py \
  --gt data/state.jsonl \
  --gt data/you.jsonl \
  --gt data/consensus.jsonl \
  --pred_dir /path/to/predictions \
  --out_dir results
```

The evaluator detects STATE, YOU, and CONSENSUS prediction files from the prediction directory.

The evaluator writes the aggregated result table to the directory specified by `--out_dir`:

```text
overall_summary.csv
```

Model predictions and experimental result files are not included in the public release.

---

## Prediction Files

Prediction JSONL files must preserve enough benchmark identity information for the evaluator to align outputs with the released gold data.

Supported identity information includes fields such as:

```text
id
bundle_name
custom_id
metadata
```

STATE predictions must additionally preserve the corresponding temporal-window identity.

Model predictions must appear in actual model-output fields.

The evaluator supports common output structures including fields and containers such as:

```text
answers
prediction
pred
pred_label
model_pred
answer
label
output
result
parsed
completion
response
choices
generated_text
output_text
response_text
```

The evaluator deliberately does **not** interpret request prompts or metadata as predictions.

Input-only records containing fields such as:

```text
messages
prompt
input
metadata
```

without an actual model response should not be treated as prediction records.

This prevents prompt text or answer-option text from being incorrectly parsed as a model prediction.

---

## Evaluation Metrics

The public output contains the following fields:

```text
model
variant

state_acc
state_macro_f1

you_q1_acc
you_q1_macro_f1

you_q2_acc
you_q2_macro_f1

cons_q1_acc
cons_q2_cond_acc
cons_points_acc
```

Confusion matrices, per-class diagnostic tables, and Micro-F1 are intentionally omitted from the public output.

---

## STATE Metrics

STATE reports:

- **Accuracy**
- **Macro-F1**

STATE metrics are computed over the **600 independent STATE evaluation records**.

Each record contains one benchmark question under `questions.Q1`, including its valid answer options, and one adjudicated reference label under `answers.Q1`. The original source-bundle and temporal-window identity are retained through `source_bundle_name` and `window_index`.

The evaluator preserves the prediction convention used in the benchmark experiments: each STATE prediction is extracted from the model output's `Q1` field.

---

## YOU Metrics

YOU-Q1 and YOU-Q2 are evaluated separately.

### YOU-Q1

Reports:

- Accuracy
- Macro-F1

### YOU-Q2

Reports:

- Accuracy
- Macro-F1

There is no conditional gating between YOU-Q1 and YOU-Q2.

---

## CONSENSUS Metrics

CONSENSUS uses a two-step scoring protocol.

### Q1 Accuracy

`cons_q1_acc` measures consensus-quality prediction accuracy.

### Conditional Q2 Accuracy

`cons_q2_cond_acc` evaluates Q2 only on instances where Q1 is predicted correctly.

### Two-Step Points Accuracy

`cons_points_acc` uses the following rule:

```text
Q1 incorrect
→ 0 points

Q1 correct, Q2 incorrect
→ 1 point

Q1 correct, Q2 correct
→ 2 points
```

Q2 therefore earns a point only when Q1 is also correct.

For an evaluated instance with both predictions available, the maximum score is 2 points.

---

## Prediction Coverage

The evaluator reports parsing and alignment statistics in the terminal.

For fair comparison with reported benchmark results, predictions should be provided for the complete released evaluation set.

Missing or unparseable predictions reduce evaluation coverage.

Users should check aligned sample counts when comparing runs, particularly when predictions are incomplete.

---

## Official Evaluation Output

`overall_summary.csv` contains one row per model and prompting variant.

Schema:

```csv
model,variant,state_acc,state_macro_f1,you_q1_acc,you_q1_macro_f1,you_q2_acc,you_q2_macro_f1,cons_q1_acc,cons_q2_cond_acc,cons_points_acc
```

---

## Evaluation Validation

The public evaluator was regression-tested against the original benchmark evaluation implementation.

Across the validated benchmark runs:

```text
52 common model/variant runs
0 missing runs
0 extra runs
0 differences across the public core metrics
```

The public evaluator therefore preserves the benchmark's original scoring behavior while providing a cleaner release interface.

---

## Reproducibility Principles

MeetingToM separates benchmark annotations from source-media distribution.

The release follows three principles:

1. **Final benchmark annotations are released directly.**
2. **AMI-derived media is not redistributed.**
3. **Benchmark media can be reconstructed locally from authorized AMI data using the released metadata and scripts.**

This design supports reproducibility while respecting the distribution conditions of the source corpus.

---

## Paper

**MeetingToM: Evaluating Multimodal LLMs on Theory-of-Mind Reasoning in Multi-Party Meetings**

Authors:

- Ziyi Wang
- Yuhang Wu
- Dongxu Piao
- Xingyu Liu
- Tianhui Zhou
- Miao Liu

---

## Citation

If you use MeetingToM in your research, please cite the MeetingToM paper.

```bibtex
@article{wang2026meetingtom,
  title   = {MeetingToM: Evaluating Multimodal LLMs on Theory-of-Mind Reasoning in Multi-Party Meetings},
  author  = {Wang, Ziyi and Wu, Yuhang and Piao, Dongxu and Liu, Xingyu and Zhou, Tianhui and Liu, Miao},
  journal = {arXiv preprint arXiv:2607.19235},
  year    = {2026}
}
```

---

## License

The MeetingToM release uses separate licenses for code and benchmark data:

- The code in `scripts/` and `evaluation/` is released under the **MIT License**. See `LICENSE-CODE`.
- The benchmark annotations in `data/` and reconstruction metadata in `metadata/` are released under the **Creative Commons Attribution 4.0 International (CC BY 4.0) License**. See `LICENSE-DATA`.

These licenses apply only to materials released by the MeetingToM authors.

**AMI Meeting Corpus video and audio are not redistributed by MeetingToM and are not covered by either MeetingToM license.** Users must obtain authorized access to AMI separately and comply with the applicable AMI terms and conditions.

---

## Acknowledgements

MeetingToM builds on the **AMI Meeting Corpus**.

We thank the creators and maintainers of AMI for making multi-party meeting data available to the research community.

---

## Contact

For questions about MeetingToM, benchmark reconstruction, or evaluation, please use the issue tracker associated with this repository.
