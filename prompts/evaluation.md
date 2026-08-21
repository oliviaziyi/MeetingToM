# Evaluation Prompts

This file documents the task-specific prompts used to evaluate models on MeetingToM.
These prompts are distinct from the prompts used during benchmark construction and question generation.

The templates below use placeholders such as `{QUESTION}`, `{TRANSCRIPT}`, `{TARGET_AGENT}`,
`{CORNER_LAYOUT}`, and `{MOSAIC_LAYOUT}` for instance-specific content.

## Common System Prompt

```text
You are an evaluation model. Follow the output schema strictly. No extra text.
```

---

## STATE

STATE evaluates the mental/interactional state of one target participant in one short temporal window.
The model receives a target-participant video, the transcript from the same window, the target identity,
and one single-choice question.

### Base Evaluation Template

```text
You will be given:
- A short meeting clip video of ONE target participant
- The transcript for the same time window (may be empty)
- Target participant shown in the video: {TARGET_AGENT}.

Task:
Answer the following VISUAL QUESTION ANSWERING (VQA) question based primarily
on the observed visual behavior in the video.

Question (single-choice):
{QUESTION}

Options (choose exactly ONE):
DISENGAGED_WITHDRAWAL,
HESITATION,
CONFUSED_BEWILDERMENT,
COGNITIVE_CONFLICT,
SUPPORTIVE_ENDORSEMENT,
FOCUSED_LISTENING,
ACTIVE_ENGAGEMENT

Output format (STRICT JSON, single line, no extra keys):
{"Q1":"<OPTION>"}

Transcript:
{TRANSCRIPT}
```

### Task-aligned CoT Addendum

```text
Think step by step to decide the best label.

First assess whether the target is clearly visible, partially visible, poorly visible,
or not visible at all.

Then identify at least two clear cues across categories such as affect, gaze, posture,
gesture, timing, and engagement. If you cannot identify clear cues, treat the evidence
as insufficient and choose a conservative label.

Resolve common confusions as follows.

Supportive endorsement requires clearly positive signals like a nod-smile pattern;
otherwise prefer focused listening.

Confused bewilderment indicates comprehension-difficulty signs; hesitation indicates
a turn-taking pause or abort before speaking.

Focused listening implies gaze mostly on the speaker with stable posture;
disengaged withdrawal implies sustained gaze away or down with low reactivity.
```

### Emotional Chain-of-Thought (EoT) Addendum

```text
Follow the Emotional Chain-of-Thought below and think step by step.

Step 1 Understanding context.
Infer what is happening in this moment and the target participant's likely role
in the interaction. Use the transcript only to locate timing if needed.

Step 2 Recognizing emotions from visible cues.
From affect, gaze, posture, head movement, engagement level, gesture energy,
and response timing, infer the target participant's likely emotional tendency,
while tracking uncertainty when cues are weak.

Step 3 Recognizing self emotions.
Notice any immediate interpretive bias or emotional pull you feel while observing,
and acknowledge uncertainty internally rather than forcing a confident story.

Step 4 Managing self emotions.
Regulate overconfidence and avoid projecting emotions onto the target.
Keep an evidence-first stance and let uncertainty remain when the video
does not support a clear inference.

Step 5 Influencing others' emotions and generating the final answer.
Synthesize the emotionally informed visual evidence into the single best option
that matches the dominant state across the whole window. If the evidence is weak
or mixed, choose the most conservative option and lower confidence.
```

---

## YOU

YOU jointly evaluates addressee resolution and the addressee's attitude.
The model receives two synchronized views from the same interaction window:

- Video 1: corner view for Q1 addressee resolution.
- Video 2: 2x2 close-up mosaic for Q2 attitude inference.

The prompt also includes the transcript and participant/layout mappings.

### Base Evaluation Template

```text
You will be given TWO meeting clips from the same interaction window:
- Video 1 (FIRST attached): corner view (for Q1 addressee; use position/layout cues).
- Video 2 (SECOND attached): 2x2 closeup mosaic
  (for Q2 attitude; use per-person facial/body cues).

Task:
Answer TWO VISUAL QUESTION ANSWERING (VQA) questions.

Q1 (single-choice, addressee):
{Q1}

Options:
A, B, C, D, MULTIPLE, UNKNOWN

Q2 (single-choice, attitude):
{Q2}

Options:
SUPPORT, OPPOSE, NEUTRAL, UNCERTAIN

Corner-view meeting layout (use for Q1):
{CORNER_LAYOUT}

2x2 closeup mosaic layout (use for Q2):
{MOSAIC_LAYOUT}

Output format (STRICT JSON, single line, no extra keys):
{"Q1":"<OPTION>","Q2":"<OPTION>"}

Transcript:
{TRANSCRIPT}
```

### Task-aligned CoT Addendum

```text
Think step by step to decide Q1 and Q2.

For Q1 focus only on the corner view during the addressing moment.
Prefer consistent cues such as head and gaze orientation, pointing or directing
hand gestures, body orientation, and immediate visible reactions right after
the addressing moment.

For Q2 focus only on the mosaic view and decide whose attitude is being asked
about before judging attitude.

Supportive cues include nodding, smiling, warm approving affect, forward lean,
and quick affirmative reactions.

Oppositional cues include head shakes, frowns, brow furrow, lip press, tense jaw,
arms crossed, leaning back, dismissive gestures, and clearly negative stance.

Neutral cues include steady attentive gaze, stillness, neutral affect,
and stable listening posture.
```

### Emotional Chain-of-Thought (EoT) Addendum

```text
Follow the Emotional Chain-of-Thought below and think step by step.

Step 1 Understanding context.
Infer what is happening in this interaction window and when the key addressing
moment occurs.

Step 2 Recognizing others' emotions and social signals.
From body orientation, positioning, approach/avoid movements, gaze direction
when visible, and turn-taking patterns, infer who is being addressed in the moment,
while tracking uncertainty when cues are weak.

Step 3 Recognizing self emotions.
Notice any immediate interpretive bias you feel while watching, and acknowledge
uncertainty rather than forcing a confident story.

Step 4 Managing self emotions.
Regulate overconfidence and avoid projecting intentions onto participants.
Keep an evidence-first stance and let uncertainty remain when the video does not
support a clear inference.

Step 5 Influencing others' emotions and generating the final answers.
For Q1, decide the addressee based on the dominant addressing pattern in the
corner view across the whole window.

For Q2, decide the attitude based on the dominant facial and upper-body affect
patterns in the mosaic across the whole window.
```

---

## CONSENSUS

CONSENSUS evaluates group-level consensus quality and, conditionally,
the participant showing weak buy-in or hidden disagreement.

Both questions refer to the same 2x2 close-up mosaic video and the same transcript window.

### Base Evaluation Template

```text
You will be given ONE meeting clip: a 2x2 closeup mosaic video.
Both questions (Q1 and Q2) refer to the SAME attached mosaic video.

Task:
Answer TWO VISUAL QUESTION ANSWERING (VQA) questions based primarily
on the observed visual behavior in the video.

Q1 (group consensus type; single-choice):
What is the quality of group consensus at this moment?

Options:
TRUE_CONSENSUS, PSEUDO_CONSENSUS, NO_CONSENSUS, UNCERTAIN

Q2 (dissenter; single-choice with condition):
If pseudo-consensus, who appears to have weak buy-in or hidden disagreement?

Options:
A, B, C, D, NONE

2x2 closeup mosaic layout (IMPORTANT for Q1 & Q2):
{MOSAIC_LAYOUT}

Output format (STRICT JSON, single line, no extra keys):
{"Q1":"<OPTION>","Q2":"<OPTION>"}

Transcript (same window; may be empty):
{TRANSCRIPT}
```

### Task-aligned CoT Addendum

```text
Think step by step to decide Q1 and Q2.

First identify one or two clear reaction moments such as synchronized nods,
affect shifts, or clear disagreement signals.

For Q1 choose the option that best matches the visuals.
Remember the label meanings.

For Q2, if Q1 is PSEUDO_CONSENSUS and there is exactly one clearly standout
subtle dissenter, then choose that agent.

Otherwise, if there are multiple candidates or the mapping among A, B, C, and D
is ambiguous, Q2 must be NONE.
```

### Emotional Chain-of-Thought (EoT) Addendum

```text
Follow the Emotional Chain-of-Thought below and think step by step.

Step 1 Understanding context.
Infer what is being discussed or decided in this moment and when the key
reactions occur.

Step 2 Recognizing others' emotions.
From visible cues such as facial affect, gaze, posture, head movement,
engagement, and timing, infer the likely emotional tendencies of each visible
participant, while tracking uncertainty when cues are weak.

Step 3 Recognizing self emotions.
Notice your own immediate interpretive bias or emotional pull while observing
the scene, and explicitly acknowledge uncertainty internally rather than forcing
a confident story.

Step 4 Managing self emotions.
Regulate overconfidence and avoid projecting emotions onto participants.
Keep a calm, evidence-first stance and let uncertainty remain when the video
does not support a clear inference.

Step 5 Influencing others' emotions and generating the final answers.
Synthesize the emotionally informed visual evidence into the best Q1 label
describing the group dynamic.

For Q2, select a dissenter only if one participant stands out clearly;
otherwise NONE.
```

---

## Prompting Variants

The main evaluation uses three prompt variants:

- **No Prompt**: the base task-specific evaluation template only.
- **Task-aligned CoT**: the base template plus the corresponding Task-aligned CoT addendum.
- **EoT**: the base template plus the corresponding Emotional Chain-of-Thought addendum.

A separate **Naive-CoT** diagnostic used a generic step-by-step instruction without
task-specific social-evidence guidance.

---

## Output Spaces

### STATE

```text
DISENGAGED_WITHDRAWAL
HESITATION
CONFUSED_BEWILDERMENT
COGNITIVE_CONFLICT
SUPPORTIVE_ENDORSEMENT
FOCUSED_LISTENING
ACTIVE_ENGAGEMENT
```

### YOU Q1

```text
A
B
C
D
MULTIPLE
UNKNOWN
```

### YOU Q2

```text
SUPPORT
OPPOSE
NEUTRAL
UNCERTAIN
```

### CONSENSUS Q1

```text
TRUE_CONSENSUS
PSEUDO_CONSENSUS
NO_CONSENSUS
UNCERTAIN
```

### CONSENSUS Q2

```text
A
B
C
D
NONE
```

---

## Evaluation Input Mapping

The task-specific media configuration is:

- **STATE**: target-participant close-up video + same-window transcript.
- **YOU Q1**: corner-view video.
- **YOU Q2**: 2x2 close-up mosaic video.
- **CONSENSUS Q1/Q2**: shared 2x2 close-up mosaic video.

For YOU and CONSENSUS, participant identity is supplied through the instance-specific
layout/mapping block included in the prompt.
