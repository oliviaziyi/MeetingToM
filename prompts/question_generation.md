# Question-Generation and Refinement Prompts

This file documents the task-specific prompts used during MeetingToM benchmark construction.
These construction-stage prompts are distinct from the prompts used for final model evaluation.

The prompt bodies below are reproduced verbatim from the recovered generation/refinement code.
Short notes outside the prompt blocks explain how construction-stage outputs relate to the final released benchmark.

## STATE

**Construction-stage note.** This prompt corresponds to the STATE transition-generation/refinement stage.
It produces annotations for EARLY and LATE temporal windows. These window-level annotations were subsequently
converted into independent 5-second STATE evaluation records in the released benchmark.

### Prompt

```text
You are labeling NONVERBAL mental/interactional states in a meeting clip. Focus on visible behavior (gaze, posture, gestures, facial expression, turn-taking cues). Do NOT rely on speech content; speech can be polite/misleading.

LABEL SET (choose exactly ONE per question):
- DISENGAGED_WITHDRAWAL:
  Low effort, attention drifting away; restless shifting, looking away/down repeatedly, fidgeting, signs of impatience or psychological withdrawal.
- HESITATION:
  Transitional moment before acting/speaking; delayed response, disfluency-like pre-speech cues, gaze aversion right before taking a turn, tentative micro-movements.
- CONFUSED_BEWILDERMENT:
  Cognitive disequilibrium/overload; puzzled facial expression, furrowed brows, head tilt, scanning others for clarification, stalled comprehension.
- COGNITIVE_CONFLICT:
  Active resistance/challenge; visible disagreement cues (head shake, negating gestures), confrontational posture, interruption attempts, tense expression while still task-oriented.
- SUPPORTIVE_ENDORSEMENT:
  Agreement/validation; nods, smiles, "alignment" posture, affirming gestures, encouraging attention toward another speaker.
- FOCUSED_LISTENING:
  Attentive listening with low outward expression; steady gaze to speaker, minimal gestures, posture oriented to information intake.
- ACTIVE_ENGAGEMENT:
  Driving the interaction; frequent initiative, animated gestures, taking the floor, leaning in, directing gaze/gestures to manage discussion.

IMPORTANT DISAMBIGUATION:
- FOCUSED_LISTENING vs SUPPORTIVE_ENDORSEMENT:
  Endorsement has clear positive alignment signals (nodding, smiles, brief affirmations). Focused listening is attentive but neutral.
- ACTIVE_ENGAGEMENT vs COGNITIVE_CONFLICT:
  Conflict includes disagreement/resistance cues; Active engagement can be energetic but not necessarily opposing.
- CONFUSED_BEWILDERMENT vs HESITATION:
  Confusion looks like not understanding; Hesitation looks like "about to respond/act" but delayed.

TASK:
You will see images from TWO time windows:
- EARLY window: use ONLY EARLY images to answer Q1
- LATE window: use ONLY LATE images to answer Q2

WHO TO LABEL:
Use the TARGET_AGENT letter given in INPUT_JSON (A/B/C/D/E). Images are captioned with agent letters to help you stay consistent.

OUTPUT FORMAT:
Return ONLY a single JSON object, with EXACTLY 2 questions:

{
  "skip": false,
  "reason": "",
  "quality": "high|ok|skip",
  "quality_score": 0.0-1.0,
  "questions": [
    {
      "id":"Q1",
      "format":"short_answer",
      "question":"What is TARGET_AGENT's state in the EARLY window?",
      "options": null,
      "answer":{"option_id":null,"text":"<ONE_LABEL_FROM_SET>"},
      "rationale":"short evidence-based rationale from visible nonverbal cues",
      "evidence_ts_rel":[EARLY_START,EARLY_END],
      "difficulty":"easy|medium|hard"
    },
    {
      "id":"Q2",
      "format":"short_answer",
      "question":"What is TARGET_AGENT's state in the LATE window?",
      "options": null,
      "answer":{"option_id":null,"text":"<ONE_LABEL_FROM_SET>"},
      "rationale":"short evidence-based rationale from visible nonverbal cues",
      "evidence_ts_rel":[LATE_START,LATE_END],
      "difficulty":"easy|medium|hard"
    }
  ]
}

If the TARGET_AGENT is not visible enough to decide in either window, set skip=true and explain why in reason.
```

---

## YOU

**Construction-stage note.** The generation-stage prompt includes addressee resolution, attitude, and a local-power component.
The final released YOU benchmark retains the addressee-resolution and attitude tasks; local-power items are not part of the released benchmark.

### Prompt

```text
# Prompt for Task 2: Addressee ("you") Resolution + Attitude + Local Power (FRAME-AWARE)

You will receive:
(1) A SET OF STILL FRAMES (images) sampled from a ~50–70s meeting clip. Frames may include multiple views (e.g., corner + closeup).
    Participants are visually labeled as A/B/C/D/(optional E) in the frames (burn-in labels or mosaic view). There may be NO transcript and NO reliable audio.
(2) A JSON "bundle" with clip metadata and multimodal annotations. The bundle MAY include:
    - clip_id, session_id
    - clip_start_sec_abs (absolute time on session timeline; optional)
    - clip_duration_sec
    - you_marks: list of second-person token occurrences extracted from AMI words.xml
      (each item may include speaker, token, t0/t1, word_id, attrs; timestamps are typically ABSOLUTE unless stated otherwise)
    - evidence: event lists from sources such as focus/headGesture/handGesture/movement/dialogueActs/disfluency/segments/decision/argumentation_*
(3) (Optional) A frame_manifest in the input JSON that maps each provided frame to an approximate clip-relative time and view.
    If frame_manifest is present, you MUST use it when choosing evidence windows and describing what is visible.

IMPORTANT INPUT REALITY (must follow):
- You do NOT receive the full continuous video; you receive sparse snapshots (frames).
- Do NOT assume you can hear audio or identify exact words spoken from frames.
- Never fabricate quotes or exact spoken content. Avoid claiming overlap/interruptions/pace/backchannels unless clearly supported by frames.
- When evidence is insufficient, prefer UNKNOWN/UNCERTAIN with low confidence rather than guessing.

Important labeling rule:
- Use participant label "E" ONLY if an "E" label is visibly present in the frames.
- If the frames show only four labels, do NOT use "E" anywhere; prefer UNKNOWN/MULTIPLE/UNCERTAIN.

Goal:
Create high-quality QA items for:
- (2a) Addressee resolution for a focal second-person reference ("you/your/you guys" family)
- (2b) Addressee attitude toward the focal speaker’s local intent/proposal/request
- (2c) Local interactional power of the focal speaker
Ground everything strictly in what is INSPECTABLE from the PROVIDED FRAMES (visible non-verbal cues + frame-supported interaction cues).

Hard rules (must follow):
- NO fabricated quotes. Never output exact spoken sentences. If referring to speech, describe it abstractly and only when frame-supported.
- Questions must be answerable by INSPECTING THE PROVIDED FRAMES alone. Do NOT mention bundle/index fields (e.g., word_id, you_marks, ps/ts, trigger_kind, debug_counts) in question text or options.
- Every non-trivial claim MUST be supported by timestamped evidence windows consistent with the provided frames (and frame_manifest if present).
- Use CLIP-RELATIVE time in seconds: t=0.0 is the first moment of the clip window.
- If clip_start_sec_abs exists and bundle times are absolute, you MUST convert:
    t_rel = t_abs - clip_start_sec_abs
  and report evidence primarily with rel times. If clip_start_sec_abs is missing, assume provided times are already clip-relative.
- If evidence is insufficient/ambiguous, prefer UNKNOWN/UNCERTAIN with low confidence rather than guessing.

Skip policy (pipeline safety):
- If bundle.you_marks is missing/empty OR you cannot align any plausible focal moment to the provided frames,
  output ONLY:
  {"skip": true, "reason": "..."}.

Key definitions:
- FOCAL_YOU: ONE chosen second-person occurrence that is inside the clip window and has the clearest addressee cues and/or interactional consequences.
- FOCAL_SPEAKER: the participant label (A/B/C/D/E) who produced that FOCAL_YOU.
- ADDRESSEE: who the focal speaker is addressing/referencing with the second-person reference.

Label spaces:
(2a) Addressee:
- A | B | C | D | E | MULTIPLE | UNKNOWN

(2b) Addressee attitude toward focal speaker’s local intent/proposal/request:
- SUPPORT | OPPOSE | NEUTRAL | UNCERTAIN
Notes:
- Judge the ADDRESSEE’s attitude toward what the FOCAL_SPEAKER is trying to get done around the focal moment.
- If addressee reaction is not frame-observable, choose UNCERTAIN.

(2c) Local interactional power of the focal speaker (in THIS clip window):
- HIGH | MEDIUM | LOW | UNCERTAIN
Notes:
- Power is local interactional control/influence, not job title.

Bundle usage policy (important):
- Treat bundle annotations as NOISY HINTS to prioritize where to inspect.
- Frame-visible evidence is the ground truth.
- You may use bundle.you_marks ONLY to select the focal moment (who/when) because frames may not reveal the exact token.
  However, addressee / attitude / power decisions MUST be justified primarily by frame-visible cues (gaze, pointing, orientation, reactions).
- Never “answer from the bundle” when frame evidence does not support it; use UNKNOWN/UNCERTAIN with low confidence.

Multimodal reasoning requirements:
- Non-verbal cues (prioritized): gaze direction, pointing/hand direction, body orientation, nod/shake, facial affect, posture shifts, engagement/withdrawal.
- Interactional cues ONLY if frame-visible: who appears to respond next (attention shift), visible floor-holding posture, visible uptake/compliance actions.
- For each core decision (2a/2b/2c), include timestamped evidence; at least one non-verbal cue whenever visible.

Step-by-step procedure:
1) Read bundle.clip_meta (session_id/clip_id/clip_duration_sec/clip_start_sec_abs if present) and frame_manifest (if present).
2) Identify at least TWO active participants in the frames (speaking posture OR clearly reacting/being addressed).
3) Select ONE FOCAL_YOU from bundle.you_marks:
   3.1) Prefer occurrences whose timestamps fall inside the clip window.
        If timestamps are absolute: keep those with t0_abs in [clip_start_sec_abs, clip_start_sec_abs + clip_duration_sec].
   3.2) Prefer candidates whose focal moment can be aligned to provided frames (via frame_manifest or by proximity to sampled times).
   3.3) If none can be aligned, return skip=true.
4) Define a local analysis window around the focal moment (clip-relative):
   - window = [max(0, t0_rel - 6.0), min(clip_duration_sec, t1_rel + 12.0)]
5) Task 2a (Addressee resolution):
   - Decide who the focal speaker is primarily addressing from frame-visible cues.
   - If more than one is clearly addressed, label MULTIPLE.
   - If unclear, label UNKNOWN.
   - Provide candidate_scores for A/B/C/D/E/MULTIPLE/UNKNOWN (0–1). Scores should be comparable; normalization is encouraged.
   - Evidence requirements:
     * >=2 distinct cues total, with >=1 non-verbal cue if visible
     * plus >=1 interaction cue when possible from frames
6) Task 2b (Addressee attitude):
   - Identify the addressee’s most direct frame-visible reaction within the analysis window.
   - Classify SUPPORT/OPPOSE/NEUTRAL/UNCERTAIN.
   - Evidence requirements:
     * >=1 non-verbal cue (if visible) + >=1 interaction cue (if possible from frames)
7) Task 2c (Focal speaker power):
   - Judge focal speaker’s local interactional power in THIS window.
   - Evidence should reference at least one frame-visible indicator:
     - initiative/framing posture (addressing group, directing attention with gesture)
     - sustained floor-holding posture across adjacent frames (if available)
     - uptake by others visible as attention alignment or compliance actions
8) Generate EXACTLY 6 QA items:
   - Q1–Q2: addressee_classification (MCQ single-best-answer; exactly 4 options)
   - Q3–Q4: attitude_classification or attitude_reasoning (one MCQ + one short-answer recommended)
   - Q5: power_classification (MCQ single-best-answer; exactly 4 options)
   - Q6: evidence_localization (MCQ or short-answer; point to the best time window supported by frames)
   Constraints:
   - At least 3 questions must directly involve identifying the addressee OR distinguishing MULTIPLE/UNKNOWN.
   - At least 2 questions must require citing non-verbal evidence (gaze/gesture/posture).
   - For MCQ about addressee: options must be drawn from ACTIVE participants when possible; include UNKNOWN or MULTIPLE if plausible; keep exactly 4.
   - Every question MUST include:
     answer key, 1–3 sentence rationale (no quotes), evidence_ts_rel [t_start,t_end], difficulty.
   - Questions must NOT mention bundle/index fields.

Output format:
Return JSON ONLY (no extra text). Use this schema exactly:

{
  "skip": false,

  "clip_meta": {
    "session_id": "string|null",
    "clip_id": "string|null",
    "clip_duration_sec": number,
    "clip_start_sec_abs": number|null,
    "active_participants": ["A","B","C","D","E"],
    "notes": "optional"
  },

  "focal_you": {
    "speaker": "A|B|C|D|E",
    "token": "you|your|you guys|other|null",
    "t0_rel": number,
    "t1_rel": number,
    "t0_abs": number|null,
    "t1_abs": number|null,
    "word_id": "string|null"
  },

  "analysis_window": {"t_start_rel": number, "t_end_rel": number},

  "task2a_addressee": {
    "label": "A|B|C|D|E|MULTIPLE|UNKNOWN",
    "confidence": 0.0,
    "candidate_scores": {"A":0.0,"B":0.0,"C":0.0,"D":0.0,"E":0.0,"MULTIPLE":0.0,"UNKNOWN":0.0},
    "evidence": [
      {"type":"nonverbal|interaction|annotation", "ts_rel":[number,number], "ts_abs":[number,number] | null, "detail":"..."}
    ]
  },

  "task2b_attitude": {
    "label": "SUPPORT|OPPOSE|NEUTRAL|UNCERTAIN",
    "confidence": 0.0,
    "evidence": [
      {"type":"nonverbal|interaction|annotation", "ts_rel":[number,number], "ts_abs":[number,number] | null, "detail":"..."}
    ]
  },

  "task2c_power": {
    "label": "HIGH|MEDIUM|LOW|UNCERTAIN",
    "confidence": 0.0,
    "evidence": [
      {"type":"nonverbal|interaction|annotation", "ts_rel":[number,number], "ts_abs":[number,number] | null, "detail":"..."}
    ]
  },

  "questions": [
    {
      "id": "Q1",
      "type": "addressee_classification|attitude_classification|attitude_reasoning|power_classification|evidence_localization",
      "format": "mcq_single|short_answer",
      "question": "string",
      "options": [
        {"id":"A","text":"..."},
        {"id":"B","text":"..."},
        {"id":"C","text":"..."},
        {"id":"D","text":"..."}
      ] | null,
      "answer": {
        "option_id": "A|B|C|D|null",
        "text": "string (for short_answer: key points)"
      },
      "rationale": "1–3 sentences grounded in frame-visible cues (no quotes).",
      "evidence_ts_rel": [number, number],
      "evidence_ts_abs": [number, number] | null,
      "difficulty": "easy|medium|hard"
    }
  ],

  "quality_checks": {
    "no_quotes_used": true,
    "all_questions_answerable_from_video": true,
    "all_questions_have_evidence": true,
    "uncertain_used": true|false
  }
}

Uncertainty handling:
- If addressee is unclear, use UNKNOWN with low confidence and create at least one question that probes ambiguity (e.g., which evidence would disambiguate).
- If attitude/power cannot be supported, use UNCERTAIN and keep rationale evidence-based.
```

---

## CONSENSUS

**Construction-stage note.** This generation-stage prompt creates a broader set of candidate QA items around consensus quality
and hidden dissent. The final released CONSENSUS benchmark uses the canonical consensus-quality and hidden-dissenter questions.

### Prompt

```text
# Prompt for Task 3 (v3): Consensus Quality & Hidden Dissent in 50–70s Meeting Clips (FRAME-AWARE)

You will receive:
(1) A SET OF STILL FRAMES (images) sampled from a 50–70s meeting clip. Frames may include multiple views (e.g., corner + closeup).
    Participants are visually labeled A/B/C/D(/E) in the frames (burn-in labels or mosaic). There may be NO transcript and NO reliable audio.
(2) An INDEX/BUNDLE JSON for this clip (from a script). It may include: session_id, clip_id, clip_start_sec_abs, clip_duration_sec,
    trigger_time, trigger_kind, trigger_speaker, scores (pseudo_score/true_score), and evidence lists (agree_hits, nonverbal_pos/neg/polite,
    clarify_event_hits, clarify_word_hits, debug_counts), and possibly a "confidence" hint like strong/weak.
(3) (Optional) A frame_manifest in the input JSON that maps each provided frame to an approximate clip-relative time and view.
    If frame_manifest is present, you MUST use it when choosing evidence windows and describing what is visible.

IMPORTANT INPUT REALITY (must follow):
- You do NOT receive the full continuous video; you receive sparse snapshots (frames).
- Do NOT assume you can observe precise turn-taking, overlap/interruptions, hedging, backchannels, pace changes, or silence-at-expected-moments.
- Audio is NOT available/reliable. Never infer exact spoken sentences. Avoid claiming specific speech acts unless clearly supported by frame-visible cues.
- When evidence is insufficient/ambiguous, be conservative: use UNCERTAIN + low confidence rather than guessing.

Goal:
Generate high-quality questions that test understanding of LOCAL GROUP CONSENSUS QUALITY and hidden dissent,
grounded in observable evidence from the PROVIDED FRAMES:
- frame-visible interaction cues: coordinated attention shifts, who appears to hold the floor (speaking posture), visible uptake/compliance actions,
  participation drop visible as disengaged posture or attention withdrawal.
- non-verbal cues: gaze convergence/divergence, head nod/shake, facial affect, posture openness/closure, hand gestures, disengagement.

This task is GROUP-level decision alignment (not individual emotion labeling).

Hard rules (must follow):
- NO fabricated quotes. Never output exact spoken sentences. If referring to speech, describe it abstractly and only when frame-supported.
- Questions must be answerable by INSPECTING THE PROVIDED FRAMES alone. Do NOT reference index fields (pseudo_score/true_score/trigger_kind/etc.) in question text/options.
- Every non-trivial claim MUST be supported by timestamped evidence windows consistent with the provided frames (and frame_manifest if present).
- Use CLIP-RELATIVE time in seconds: t=0.0 is the first moment of the clip window.
- If clip_start_sec_abs is provided: abs_t = clip_start_sec_abs + rel_t.
- Use participant label "E" ONLY if an "E" label is visibly present in the frames.
- If the frames show only four labels, do NOT use "E" anywhere (including hidden_dissenter and active_speakers). Prefer NONE / UNCERTAIN where appropriate.

Label spaces:
Local consensus label (within this clip window):
- NO_CONSENSUS
- TRUE_CONSENSUS
- PSEUDO_CONSENSUS
- UNCERTAIN

Hidden dissenter (ONLY if local label is PSEUDO_CONSENSUS; otherwise MUST be NONE):
- A, B, C, D, E, NONE

Definitions (operational, frame-aware):
- NO_CONSENSUS: no clear convergence is visible; attention/engagement remains split or unresolved across frames.
- TRUE_CONSENSUS: convergence appears substantive; multiple participants show aligned attention/positive engagement toward the same outcome across frames.
- PSEUDO_CONSENSUS: surface convergence appears (little/no visible disagreement), but at least one participant shows frame-visible reluctance /
  lack of understanding / weak buy-in (e.g., minimal acknowledgment posture, gaze aversion, closed posture, disengagement near the convergence moment).
- UNCERTAIN: frames do not contain enough evidence to determine consensus quality.

Index usage policy:
- Treat index/bundle as a noisy hint to prioritize where to inspect (e.g., trigger_time ±10s).
- Frame-visible evidence is the ground truth. If index suggests a label but you cannot see supporting cues in frames, output UNCERTAIN or lower confidence.

Strong/weak hint policy (if present):
- strong/weak is ONLY a search hint (where to look first), NOT a decision rule.
- You MUST still verify using frame-visible cues.

Task steps:
1) Read INDEX/BUNDLE JSON (if present) and extract session_id, clip_id, clip_duration_sec, clip_start_sec_abs (optional), trigger_time (optional),
   and frame_manifest (if present).
2) Identify at least TWO active speakers/actors (A/B/C/D/E) based on frame-visible participation (speaking posture, gestures, attention).
3) Decide ONE local consensus label for the group and set consensus_confidence (0–1).
4) If consensus_label == PSEUDO_CONSENSUS:
   - choose exactly ONE hidden_dissenter from {A,B,C,D,E} and set dissenter_confidence (0–1).
   Else:
   - hidden_dissenter MUST be "NONE" and dissenter_confidence MUST be 0.
5) Identify key moments (frame-aware):
   - t_consensus_rel: the moment where convergence (real or surface) is most evident, OR null if none.
   - If PSEUDO_CONSENSUS: t_contradiction_rel: a moment showing mismatch (e.g., resistant posture/gaze aversion/disengagement),
     OR null if not clearly visible.
6) Write an evidence summary with timestamped cues:
   - supporting_cues: 2–5 cues that support your consensus label
   - counter_cues: 0–3 cues that push against it / introduce ambiguity
   Each cue must be aligned to frames and use a reasonable window (prefer 8–20s if frame-sparse; avoid fake precision).

Question generation (exactly 5 questions; avoid redundancy):
Generate exactly 5 questions for dataset creation, designed to be answerable from the provided frames alone.

Required composition:
- Q1–Q2: consensus_classification (MCQ single-best-answer, exactly 4 options)
  - Q1 MUST ask for the overall consensus label.
  - Q2 MUST stress TRUE vs PSEUDO discrimination (but include NO_CONSENSUS and/or UNCERTAIN as distractors to keep 4 options).
- Q3: reasoning (short_answer) requiring 2–3 evidence-backed cues, including at least ONE non-verbal cue.
- Q4: evidence_localization (mcq_single OR short_answer): ask for the best time window supported by frames.
- Q5: conditional:
  - If consensus_label == PSEUDO_CONSENSUS:
    Q5 MUST be a hidden_dissenter identification question (MCQ single-best-answer, exactly 4 options).
    Options rule: choose 3 plausible participants from active_speakers + 1 option "NONE/UNCERTAIN" (as text). Keep exactly 4.
  - Else (TRUE/NO/UNCERTAIN):
    Q5 MUST be counterfactual_or_boundary reasoning:
    Ask what observable frame-visible change would most likely flip the label (e.g., from TRUE→PSEUDO, NO→TRUE). Can be mcq_single or short_answer.

Quality constraints for all questions:
- No index terms in question text/options.
- Each question MUST include:
  - answer key
  - rationale (1–3 sentences grounded in observable frame cues, no quotes)
  - evidence_ts_rel: [t_start, t_end] with a reasonable window (prefer 8–20s if frame-sparse)
  - evidence_ts_abs: compute if clip_start_sec_abs is available, else null
  - difficulty: easy|medium|hard
- At least 3 questions must directly test TRUE vs PSEUDO or hidden dissent evidence (when applicable).
- If the clip is ambiguous, questions should reflect ambiguity (e.g., ask what evidence would disambiguate) rather than forcing a confident label.

Output JSON only (no extra text). Use this schema exactly:
{
  "clip_meta": {
    "session_id": "string|null",
    "clip_id": "string|null",
    "clip_duration_sec": number,
    "clip_start_sec_abs": number|null,
    "active_speakers": ["A","B","C","D","E"],
    "consensus_label": "NO_CONSENSUS|TRUE_CONSENSUS|PSEUDO_CONSENSUS|UNCERTAIN",
    "consensus_confidence": 0.0-1.0,
    "hidden_dissenter": "A|B|C|D|E|NONE",
    "dissenter_confidence": 0.0-1.0,
    "index_hints_used": {
      "trigger_time_abs_or_rel": number|null,
      "used_as_hint": true|false,
      "note": "short"
    },
    "notes": "optional"
  },
  "key_moments": {
    "t_consensus_rel": number|null,
    "t_contradiction_rel": number|null,
    "evidence_ts_rel": [number, number]
  },
  "evidence_summary": {
    "supporting_cues": [
      {"t_rel":[number,number], "modality":"verbal|nonverbal|interaction", "cue":"string"}
    ],
    "counter_cues": [
      {"t_rel":[number,number], "modality":"verbal|nonverbal|interaction", "cue":"string"}
    ]
  },
  "questions": [
    {
      "id": "Q1",
      "type": "consensus_classification|reasoning|counterfactual|evidence_localization|hidden_dissenter",
      "format": "mcq_single|short_answer",
      "question": "string",
      "options": [
        {"id":"A","text":"..."},
        {"id":"B","text":"..."},
        {"id":"C","text":"..."},
        {"id":"D","text":"..."}
      ] | null,
      "answer": {
        "option_id": "A|B|C|D|null",
        "text": "string"
      },
      "rationale": "1–3 sentences grounded in observable frame cues (no quotes).",
      "evidence_ts_rel": [number, number],
      "evidence_ts_abs": [number, number] | null,
      "difficulty": "easy|medium|hard"
    }
  ],
  "quality_checks": {
    "no_quotes_used": true,
    "all_questions_answerable_from_video": true,
    "all_questions_have_evidence": true,
    "uncertain_used": true|false
  }
}

Uncertainty handling:
- If consensus quality is unclear, set consensus_label=UNCERTAIN with low confidence.
- Still generate 5 questions, but favor ambiguity-aware reasoning and evidence-localization questions that would disambiguate TRUE vs PSEUDO vs NO.
```
