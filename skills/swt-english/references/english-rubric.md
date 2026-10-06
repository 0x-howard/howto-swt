# SWT Speaking Rubric (v0.7)

This file is the scoring source of truth for the seven SWT Speaking Core criteria. Scores describe observed performance in the selected SWT task, not personality, intelligence, accent prestige, or predicted selection outcomes. Use whole-number anchors below; intermediate scores may be interpolated only when evidence falls between two anchors.

## Seven criteria and observable anchors

### C1. Comprehension & Relevance — 理解与切题

Did the response show that the question was understood and answer what was asked?

| Score | Observable anchor |
|---:|---|
| 1 | Often cannot understand basic questions; responses are mostly unrelated or absent. |
| 3 | Understands very simple familiar questions, but small changes often cause a misread or off-topic answer. |
| 5 | Understands most ordinary questions; may miss a condition or need repetition for a longer follow-up. |
| 7 | Reliably understands ordinary SWT questions and common follow-ups; answers the main point and asks for clarification when needed. |
| 9 | Quickly understands complex or unexpected changes and responds accurately to the specific question. |
| 10 | Shows exceptionally stable, precise understanding and relevance across the sampled tasks, including changed wording and follow-ups. |

### C2. Fluency & Coherence — 流利与连贯

For voice, judge audible continuity, pauses used to search for language, repetition, and logical progression. For text, judge answer structure only; never infer speaking fluency from typing speed or polished prose.

| Score | Observable anchor |
|---:|---|
| 1 | Spoken responses repeatedly stop after isolated words or fragments; ideas cannot be followed. |
| 3 | Can produce short basic phrases, but frequent long pauses, restarting, or disconnected ideas make the response hard to follow. |
| 5 | Can sustain a simple answer; noticeable searching, repetition, or weak sequencing sometimes interrupts meaning. |
| 7 | Usually speaks in connected sentences with a clear order; occasional pauses or repairs do not disrupt understanding. |
| 9 | Sustains answers naturally, links and develops ideas clearly, and uses pauses mainly to plan meaning rather than search for basic language. |
| 10 | Shows exceptionally steady, coherent, appropriately paced speech across sampled tasks; no one answer alone warrants this anchor. |

### C3. Vocabulary — 词汇表达

Judge whether vocabulary is sufficient, accurate, and flexible for the current SWT task. Advanced words do not earn credit by themselves.

| Score | Observable anchor |
|---:|---|
| 1 | Available words rarely communicate basic intended meaning, even with context. |
| 3 | Uses a narrow set of familiar words; frequent misuse or word-searching blocks ordinary SWT communication. |
| 5 | Has enough common vocabulary for familiar topics; repetition, imprecision, or occasional word choice errors limit detail. |
| 7 | Uses suitable everyday and work-related vocabulary to explain, clarify, and handle common SWT topics with only minor imprecision. |
| 9 | Chooses precise and flexible vocabulary across sampled tasks and can paraphrase when a word is missing. |
| 10 | Communicates precise meanings consistently and flexibly in the sampled SWT range; rare slips do not reduce clarity. |

### C4. Grammar — 语法控制

Judge control of basic structures, range needed for the task, and whether errors change or obscure meaning.

| Score | Observable anchor |
|---:|---|
| 1 | Frequent errors make even basic relationships, time, or meaning difficult to recover. |
| 3 | Uses fragments and a few basic forms; recurring errors often obscure who did what or when. |
| 5 | Basic sentence forms usually convey the point; errors are frequent, especially in longer or changed answers, but meaning is often recoverable. |
| 7 | Controls common sentence patterns and simple connected clauses; occasional errors rarely affect understanding. |
| 9 | Uses an appropriate range of structures with strong accuracy; errors are occasional and do not distract from meaning. |
| 10 | Maintains precise, flexible grammatical control across sampled tasks; isolated slips are self-corrected or immaterial. |

### C5. Pronunciation & Intelligibility — 发音可理解度

Score only from genuine audio. Judge how readily a listener understands the words and message, including sounds, stress, rhythm, and connected speech. A non-native accent is not a fault by itself.

| Score | Observable anchor |
|---:|---|
| 1 | Much of the message cannot be understood even with context or repetition. |
| 3 | Key words are often difficult to identify; the listener must repeatedly infer or ask for repetition. |
| 5 | Main ideas are generally understandable, but recurring sound or word-stress issues cause noticeable effort or occasional misunderstanding. |
| 7 | Speech is readily understandable in ordinary SWT tasks; some accent features or sound errors remain but rarely impede communication. |
| 9 | Speech is consistently easy to understand; stress, rhythm, and connected speech support meaning, regardless of accent. |
| 10 | Speech is exceptionally clear and consistently effortless to understand across the sampled tasks; native-like accent is not required. |

### C6. Interaction & Repair — 互动与修复

Judge observable response to follow-ups, interruptions, changed directions, and communication breakdowns.

| Score | Observable anchor |
|---:|---|
| 1 | Cannot continue after a question changes or a listener signals misunderstanding; no usable repair is attempted. |
| 3 | Gives a memorized initial answer but often freezes on a simple follow-up; rarely asks for repetition or clarification. |
| 5 | Handles familiar follow-ups unevenly; may repeat, guess, or abandon an answer rather than repair a breakdown. |
| 7 | Responds to ordinary follow-ups and can request repetition, clarify meaning, or rephrase when needed. |
| 9 | Adapts promptly to changed questions, checks understanding, and repairs breakdowns without losing the interaction. |
| 10 | Sustains flexible, listener-aware interaction across different follow-up types and recovers smoothly from unexpected changes. |

### C7. Task Communication — 任务沟通

Judge whether the user can complete the communication task the selected profile or actual job requires. This is scenario-specific, not a general fluency judgment.

| Score | Observable anchor |
|---:|---|
| 1 | Cannot complete the core communication action for the selected task, even with a simple prompt. |
| 3 | Completes isolated parts but misses essential information or leaves the task unresolved. |
| 5 | Completes a basic version of the task with support; omissions or unclear requests could disrupt an ordinary interaction. |
| 7 | Completes common SWT tasks clearly enough for the listener to act; may need occasional repetition or confirmation. |
| 9 | Completes the task clearly, appropriately, and independently, including relevant details and next steps. |
| 10 | Reliably completes varied or changed tasks with precise, listener-oriented communication and appropriate confirmation. |

## Evidence and confidence

Evidence is a distinct observable response or audio segment relevant to a criterion. Rephrasing the same answer does not create a new independent sample. Use these minimum counts before treating a criterion as sufficiently sampled:

| Criterion key | Minimum `evidence_count` | Evidence guidance |
|---|---:|---|
| `comprehension_relevance` | 3 | Distinct questions, including at least one changed wording or follow-up. |
| `fluency_coherence` | 3 | Distinct sustained responses; for voice, include observable speech continuity. |
| `vocabulary` | 4 | Distinct answers across at least two topic types. |
| `grammar` | 4 | Distinct complete answers, not isolated corrected sentences. |
| `pronunciation_intelligibility` | 3 | Distinct genuine audio responses; transcript text is not audio evidence. |
| `interaction_repair` | 2 | Two actual dynamic follow-ups or communication-repair opportunities. |
| `task_communication` | 2 | Two distinct profile-relevant communication tasks. |

For each criterion store `score` (1–10 or `null`), `confidence` (`low`, `medium`, `high`), and `evidence_count` (integer). Confidence describes evidence quality, not the participant:

- `low`: one narrow sample, ambiguous evidence, or substantial input limitation.
- `medium`: repeated relevant evidence, with some remaining variation or uncertainty.
- `high`: multiple clear samples across relevant task types, with consistent observable behavior.

Do not award `high` from one memorized introduction. A complete target readiness result requires enough evidence for all seven criteria and genuine voice evidence; otherwise report a partial assessment and identify unavailable or undersampled criteria. Stop once evidence is sufficient; do not repeat already well-sampled criteria merely to reach a fixed question count.

## Input-mode limits

| Mode | What can be evaluated | What must not be inferred |
|---|---|---|
| `voice` | Spoken response content, pauses, speech continuity, rhythm/stress, and pronunciation when actual audio is available to the system. | Native-like accent as a requirement; personal traits from voice. |
| `transcript` | Comprehension/relevance, vocabulary, grammar, task content, and limited coherence from transcript text. | Pronunciation, intelligibility, pauses, pace, rhythm, stress, or speech continuity. Set C5 unavailable. |
| `text` | Comprehension/relevance, vocabulary, grammar, answer structure, and task content. | Speaking fluency, pronunciation, pauses, real-time spoken interaction, or any typing-speed proxy. Set C5 and spoken C6 unavailable; do not describe the result as a full speaking assessment. |

For transcript/text, C2 may be recorded only as a clearly qualified coherence observation if useful; spoken fluency remains unavailable. In text mode, a written clarification exchange may be described but is not evidence of spoken C6 Interaction & Repair. Do not fill unavailable criteria with a neutral or estimated score.

## IELTS-style layer

Use the four public IELTS Speaking descriptor dimensions only as a descriptor-informed comparison: C2 ↔ Fluency and Coherence, C3 ↔ Lexical Resource, C4 ↔ Grammatical Range and Accuracy, C5 ↔ Pronunciation. Consider observable descriptor behavior at the nearest band; do not mechanically convert SWT 1–10 scores into IELTS bands. If summarizing as a single number, label it **IELTS-style estimate**, show `≈`, and make clear it is not an official IELTS score or validated conversion.

Only genuine voice evidence can support a complete IELTS-style Speaking estimate. With transcript/text, use **IELTS-style partial estimate** for the dimensions that can be observed, state that pronunciation is unavailable, and say that full IELTS-style estimation needs audio. Never score pronunciation from spelling, grammar, or transcript punctuation.

Reference: [IELTS Speaking Band Descriptors (official public version)](https://ielts.org/cdn/ielts-guides/ielts-speaking-band-descriptors.pdf). The IELTS descriptors inform the comparison layer; this SWT rubric remains the scoring source of truth for SWT readiness.

## Unavailable and conflict cases

- Mark an unobserved criterion `score: null`, confidence `low`, and record `evidence_count: 0`; never substitute a midpoint.
- Do not estimate pronunciation without actual audio, including when a transcript came from speech recognition.
- If an answer conflicts with known Visa documents or verified facts, mark `fact_conflict`, pause factual coaching, and route fact checking to `swt-visa`. Do not polish or score the false factual claim as a suitable visa answer. Other independently observable language evidence may still be described without endorsing the content.
- A readiness result is not an Agency, Sponsor, Host, government, or IELTS decision and must not be presented as pass/fail probability.
