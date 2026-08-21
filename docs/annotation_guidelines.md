# MeetingToM Annotation Guidelines

This document specifies the annotation criteria used for the released MeetingToM benchmark. It is intentionally limited to **how benchmark labels are interpreted and assigned**. The dataset construction workflow, GPT-assisted candidate generation, screening stages, annotator preparation, calibration, and release conversion are documented separately in [`generation_protocol.md`](generation_protocol.md).

## 1. Annotation Scope and Interpretation

MeetingToM evaluates meeting-grounded social reasoning at three levels:

1. **STATE** — subject-level mental/interactional state prediction;
2. **YOU** — dyadic-level addressee identification and attitude inference;
3. **CONSENSUS** — group-level consensus-quality and hidden-dissent reasoning.

MeetingToM labels are **protocol-conditioned, evidence-grounded third-person judgments** based on observable behavior and aligned conversational context. When multiple interpretations are plausible, annotators select the label best supported by the evidence in the task-specific observation window. Adjudication provides the reference label used for benchmark scoring.

### 1.1 Evidence Sources

Depending on the task, relevant evidence may include:

- facial expression and visible affect;
- gaze and head orientation;
- posture and body orientation;
- hand and arm gestures;
- movement and response timing;
- turn-taking behavior;
- immediate reactions to other participants;
- aligned conversational utterances;
- local interaction context.

The relative contribution of visual, linguistic, and interactional evidence is **task- and instance-dependent**. MeetingToM evaluates meeting-grounded social reasoning under multimodal conditions.

### 1.2 General Decision Principles

#### Evidence grounding

Every label should be supported by evidence in the relevant observation window. Annotators should avoid judgments based primarily on presumed personality, formal role, unstated motives, long-term relationships, or stereotypes about social behavior.

#### Multiple converging cues

A single weak cue is rarely sufficient for a strong social-state judgment. Whenever possible, annotators should seek converging evidence across multiple cue types, such as gaze plus posture, facial affect plus head movement, or verbal response plus temporally aligned visible reaction.

Strong, sustained, and temporally aligned evidence may receive greater weight than several weak or incidental cues.

#### Temporal alignment

Evidence must correspond to the interval defined by the benchmark record.

- **STATE:** use the single released 5-second window for the record.
- **YOU Q1:** focus on the addressing moment in the corner view.
- **YOU Q2:** focus on the identified addressee's reaction in the aligned interaction window, using the close-up mosaic and local conversational context.
- **CONSENSUS:** focus on the group configuration around the relevant discussion, proposal, or convergence moment.

Behavior substantially outside the target interval should not override the evidence visible within the annotated window.

#### Conservative inference

Do not force a highly specific interpretation when evidence is weak, contradictory, occluded, or unavailable. Use the task-specific uncertainty category when one exists:

- `UNKNOWN` for unresolved addressee identity;
- `UNCERTAIN` for unresolved attitude or consensus quality.

For STATE, construction-stage items with insufficient target visibility or insufficient behavioral evidence were excluded rather than assigned an unsupported label.

#### Verbal and non-verbal evidence

Transcript content may help identify timing, turn-taking, the focal proposal, or the interactional target. Annotators interpret it jointly with visible behavior. In cases of verbal–non-verbal mismatch, the decision should follow the most coherent temporally aligned multimodal pattern.

---

# 2. STATE — Subject-Level Mental/Interactional State

## 2.1 Task Definition

Each released STATE evaluation record contains one short temporal window centered on one target participant. The annotation objective is to select the **dominant observable mental/interactional state** of that target within the window.

The released STATE label space is:

```text
ACTIVE_ENGAGEMENT
SUPPORTIVE_ENDORSEMENT
FOCUSED_LISTENING
COGNITIVE_CONFLICT
CONFUSED_BEWILDERMENT
HESITATION
DISENGAGED_WITHDRAWAL
```

These categories provide an operational description of meeting behavior for benchmark evaluation.

---

## 2.2 ACTIVE_ENGAGEMENT

### Definition

`ACTIVE_ENGAGEMENT` describes a state in which the target is actively contributing to, organizing, or driving the interaction rather than primarily receiving information.

### Typical supporting evidence

Evidence may include:

- taking or sustaining the conversational floor;
- animated explanatory, illustrative, or directive gestures;
- forward-oriented posture;
- active gaze management across other participants;
- visible initiative in directing attention or advancing the discussion;
- temporally coordinated speech and purposeful gesture;
- other participants visibly orienting toward the target while the target leads the exchange.

### Exclusion criteria

Speaking or movement alone is insufficient for `ACTIVE_ENGAGEMENT`. Prefer another label when:

- the participant is attentive but primarily listening;
- the dominant behavior is agreement with another speaker rather than interactional initiative;
- the activity is primarily oppositional or corrective;
- the visible movement is unrelated to the meeting interaction.

### Boundary: ACTIVE_ENGAGEMENT vs COGNITIVE_CONFLICT

Both may involve high behavioral energy and strong task involvement.

- Choose `ACTIVE_ENGAGEMENT` when the dominant pattern is contribution, explanation, coordination, or interaction management without clear opposition.
- Choose `COGNITIVE_CONFLICT` when the dominant pattern is rejection, skepticism, correction, resistance, or challenge.

---

## 2.3 SUPPORTIVE_ENDORSEMENT

### Definition

`SUPPORTIVE_ENDORSEMENT` describes observable positive alignment, agreement, validation, or encouragement toward another participant's contribution.

### Typical supporting evidence

Evidence may include:

- repeated or clearly affirmative nodding;
- warm or approving facial affect;
- smiling temporally aligned with another participant's contribution;
- open and receptive posture;
- quick affirmative reactions after a proposal or statement;
- brief verbal affirmation consistent with visible positive alignment.

### Exclusion criteria

Simple attentive neutrality remains `FOCUSED_LISTENING`. A single small acknowledgment nod is insufficient for endorsement.

### Boundary: SUPPORTIVE_ENDORSEMENT vs FOCUSED_LISTENING

The critical distinction is the presence of **clear positive alignment**.

- `SUPPORTIVE_ENDORSEMENT`: positive affect or repeated affirmative behavior is visible.
- `FOCUSED_LISTENING`: attention is sustained, but positive or negative stance evidence is insufficient.

Repeated nodding, a temporally aligned smile, or another clear positive cue strengthens an endorsement judgment.

---

## 2.4 FOCUSED_LISTENING

### Definition

`FOCUSED_LISTENING` describes attentive, task-oriented reception with no sufficiently strong positive or negative stance signal.

### Typical supporting evidence

Evidence may include:

- sustained gaze toward the current speaker, screen, or shared object;
- stable upright or task-oriented posture;
- limited but responsive movement;
- neutral facial affect;
- sparse acknowledgment nods that do not clearly signal agreement;
- consistent attention across the observation window.

### Exclusion criteria

Do not select `FOCUSED_LISTENING` when:

- clear positive alignment is present;
- attention persistently drifts away from the interaction;
- the participant is actively taking or directing the floor;
- clear opposition, comprehension difficulty, or transition-to-speech hesitation dominates the interval.

### Boundary: FOCUSED_LISTENING vs DISENGAGED_WITHDRAWAL

Stillness alone does not imply disengagement.

- `FOCUSED_LISTENING` requires maintained task orientation.
- `DISENGAGED_WITHDRAWAL` requires sustained evidence that attention or participation has moved away from the interaction.

---

## 2.5 COGNITIVE_CONFLICT

### Definition

`COGNITIVE_CONFLICT` describes observable disagreement, skepticism, resistance, or active challenge while the target remains engaged with the task.

### Typical supporting evidence

Evidence may include:

- head shaking or other rejection signals;
- furrowed brow accompanied by oppositional behavior;
- lip press or tense jaw;
- defensive or distancing posture;
- dismissive or negating gestures;
- interruption or corrective behavior;
- visible reaction inconsistent with the position being advanced;
- explicit disagreement when it is aligned with the observed behavioral stance.

### Exclusion criteria

Conflict should be supported by an oppositional pattern rather than a generic frown, crossed arms, or another isolated cue.

### Boundary: COGNITIVE_CONFLICT vs CONFUSED_BEWILDERMENT

The key distinction is the function of the observable uncertainty or negative affect.

- `COGNITIVE_CONFLICT`: behavior is primarily rejecting, challenging, or skeptical.
- `CONFUSED_BEWILDERMENT`: behavior is primarily searching, clarifying, or indicating difficulty understanding.

---

## 2.6 CONFUSED_BEWILDERMENT

### Definition

`CONFUSED_BEWILDERMENT` describes observable difficulty understanding, integrating, or resolving the information in the current interaction.

### Typical supporting evidence

Evidence may include:

- puzzled or searching facial expression;
- furrowed brow combined with scanning behavior;
- head tilt;
- looking between participants as if seeking clarification;
- self-touch around the chin or forehead during an uncertain moment;
- stalled comprehension;
- clarification-oriented reaction or response.

### Exclusion criteria

A pause before speaking is better treated as `HESITATION` unless the surrounding behavior indicates comprehension difficulty.

### Boundary: CONFUSED_BEWILDERMENT vs HESITATION

- `CONFUSED_BEWILDERMENT`: uncertainty concerns **what is being understood**.
- `HESITATION`: uncertainty concerns **whether or how to respond or act**.

---

## 2.7 HESITATION

### Definition

`HESITATION` describes a transitional pause or aborted initiation immediately before speaking, acting, or taking a conversational turn.

### Typical supporting evidence

Evidence may include:

- delayed response after a turn becomes available;
- mouth opening and closing before speech;
- a gesture beginning and then stopping;
- brief gaze aversion immediately before re-engagement;
- partial forward movement followed by withdrawal;
- visible uncertainty around turn entry;
- tentative or disfluent speech initiation when aligned with visible hesitation.

### Exclusion criteria

Sustained confusion, stable neutral listening, and general low engagement should be assigned to their corresponding categories rather than `HESITATION`.

### Boundary principle

Hesitation is temporally **transitional**. It should be tied to an imminent, attempted, delayed, or aborted response rather than a persistent state of uncertainty.

---

## 2.8 DISENGAGED_WITHDRAWAL

### Definition

`DISENGAGED_WITHDRAWAL` describes sustained reduction in attention, participation, or visible investment in the ongoing interaction.

### Typical supporting evidence

Evidence may include:

- repeated or sustained gaze away from relevant speakers or shared material;
- prolonged low-reactivity posture;
- leaning away from the interaction;
- unrelated fidgeting or object manipulation;
- absence of response to salient interactional events;
- flat or checked-out affect when combined with other disengagement cues.

### Exclusion criteria

Quietness or stillness alone does not indicate disengagement; task orientation distinguishes listening from withdrawal.

### Boundary: DISENGAGED_WITHDRAWAL vs FOCUSED_LISTENING

The critical variable is **task orientation**.

- attentive stillness and stable orientation → `FOCUSED_LISTENING`;
- sustained attentional withdrawal and reduced reactivity → `DISENGAGED_WITHDRAWAL`.

---

## 2.9 STATE Decision Procedure

When several labels are plausible, use the following sequence:

1. **Is the target sufficiently visible?**  
   If not, the item should not be over-interpreted.

2. **Is the target actively taking or managing the floor?**  
   - contribution/coordination → consider `ACTIVE_ENGAGEMENT`;
   - opposition/challenge → consider `COGNITIVE_CONFLICT`.

3. **If primarily receiving information, is there clear positive alignment?**  
   - yes → consider `SUPPORTIVE_ENDORSEMENT`;
   - no, but sustained task-oriented attention → consider `FOCUSED_LISTENING`.

4. **If uncertainty or negative cues dominate, determine their interactional function:**  
   - rejection/skepticism → `COGNITIVE_CONFLICT`;
   - comprehension difficulty → `CONFUSED_BEWILDERMENT`;
   - pre-response transition → `HESITATION`;
   - attentional withdrawal → `DISENGAGED_WITHDRAWAL`.

If the target visibly transitions within the five-second interval, select the state that is most dominant and best supported across the full window. A brief micro-expression should not automatically override the broader interactional pattern.

---

# 3. YOU — Dyadic-Level Referential Reasoning

## 3.1 Task Definition

YOU evaluates two linked forms of dyadic social reasoning:

- **Q1 — Addressee Identification:** who is being addressed by the focal speaker?
- **Q2 — Attitude Inference:** what attitude does the addressee display toward the focal speaker's apparent communicative intent or statement?

The subtasks use different visual perspectives:

- **Q1:** corner view, emphasizing spatial layout, gaze, orientation, and response cues;
- **Q2:** synchronized 2×2 close-up mosaic, emphasizing per-person facial and upper-body reactions.

The final released YOU benchmark contains addressee identification and attitude inference; the earlier local interactional-power component was removed during task cleaning.

---

## 3.2 YOU Q1 — Addressee Identification

### Label space

```text
A
B
C
D
MULTIPLE
UNKNOWN
```

### Core evidence

Annotators should jointly consider:

1. **Speaker gaze direction**  
   Who is the speaker looking toward at or immediately around the addressing moment?

2. **Head and body orientation**  
   Is the speaker consistently oriented toward one participant or toward the group?

3. **Pointing or directing gestures**  
   Does the speaker use a hand, arm, object, or body movement that identifies a recipient?

4. **Immediate recipient response**  
   Who reacts, acknowledges the address, or takes the next relevant turn?

5. **Local turn-taking context**  
   Does the conversational sequence constrain the likely recipient?

No single cue is universally decisive. Gaze, gesture, spatial configuration, and turn-taking should be interpreted together.

### A / B / C / D

Choose a participant identifier when converging evidence supports one specific addressee.

### MULTIPLE

Use `MULTIPLE` when the addressing behavior is directed to more than one participant or to the group collectively.

Group-directed wording alone is not sufficient if the speaker's gaze, body orientation, gesture, or immediate turn-taking clearly singles out one recipient.

### UNKNOWN

Use `UNKNOWN` when the addressee cannot be reliably resolved because:

- the relevant gaze or orientation is not visible;
- the corner-view geometry is insufficient;
- multiple individual candidates remain equally plausible;
- the interaction does not contain enough evidence for a reliable assignment.

`UNKNOWN` denotes insufficient evidence, not merely a subtle interaction.

---

## 3.3 YOU Q2 — Attitude Inference

### Label space

```text
SUPPORT
OPPOSE
NEUTRAL
UNCERTAIN
```

Q2 concerns the **identified addressee's observable stance toward the focal speaker's statement or apparent communicative intent**.

### SUPPORT

#### Definition

The addressee displays observable positive alignment, acceptance, or endorsement.

#### Typical supporting evidence

- affirmative nodding;
- smile or warm approving affect;
- forward-oriented engagement;
- open posture;
- quick positive response;
- verbal affirmation consistent with visible positive alignment.

### OPPOSE

#### Definition

The addressee displays observable disagreement, resistance, rejection, or negative stance.

#### Typical supporting evidence

- head shaking;
- skeptical or negative facial affect;
- lip press or tense jaw;
- leaning back or defensive posture;
- dismissive gesture;
- explicit disagreement when aligned with the visible reaction.

### NEUTRAL

#### Definition

The addressee is observably engaged with the interaction but does not display sufficiently strong positive or negative stance evidence.

#### Typical supporting evidence

- steady attention;
- neutral facial affect;
- stable listening posture;
- no meaningful approach/avoidance shift;
- acknowledgment without clear endorsement.

`NEUTRAL` is not equivalent to missing evidence. It is an observable, non-polar stance.

### UNCERTAIN

#### Definition

The attitude cannot be reliably resolved from the available evidence.

Use `UNCERTAIN` when:

- the relevant participant is not sufficiently visible;
- facial or body cues are too weak or occluded;
- signals are materially contradictory;
- the addressee identity itself cannot be resolved well enough to support attitude inference.

---

## 3.4 YOU Boundary Rules

### SUPPORT vs NEUTRAL

Use `SUPPORT` only when meaningful positive-alignment evidence is present. Attentive listening without clear positive affect or endorsement should remain `NEUTRAL`.

### OPPOSE vs NEUTRAL

A single frown, arm crossing, or backward movement is not automatically opposition. Prefer `OPPOSE` when multiple cues converge or a strong cue is clearly synchronized with the focal statement.

### NEUTRAL vs UNCERTAIN

- `NEUTRAL`: the participant is sufficiently observable and appears non-polar.
- `UNCERTAIN`: the evidence itself is insufficient, occluded, or contradictory.

### Verbal–non-verbal mismatch

If spoken agreement co-occurs with a coherent, sustained visible pattern of tension, avoidance, or rejection, annotate the combined multimodal pattern rather than automatically assigning `SUPPORT`.

At the same time, one isolated ambiguous non-verbal cue should not override otherwise consistent support evidence.

---

# 4. CONSENSUS — Group-Level Consensus Reasoning

## 4.1 Task Definition

CONSENSUS evaluates whether an apparent group-level pattern reflects genuine alignment, surface-level agreement with hidden misalignment, overt lack of consensus, or insufficient evidence.

The released task contains:

- **Q1:** consensus-quality classification;
- **Q2:** conditional identification of a participant showing weak buy-in or hidden disagreement.

Both questions refer to the same synchronized 2×2 close-up mosaic and aligned transcript window.

---

## 4.2 CONSENSUS Q1 — Consensus Quality

### Label space

```text
TRUE_CONSENSUS
PSEUDO_CONSENSUS
NO_CONSENSUS
UNCERTAIN
```

### TRUE_CONSENSUS

#### Definition

The group displays broad, observable alignment with no notable participant-level misalignment signal sufficient to undermine the apparent agreement.

#### Typical supporting evidence

- multiple participants orienting toward the same discussion focus;
- synchronized or repeated affirmative reactions;
- broadly compatible positive or neutral affect;
- coordinated turn-taking consistent with convergence;
- no participant showing persistent visible resistance, withdrawal, or contradictory reaction at the focal moment.

A `TRUE_CONSENSUS` judgment does not require identical behavior from every participant. It requires a group pattern compatible with genuine alignment and no meaningful contradictory signal.

---

### PSEUDO_CONSENSUS

#### Definition

The interaction displays **surface-level or majority agreement**, while at least one participant shows a persistent subtle misalignment pattern suggesting weak buy-in, hesitation, skepticism, avoidance, or concealed disagreement.

#### Required structure

A pseudoconsensus judgment requires evidence at **both** levels:

1. **Group level:** an appearance of agreement, convergence, or acceptance;
2. **Participant level:** evidence that meaningfully contradicts that apparent agreement.

#### Typical misalignment evidence

Potential cues include:

- delayed or noticeably weaker affirmative response relative to others;
- tense or skeptical facial affect;
- persistent gaze avoidance at a salient agreement moment;
- defensive or distancing posture;
- suppressed or minimal response while others visibly align;
- verbal agreement accompanied by a coherent pattern of non-verbal resistance.

`PSEUDO_CONSENSUS` should not be inferred from one fleeting micro-expression, a lack of enthusiasm, or weak visibility alone.

---

### NO_CONSENSUS

#### Definition

The group does not display a coherent consensus pattern, and disagreement, fragmentation, or incompatible positions are overtly observable.

#### Typical supporting evidence

- explicit disagreement;
- visible rejection or competing stances;
- multiple participants displaying incompatible orientations;
- sustained negative reactions;
- competing conversational trajectories;
- fragmented attention or interaction around the focal issue.

The distinction from `PSEUDO_CONSENSUS` is that disagreement in `NO_CONSENSUS` is not primarily hidden beneath an apparent group agreement.

---

### UNCERTAIN

#### Definition

The available evidence is insufficient to reliably distinguish among true consensus, pseudoconsensus, and no consensus.

Use `UNCERTAIN` when:

- critical participants are not sufficiently visible;
- the window does not contain a meaningful convergence or decision moment;
- participant reactions cannot be aligned to the relevant statement;
- multiple consensus interpretations remain comparably plausible.

---

## 4.3 CONSENSUS Q2 — Hidden Dissenter

### Label space

```text
A
B
C
D
NONE
```

Q2 is interpreted conditionally with respect to Q1.

### Decision rule

| Q1 label | Q2 label |
|---|---|
| `TRUE_CONSENSUS` | `NONE` |
| `PSEUDO_CONSENSUS` | `A`, `B`, `C`, or `D` only if one participant is clearly identifiable as the standout hidden dissenter |
| `NO_CONSENSUS` | `NONE` |
| `UNCERTAIN` | `NONE` |

Even when Q1 is `PSEUDO_CONSENSUS`, Q2 should be `NONE` if:

- more than one participant shows comparable subtle misalignment;
- participant identity cannot be reliably mapped;
- no single participant stands out with sufficient evidence.

When no single participant clearly stands out, Q2 is `NONE`.

---

## 4.4 CONSENSUS Boundary Rules

### TRUE_CONSENSUS vs PSEUDO_CONSENSUS

Ask whether there is a **meaningful, persistent participant-level contradiction** to the surface agreement.

- no meaningful contradiction → `TRUE_CONSENSUS`;
- surface agreement plus one clear subtle contradiction → `PSEUDO_CONSENSUS`.

### PSEUDO_CONSENSUS vs NO_CONSENSUS

- `PSEUDO_CONSENSUS`: the group **appears to agree**, while dissent remains indirect, suppressed, or weakly expressed;
- `NO_CONSENSUS`: disagreement is sufficiently overt or the group is visibly fragmented.

### PSEUDO_CONSENSUS vs UNCERTAIN

Pseudoconsensus requires **positive evidence of misalignment**, not merely absence of enthusiasm or insufficient visibility.

If the evidence does not establish a contradictory participant-level signal, use `UNCERTAIN` rather than inferring hidden dissent.

---

# 5. Cross-Task Ambiguity Rules

## 5.1 Occlusion or poor visibility

If the task-relevant participant or reaction is not sufficiently observable, do not infer a social state from transcript content alone.

Use a task-specific uncertainty label where available. During construction, candidates with insufficient visual support could be excluded.

## 5.2 Conflicting evidence

When cues disagree:

1. verify that the cues occur in the same relevant temporal interval;
2. distinguish sustained cues from incidental movements;
3. determine whether the cues refer to the same interactional target;
4. prefer the interpretation supported by the strongest coherent multimodal pattern;
5. if no interpretation is adequately supported, use the relevant uncertainty category.

## 5.3 Politeness, conformity, and social norms

Meeting behavior may be shaped by politeness, hierarchy, conformity, or conflict avoidance. Such factors should only enter the annotation when they are reflected in observable behavior.

Do not infer social pressure from participant role, hierarchy, or workplace assumptions alone.

For example, verbal agreement plus persistent visible skepticism may support pseudoconsensus; verbal agreement by itself does not establish hidden dissent.

## 5.4 Cultural interpretation

Interpretations of gaze, politeness, engagement, disagreement, and conformity can depend on cultural and interactional norms. MeetingToM therefore represents one documented operationalization under a fixed protocol rather than a culturally universal interpretation of human social behavior.

---

# 6. Quick Reference

## 6.1 STATE

| Label | Core operational criterion |
|---|---|
| `ACTIVE_ENGAGEMENT` | actively contributing, leading, or managing the interaction |
| `SUPPORTIVE_ENDORSEMENT` | clear positive alignment or validation |
| `FOCUSED_LISTENING` | attentive, task-oriented, affectively neutral reception |
| `COGNITIVE_CONFLICT` | visible disagreement, resistance, or skepticism |
| `CONFUSED_BEWILDERMENT` | visible comprehension difficulty or searching uncertainty |
| `HESITATION` | transitional uncertainty immediately before speaking or acting |
| `DISENGAGED_WITHDRAWAL` | sustained attentional or interactional withdrawal |

## 6.2 YOU Q1

| Label | Criterion |
|---|---|
| `A/B/C/D` | converging cues support one specific addressee |
| `MULTIPLE` | the address is directed to multiple participants or the group |
| `UNKNOWN` | the addressee cannot be reliably resolved |

## 6.3 YOU Q2

| Label | Criterion |
|---|---|
| `SUPPORT` | observable positive alignment |
| `OPPOSE` | observable disagreement or resistance |
| `NEUTRAL` | observable but non-polar stance |
| `UNCERTAIN` | insufficient or materially conflicting evidence |

## 6.4 CONSENSUS

| Label | Criterion |
|---|---|
| `TRUE_CONSENSUS` | broad alignment with no meaningful contradictory participant signal |
| `PSEUDO_CONSENSUS` | surface agreement plus a clear subtle misalignment signal |
| `NO_CONSENSUS` | overt disagreement or fragmented group alignment |
| `UNCERTAIN` | insufficient evidence to distinguish the consensus states |

---

# 7. Interpretation Note

MeetingToM provides a consistent annotation framework for meeting-grounded social reasoning. Attitude, pseudoconsensus, and hidden-dissent labels are adjudicated third-person judgments based on the evidence available in the annotated interaction window. As with other socially interpretive annotations, some boundary cases may support more than one reasonable reading.

The benchmark should therefore be used as a documented operationalization of these social-reasoning constructs under the released protocol.
