# SWT English Assessment (v0.7)

Assessment is the `ASSESS` path in `swt-english`. Formal Sponsor/Host/Visa simulation uses `MOCK`; ordinary corrections and work/life help use `PRACTICE` or the `GENERAL ENGLISH` fallback. Pro long-term training state is handled only through the existing Lifecycle Context.

## Start and route

Use assessment when a user asks to test, measure, assess, score, or check readiness, such as “测一下我的口语”, “机构口测”, “看看我能不能应付 Sponsor 面试”, “测我的 cashier 英语”, “测一下美签英语”, or “综合 SWT 英语测评”. A request for a realistic interview simulation enters `MOCK`, which delays feedback and produces the same Assessment Result at completion.

Select `agency_generic`, `sponsor_generic`, `host_generic`, `visa_interview_generic`, or `comprehensive` from the user's explicit target. A named agency or Sponsor stays generic without authentic specific scoring material. For comprehensive, gather one shared evidence set and map it through each profile. Do not repeat the assessment four times.

For Host, reuse existing Employer, Position, duties, customer interaction, environment, Offer/JD, and current job context. Ask one role question only if no usable position context exists and it changes task selection: “你准备面试什么岗位？” If context already says Retail Associate, do not ask again.

For Visa, load `swt-visa` facts/context for any known DS-160, DS-2019, Offer, Sponsor, job, location, and dates. `swt-visa` determines what is factually correct; this assessment judges how the user communicates verified facts. Mark `fact_conflict`, pause content coaching, and route reconciliation to `swt-visa` when an answer conflicts with a known source. Never make incorrect facts sound more convincing.

## Input mode

Record one mode for each response set:

- `voice`: the system has actual audio, not merely audio-origin text.
- `transcript`: only a transcript is available.
- `text`: user is typing.

Follow [english-rubric.md](english-rubric.md) for mode-specific criteria. In text mode say: “当前为文字模拟，不能代表完整口语表现。” Neither transcript nor text can receive a pronunciation score; do not equate typing speed with speech fluency. Mark unobserved criteria unavailable and let the calculator return a partial assessment.

## Adaptive assessment flow

1. State the selected profile and mode briefly. Reuse known context; ask only for a decision-changing missing item.
2. Ask one question at a time. Default sequence: Q1 warm-up/self-introduction; Q2 personal/school background; Q3–Q4 profile-relevant core tasks; Follow-up 1; a situation question; Follow-up 2. Add Q7/Q8 only for criteria whose evidence is still insufficient.
3. Select question types, difficulty, and criterion targets from [english-question-bank.md](english-question-bank.md); vary wording and follow-up direction. The bank is a pool, not a fixed test or answer script.
4. Track evidence per criterion internally as `{score, confidence, evidence_count}`. Use the minimum counts in the rubric. After each answer, ask a targeted follow-up only if evidence is missing/weak; do not repeat a criterion already sufficiently sampled. Two genuine follow-ups are required before assigning a high Interaction & Repair score.
5. Normally finish after 6–8 main questions (about 8–12 minutes), but finish earlier when all important evidence is sufficient or add Q7/Q8 when needed. The stop rule is evidence sufficiency, not a fixed question count. If the user stops early, report partial results.
6. Calculate each profile score only with `scripts/speaking_score.py`; do not do weighted arithmetic in prose. The script normalizes by the weights of sufficiently evidenced criteria, rounds half-up to one decimal, reports the sum of included profile weights as `weight_coverage_pct` (0–100), carries forward the lowest included criterion confidence, and lists each missing/undersampled criterion. A missing or undersampled criterion produces `Partial Assessment`, not a full precise score. If input mode is omitted from a script request, the script defaults to `text` and will not infer audio evidence.
7. For comprehensive mode, apply all four profile weight columns to the same seven observed criteria, display the mappings together, and name the largest profile-fit difference; no duplicate questioning.
8. Compare an IELTS-style layer only through C2–C5 and official public descriptor behaviors. Do not claim IELTS score equivalence. Without voice, show only an `IELTS-style partial estimate` or state that full estimation needs audio; pronunciation stays unavailable.

The usual session is 6–8 main questions and roughly 8–12 minutes, not a quota. Dynamic follow-ups distinguish a prepared answer from live interaction. Stop once evidence is sufficient.

For a Comprehensive result, use one compact four-row table (`Profile | Readiness`) for Agency, Sponsor, Host, and Visa Interview Communication. Show the actual Host position in its row when known, then name the largest readiness difference and which criterion weights explain that scenario-fit difference.

## First result and follow-up choices

Compress the first result to: one key conclusion; a small result table; at most three current weaknesses; one to three material limitations; and one choice question. Example table:

| Result | Score |
|---|---:|
| Sponsor Readiness | 7.1 / 10 (partial or complete) |
| IELTS-style | ≈ 5.5 / 9 (only when evidence supports it) |

Show no more than three weakest criteria. State the actual mode and any missing audio/factual evidence when it changes interpretation. Do not default to all per-question errors, all seven explanations, every evidence note, full IELTS descriptors, or a long teacher-style review. End with only:

> 接下来想看什么？A. 逐题评分　B. 七维详情　C. 错误示例　D. 再测一次

- **A. 逐题评分:** expand only question-by-question performance.
- **B. 七维详情:** expand only the seven criterion details.
- **C. 错误示例:** show representative `original → issue → more natural expression`, preserving the user's true facts.
- **D. 再测一次:** begin a new assessment and append a new run; do not overwrite the prior result.

Answering A/B/C is a detail request, not a request to repeat the test.

## Result record

Keep only current-conversation state. A run uses:

```yaml
english_assessment:
  assessment_id: local sequence or conversation turn id
  profile: sponsor_generic
  target_name: null
  target_position: null
  input_mode: voice
  question_count: 0
  criteria: {}
  ielts_style: unavailable
  readiness: null
  top_weaknesses: []
  fact_conflict: false
  completed: false
  previous_runs: []
```

Append a compact completed-result snapshot to `previous_runs` before starting a retest. Do not imply cross-conversation persistence. The recommended result object is:

```json
{
  "assessment_type": "swt_english",
  "profile": "sponsor_generic",
  "target_name": null,
  "target_position": null,
  "input_mode": "voice",
  "criteria": {
    "comprehension_relevance": {"score": 8.0, "confidence": "high", "evidence_count": 5},
    "fluency_coherence": {"score": 6.1, "confidence": "high", "evidence_count": 6},
    "vocabulary": {"score": 6.8, "confidence": "high", "evidence_count": 6},
    "grammar": {"score": 6.3, "confidence": "high", "evidence_count": 6},
    "pronunciation_intelligibility": {"score": 7.0, "confidence": "medium", "evidence_count": 6},
    "interaction_repair": {"score": 5.8, "confidence": "medium", "evidence_count": 2},
    "task_communication": {"score": 7.1, "confidence": "high", "evidence_count": 4}
  },
  "ielts_style": 5.5,
  "ielts_style_status": "IELTS-style estimate, IELTS-style partial estimate, or unavailable",
  "target_readiness": 7.1,
  "readiness_status": "complete or partial",
  "weight_coverage_pct": 100,
  "top_weaknesses": ["interaction_repair", "fluency_coherence", "grammar"],
  "fact_conflict": false
}
```

## Score names and limitations

Use only `Agency Readiness`, `Sponsor Readiness`, `Host Readiness`, `Visa Interview Communication Readiness`, or profile-specific variants with a known job name. Generic profiles report readiness only. Never say “will pass”, “will fail”, “80% chance”, Visa Pass Score, Visa Success Probability, Sponsor pass probability, or Host hiring probability. These are internal readiness estimates, not official assessments from a government, agency, Sponsor, Host, or IELTS.
