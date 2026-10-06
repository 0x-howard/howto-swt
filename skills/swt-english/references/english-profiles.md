# SWT English Assessment Profiles (v0.7)

All profiles share the seven criteria in [english-rubric.md](english-rubric.md). Profile weights select which observed abilities matter most in the target setting; they are **SWT Skill v0.7 Internal Rubric** weights, not U.S. government, Sponsor, Agency, Host, or IELTS official scores. Weights may be calibrated later only against reliable, relevant evidence.

## Profiles and internal weights

| Criterion | Criterion key | `agency_generic` | `sponsor_generic` | `host_generic` | `visa_interview_generic` |
|---|---|---:|---:|---:|---:|
| C1 理解与切题 | `comprehension_relevance` | 20 | 25 | 20 | 30 |
| C2 流利与连贯 | `fluency_coherence` | 20 | 15 | 15 | 15 |
| C3 词汇表达 | `vocabulary` | 15 | 10 | 10 | 5 |
| C4 语法控制 | `grammar` | 10 | 10 | 5 | 5 |
| C5 发音可理解度 | `pronunciation_intelligibility` | 15 | 15 | 15 | 15 |
| C6 互动与修复 | `interaction_repair` | 10 | 20 | 10 | 15 |
| C7 任务沟通 | `task_communication` | 10 | 5 | 25 | 15 |
| **Total** |  | **100** | **100** | **100** | **100** |

## `agency_generic` — Agency Screening

- **Purpose:** estimate readiness for a generic agency basic English screening: “How prepared is the participant for an agency-level basic English check now?”
- **Priority abilities:** basic question comprehension, relevant answers, self-introduction, simple SWT motivation, and staying engaged through a plain follow-up.
- **Typical task types:** self-introduction; school/major; SWT motivation; basic work experience; simple follow-up; everyday communication.
- **Output name:** `Agency Readiness`.
- **Limitations:** no claim that a named agency will pass or accept the participant. Use `agency_generic` unless current, authentic agency-specific criteria and evidence are available. A named agency alone is not enough to create `agency_xxx`.

## `sponsor_generic` — Sponsor Screening

- **Purpose:** estimate readiness to communicate about the SWT program and handle an ordinary generic Sponsor screening.
- **Priority abilities:** understanding questions, relevant response, explaining SWT participation, real-time interaction, follow-up handling, repair strategies, and communicating a problem or request for help.
- **Typical task types:** program understanding; motivation; work/life expectations; problem handling; communication difficulty; Sponsor/employer problem scenario; follow-up.
- **Output name:** `Sponsor Readiness`.
- **Limitations:** use `sponsor_generic` without reliable, current Sponsor-specific interview criteria. Do not infer a Sponsor's decision or pass line.

## `host_generic` — Host Employer Interview

- **Purpose:** estimate whether the participant can complete the communication tasks of the specific job, not whether their English is generally “good.”
- **Priority abilities:** job-duty understanding and explanation, customer or coworker interaction, supervisor communication, instructions/safety, and job-specific scenarios.
- **Typical task types:** why this position; work experience; explain a duty; customer interaction; manager communication; complaint handling; safety/instruction comprehension; availability; job-specific scenario.
- **Output name:** `Host Readiness` (show the known position, e.g. `Host Readiness — Retail Associate`).
- **Limitations:** reuse known employer, position, duties, customer contact, environment, Offer/JD, and job context. If absent and it could materially change the assessment, ask only: “你准备面试什么岗位？” If no answer is available, label the result `General Host Communication`; do not use one identical task test for every job. Never infer hiring probability.

## `visa_interview_generic` — Visa Interview Communication

- **Purpose:** assess how clearly, directly, concisely, and naturally the participant can communicate true, verified information in a visa interview context.
- **Priority abilities:** understanding the officer's question, direct answer, concise explanation, follow-up handling, and natural but truthful delivery.
- **Typical task types:** trip/program purpose; Sponsor; employer and job; location; dates; school/student identity; basic factual follow-up.
- **Output name:** `Visa Interview Communication Readiness`.
- **Limitations:** `swt-visa` owns factual correctness, source documents, consistency, and visa process. Load known DS-160/DS-2019/Offer facts; mark `fact_conflict` and stop polishing or endorsing conflicting content. Never output visa pass score, visa success probability, or approval odds.

## `comprehensive`

Comprehensive Assessment is one evidence-gathering session against the shared seven criteria, followed by four deterministic profile mappings using the same criterion evidence. It is not four full assessments in sequence. Display each mapped profile separately. When job context is missing, use `General Host Communication` until one key position detail is available. Report the largest profile-fit differences as task-weight differences, not as four different underlying English abilities.
