# MeetingToM Generation Protocol

This document describes the **dataset construction and release pipeline** for MeetingToM. It focuses on how source meeting material was converted into candidate tasks, how GPT-assisted candidate generation was used, how candidates were screened and annotated, and how the final public benchmark representation was produced.

For label semantics and task-specific annotation decisions, see [`annotation_guidelines.md`](annotation_guidelines.md).  
For the recovered question-generation prompts, see [`../prompts/question_generation.md`](../prompts/question_generation.md).  
For model-evaluation prompts, see [`../prompts/evaluation.md`](../prompts/evaluation.md).

## 1. Scope and Provenance

MeetingToM is constructed from the **AMI Meeting Corpus** and evaluates meeting-grounded social reasoning at three levels:

1. **STATE** — subject-level mental/interactional state;
2. **YOU** — dyadic-level addressee and attitude reasoning;
3. **CONSENSUS** — group-level consensus quality and hidden dissent.

MeetingToM does not redistribute AMI audiovisual media. The public release provides benchmark annotations, source-session identifiers, source time windows, view requirements, participant/view mappings, reconstruction metadata, reconstruction utilities, prompts, documentation, and the official evaluator. Users reconstruct the task media from an authorized local copy of AMI.

The construction process consisted of:

- task-specific candidate extraction from AMI-derived meeting material;
- GPT-assisted candidate question generation;
- candidate ranking;
- manual screening;
- human annotation and adjudication;
- task-specific cleaning and normalization;
- final release conversion and validation.

---

# 2. Final Benchmark Accounting

The released benchmark should be counted at two distinct levels: **source bundles** and **evaluation records**.

## 2.1 Source bundles

Each task family contributes 300 selected source bundles:

```text
STATE source bundles        300
YOU source bundles          300
CONSENSUS source bundles    300
-------------------------------
Total source bundles        900
```

## 2.2 Evaluation records

STATE uses two independently evaluated five-second windows per selected source bundle. Each window is released as a separate evaluation record with one state question.

YOU and CONSENSUS each retain one evaluation record per selected source bundle, with two benchmark questions per record.

```text
STATE evaluation records        600   (300 bundles × 2 windows)
YOU evaluation records          300
CONSENSUS evaluation records    300
-----------------------------------
Total evaluation records      1,200
```

## 2.3 Gold answers

```text
STATE gold answers        600   (1 per evaluation record)
YOU gold answers          600   (2 per evaluation record)
CONSENSUS gold answers    600   (2 per evaluation record)
-----------------------------
Total gold answers      1,800
```

Thus, the release contains:

> **900 source bundles, expanded into 1,200 evaluation records with 1,800 adjudicated reference answers.**

---

# 3. Source Representation and Media Views

MeetingToM uses AMI session identifiers and source time intervals to define reconstructable benchmark media.

The task-specific evaluation views are:

| Task | Visual input |
|---|---|
| STATE | target-participant close-up |
| YOU Q1 | corner/global view |
| YOU Q2 | synchronized 2×2 close-up mosaic |
| CONSENSUS Q1/Q2 | synchronized 2×2 close-up mosaic |

Where used by the reconstruction pipeline, audio is derived from the aligned AMI Mix-Headset channel, and task records are paired with the aligned transcript window.

The 2×2 mosaic follows the fixed spatial arrangement:

```text
Closeup1 | Closeup2
---------+---------
Closeup3 | Closeup4
```

The mapping from AMI close-up views to anonymized benchmark participant labels (`A`–`D`) is session-specific and is stored in the released reconstruction metadata.

The public reconstruction specification is stored under:

```text
metadata/reconstruction.jsonl
metadata/reconstruction_summary.json
```

with reconstruction utilities under:

```text
scripts/reconstruct.py
scripts/build_mosaic.py
```

The reconstruction metadata contains source provenance and media-building information but does not contain gold benchmark answers.

---

# 4. Pipeline Overview

At a high level, the benchmark was constructed through the following stages:

```text
AMI source meetings
        ↓
task-specific candidate extraction
        ↓
GPT-assisted candidate question generation
        ↓
automatic candidate scoring / ranking
        ↓
manual screening of ranked candidates
        ↓
human annotation and adjudication
        ↓
task-specific cleaning and normalization
        ↓
final selection of 300 source bundles per task
        ↓
STATE window-to-record conversion
        ↓
public JSONL + reconstruction metadata
        ↓
release validation and evaluator regression testing
```

The following sections document each stage in more detail.

---

# 5. Task-Specific Candidate Construction

## 5.1 STATE

### Construction representation

The STATE construction pipeline originally represented a selected candidate using two short temporal windows:

- an **EARLY** five-second window;
- a **LATE** five-second window.

Both windows referred to the same target participant.

The transition/refinement prompt recovered from the construction code asked for:

- Q1: the target participant's state in the EARLY window;
- Q2: the target participant's state in the LATE window.

The candidate label set was:

```text
ACTIVE_ENGAGEMENT
SUPPORTIVE_ENDORSEMENT
FOCUSED_LISTENING
COGNITIVE_CONFLICT
CONFUSED_BEWILDERMENT
HESITATION
DISENGAGED_WITHDRAWAL
```

### Final release conversion

The final public STATE benchmark does **not** treat EARLY and LATE as two questions inside one evaluation record.

Instead, each selected STATE source bundle is converted into two independent five-second records:

```text
source bundle
├── window_index = 0  → one STATE evaluation record, answers.Q1
└── window_index = 1  → one STATE evaluation record, answers.Q1
```

This produces:

```text
300 STATE source bundles
→ 600 independent STATE evaluation records
→ 600 gold STATE answers
```

Each final record is evaluated independently.

---

## 5.2 YOU

YOU was constructed to support dyadic reasoning around a focal addressing event.

### Final released subtasks

The released benchmark retains:

- **Q1 — Addressee Identification**
- **Q2 — Attitude Inference**

The final label spaces are:

```text
Q1:
A, B, C, D, MULTIPLE, UNKNOWN

Q2:
SUPPORT, OPPOSE, NEUTRAL, UNCERTAIN
```

### View specialization

The two subtasks use different synchronized visual representations:

- Q1 uses the corner/global view to support gaze, body orientation, spatial layout, and recipient-response reasoning.
- Q2 uses the 2×2 close-up mosaic to support per-participant facial and upper-body attitude evidence.

### Construction-stage local-power component

The recovered original YOU candidate-generation prompt covered three conceptual components:

1. addressee resolution;
2. addressee attitude;
3. local interactional power.

It requested a broader set of candidate QA items, including a local-power classification.

Subsequent cleaned YOU artifacts (`nopower`) retain only Q1 and Q2 corresponding to addressee and attitude. The local-power component was therefore removed before the final released benchmark and is not part of the public YOU task.

---

## 5.3 CONSENSUS

The CONSENSUS construction prompt generated a broader candidate QA set around group agreement, social convergence, and hidden dissent.

The final released benchmark retains two canonical questions:

- **Q1 — Consensus Quality**
- **Q2 — Hidden Dissenter**

The final Q1 label space is:

```text
TRUE_CONSENSUS
PSEUDO_CONSENSUS
NO_CONSENSUS
UNCERTAIN
```

The final Q2 label space is:

```text
A
B
C
D
NONE
```

Q2 is semantically conditional: an individual dissenter is identified only for a pseudoconsensus interpretation when one participant can be reliably isolated as the standout weak-buy-in or hidden-disagreement case.

Both questions are grounded in the same synchronized 2×2 close-up mosaic and aligned transcript window.

---

# 6. GPT-Assisted Candidate Question Generation

## 6.1 Role of GPT

GPT was used to assist **candidate construction**, not to determine the final benchmark gold labels.

For candidate clips, the generation system produced structured candidate information that could include:

- question text;
- answer options;
- a provisional answer;
- a rationale;
- evidence timestamps or evidence localization;
- a quality / evidence-coverage score;
- task-specific metadata.

The model-produced score was used only as a **ranking heuristic** during manual screening. It was not interpreted as:

- a correctness probability;
- an evaluation metric;
- confidence in the final human label;
- supervision for the adjudicated benchmark reference.

Final benchmark answers were assigned and adjudicated by human annotators rather than copied from model provisional answers.

---

## 6.2 Recovered Original Generator Configuration

The recovered original multi-task question-generation source uses the OpenAI Responses API.

Its source defaults specify:

```text
model: gpt-5-2025-08-07
max_output_tokens: 8000
frames: 6
max_workers: 20
```

The recovered API call passes:

```text
model
input
max_output_tokens
```

and does not explicitly pass:

```text
temperature
top_p
seed
```

This is the configuration described in the reviewer response for the original GPT-assisted candidate-generation stage.

### Configuration provenance

The values above are the recovered source defaults and API-call settings for the original generator. The retained generation outputs do not store a separate per-run copy of the full command-line configuration.

---

## 6.3 STATE Transition/Refinement Prompt Provenance

A later STATE transition rerun/refinement script was also recovered. Its prompt is the STATE construction prompt reproduced in `prompts/question_generation.md`.

This script:

- uses the OpenAI Responses API;
- takes the model identifier as a required command-line argument;
- exposes `max_output_tokens` with a source default of `1200`;
- exposes `temperature` with a source default of `0.2`;
- generates Q1 for the EARLY window and Q2 for the LATE window.

This later STATE refinement stage is documented separately from the original multi-task generator because it used a distinct task-specific script and configuration interface.

---

## 6.4 Prompt Release

The recovered construction prompts are documented in:

```text
prompts/question_generation.md
```

The prompt file intentionally preserves construction-stage scope, including components that were later removed during cleaning, and documents the corresponding final-task conversion separately rather than silently rewriting the historical prompt.

---

# 7. Candidate Ranking and Manual Screening

## 7.1 Ranking signal

Candidate-generation outputs included a model-produced score reflecting evidence quality or evidence coverage.

This score was used as a preliminary ranking signal to prioritize manual review.

It was **not** used as:

- a gold-label confidence score;
- a probability of correctness;
- a model-performance metric;
- automatic supervision for the final reference answers.

## 7.2 Initial screening pool

For each task family, the **400 highest-ranked candidates** formed the initial manual screening pool.

Across the three task families:

```text
STATE ranked screening pool        400
YOU ranked screening pool          400
CONSENSUS ranked screening pool    400
--------------------------------------
Total ranked screening pool      1,200
```

The retained final source-bundle IDs are strict subsets of these ranked pools.

## 7.3 Manual review procedure

Annotators reviewed candidates in descending rank order.

Candidates could be excluded when the available evidence did not support a reliable benchmark judgment. Replacements were drawn from the remaining ranked candidates until 300 source bundles were retained for the task.

Typical exclusion reasons included:

- insufficient visibility of the target participant;
- ambiguous or internally conflicting behavioral evidence;
- a camera view that did not support the inference required by the question;
- insufficiently identifiable participant mapping;
- insufficiently informative interaction around the target event;
- evidence that did not support a stable task-specific annotation.

The generated question text was retained without manual rewriting in the documented screening protocol.

## 7.4 Recoverability of per-reason counts

The final retained sets and the 400-item ranked pools are recoverable.

The retained artifacts support the stage-level counts reported below and the main exclusion categories. Per-reason rejection totals were not preserved as a separate canonical ledger.

---

# 8. Human Annotation and Adjudication

## 8.1 Annotation team

The annotation team consisted of three annotators:

- two undergraduate students;
- one master's graduate.

Their academic/research backgrounds spanned:

- management;
- computer vision;
- machine learning.

One annotator had approximately one year of HCI research experience and prior research related to cognition.

## 8.2 Preparation

Before production annotation, all annotators completed approximately one week of task-specific preparation.

Preparation included:

- studying the annotation guidelines;
- reading relevant Theory-of-Mind and cognitive-science literature cited by the project;
- familiarization with task definitions and evidence requirements;
- discussion of common label confusions and boundary cases.

## 8.3 Pilot stage

All annotators independently labeled a common pilot set of approximately 20 instances.

No numerical qualification threshold was used.

Production annotation began after the pilot set had been completed and the team had reviewed:

- major disagreements;
- label definitions;
- evidence requirements;
- ambiguous cases;
- the adjudication procedure.

## 8.4 Calibration during production

Throughout production annotation, the team held approximately weekly calibration meetings lasting one to two hours.

These meetings were used to:

- review ambiguous items;
- resolve disagreements;
- clarify label boundaries;
- update the annotation guidelines;
- maintain consistency in the use of uncertainty categories and evidence requirements.

## 8.5 Adjudication

The final reference labels are **adjudicated, evidence-grounded third-person annotations**.

Adjudication establishes the reference label used for benchmark scoring. This is particularly relevant for socially interpretive categories such as interpersonal attitude, pseudoconsensus, and hidden dissent.

Complete item-level pre-adjudication labels are not part of the retained release artifacts.

---

# 9. Relationship Between GPT Outputs and Human Gold Labels

The candidate-generation system could output provisional answers and rationales. These outputs were **not** treated as final benchmark answers.

The construction protocol separates the two roles:

```text
GPT-assisted generation
→ candidate question / options / provisional interpretation / ranking signal

Human annotation and adjudication
→ final benchmark reference label
```

The final public `answers` fields therefore contain adjudicated human reference labels rather than copied GPT provisional answers.

## 9.1 Provisional GPT fields during screening

Candidate records contained provisional GPT answers and rationales. The retained artifacts do not encode a stage-by-stage visibility log for these fields during manual screening. The final reference answers were assigned and adjudicated by human annotators rather than copied from GPT outputs.

---

# 10. Task-Specific Cleaning and Final Normalization

## 10.1 STATE

The construction representation used two temporal questions per selected source bundle:

```text
EARLY window → Q1
LATE window  → Q2
```

For final release, the two windows were separated into independent five-second evaluation records.

Each record contains:

- one benchmark question under `questions.Q1`;
- one adjudicated reference answer under `answers.Q1`;
- `source_bundle_name`;
- `window_index`;
- source-session and reconstruction information.

This conversion preserves the selected source bundle while making the two temporal observations independently evaluable.

## 10.2 YOU

Earlier candidate-generation material included addressee, attitude, and local interactional power.

Subsequent cleaned `nopower` artifacts contain only:

```text
Q1 = addressee
Q2 = attitude
```

The public YOU task therefore excludes local power.

## 10.3 CONSENSUS

The broader construction-stage candidate QA set was reduced to the final canonical pair:

```text
Q1 = consensus quality
Q2 = hidden dissenter
```

The public benchmark uses the fixed label spaces documented in `annotation_guidelines.md`.

---

# 11. Question and Option Enrichment of the Public JSONL

The final public JSONL records include:

- benchmark question text under `questions`;
- valid answer options under each question;
- adjudicated reference labels under `answers`.

The question text in the final release was aligned against the cleaned construction artifacts.

Validation of the public question enrichment found:

```text
STATE question mismatches:       0
YOU Q1 question mismatches:      0
YOU Q2 question mismatches:      0
CONSENSUS Q1 mismatches:         0
CONSENSUS Q2 mismatches:         0
```

A non-question-field comparison also found no changes to the benchmark records beyond the intended question/option enrichment.

The provisional GPT answers and rationales from candidate generation are **not** used as the public gold answers.

---

# 12. Final Public Data Files

The released benchmark annotations are stored in:

```text
data/state.jsonl
data/you.jsonl
data/consensus.jsonl
```

At the evaluation-record level:

```text
data/state.jsonl        600 records
data/you.jsonl          300 records
data/consensus.jsonl    300 records
```

The public JSONL files are the source of truth for benchmark evaluation.

---

# 13. Reconstruction Package

Because MeetingToM does not redistribute AMI audiovisual files, each selected source bundle is paired with a reconstruction specification.

The public package includes:

```text
metadata/reconstruction.jsonl
metadata/reconstruction_summary.json
scripts/reconstruct.py
scripts/build_mosaic.py
```

The reconstruction metadata specifies, where applicable:

- benchmark task;
- source bundle identity;
- AMI session identifier;
- source start/end timestamps;
- target participant;
- required camera view(s);
- close-up-to-participant mapping;
- mosaic layout;
- audio source;
- media-construction parameters.

Representative reconstruction checks obtained high visual similarity (approximately 0.98–0.99 SSIM in validated cases) and exact or near-exact audio agreement in the checked cases.

These checks validate the reconstruction procedure for representative samples; they are not benchmark performance metrics.

---

# 14. Evaluation-Record Validation

The public benchmark evaluator is located at:

```text
evaluation/evaluate.py
```

It supports:

- STATE accuracy and Macro-F1;
- YOU Q1 accuracy and Macro-F1;
- YOU Q2 accuracy and Macro-F1;
- CONSENSUS Q1 accuracy;
- conditional CONSENSUS Q2 accuracy;
- two-step CONSENSUS points accuracy.

The public evaluator was regression-tested against the original benchmark evaluation behavior on the validated run set:

```text
common model/variant runs:    52
missing runs:                  0
extra runs:                    0
core-metric differences:      0
```

Question/option enrichment of the public JSONL also produced zero differences in the validated core metrics.

---

# 15. Recoverable Stage-Level Counts

The following counts are directly recoverable from the retained artifacts and final release:

| Stage | STATE | YOU | CONSENSUS | Total |
|---|---:|---:|---:|---:|
| Ranked manual-screening pool | 400 | 400 | 400 | 1,200 |
| Final selected source bundles | 300 | 300 | 300 | 900 |
| Final evaluation records | 600 | 300 | 300 | 1,200 |
| Final gold answers | 600 | 600 | 600 | 1,800 |

A single canonical count for every earlier raw candidate-generation stage is not available across all three task families. The release therefore reports the counts that are directly recoverable and avoids reconstructing unsupported totals.

---

# 16. Provenance Notes

The release records the construction information that can be directly supported by retained source code, candidate artifacts, final benchmark files, and evaluation outputs. The main historical fields that were not stored as canonical per-run metadata are:

- exact command-line overrides for every generation run;
- per-rejection-reason totals;
- complete item-level pre-adjudication labels;
- a stage-by-stage visibility log for provisional GPT answers and rationales during screening.

These notes concern historical construction metadata; the released benchmark questions, option spaces, adjudicated reference labels, reconstruction specifications, and evaluation behavior are directly validated by the retained artifacts.

# 17. Relationship to Other Release Files

The release separates four reproducibility concerns:

```text
prompts/question_generation.md
    Historical/recovered prompts used during candidate construction.

docs/generation_protocol.md
    Dataset construction, ranking, screening, annotation, adjudication,
    cleaning, final selection, and release conversion.

docs/annotation_guidelines.md
    Operational definitions and decision rules for benchmark labels.

prompts/evaluation.md
    Prompts used to evaluate models on the completed benchmark.
```

This separation is intentional: **construction prompts**, **construction procedure**, **human label semantics**, and **model evaluation prompts** are distinct components of the benchmark.
