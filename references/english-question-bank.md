# SWT English Assessment Question Bank (v0.7)

Choose and adapt one prompt at a time from the relevant profile and question type. Prompt variation and dynamic follow-up are intentional: this is not a fixed eight-question test. Never pre-supply model answers. `targets` refer to criterion keys in [english-rubric.md](english-rubric.md). Tailor details to known user facts and profile context.

## Agency Screening (`agency_generic`)

| Question type | Difficulty | Example prompt | Targets | Follow-up type |
|---|---|---|---|---|
| Self-introduction | easy | “Could you briefly introduce yourself?” | C1, C2, C3, C4 | ask one detail not in the prepared opening |
| School / major | easy | “What are you studying, and what do you like about it?” | C1, C3, C4, C7 | ask for a concrete example or clarification |
| SWT motivation | easy | “Why do you want to join the Summer Work Travel program?” | C1, C2, C4, C7 | ask what the participant hopes to learn or experience |
| Basic work experience | easy | “Have you worked before? What did you do?” | C1, C3, C4, C7 | vary to a task or responsibility they actually had |
| Simple follow-up | medium | “What would you do if you did not understand a coworker?” | C1, C6, C7 | ask for the exact words they would use |
| Daily communication | easy | “How would you ask someone to repeat a direction?” | C1, C3, C6, C7 | change one detail or ask them to rephrase |

## Sponsor Screening (`sponsor_generic`)

| Question type | Difficulty | Example prompt | Targets | Follow-up type |
|---|---|---|---|---|
| SWT understanding | medium | “What do you understand about the purpose of the SWT program?” | C1, C3, C4, C7 | ask which part involves cultural exchange or work responsibilities |
| Motivation | easy | “Why did you choose to participate this year?” | C1, C2, C3, C7 | ask why now or what the participant expects to be challenging |
| Work / life expectations | medium | “What do you expect daily life and work in the U.S. to be like?” | C1, C2, C3, C7 | change a condition and ask how they would adapt |
| Problem handling | situational | “Your schedule differs from what you expected. How would you handle it?” | C1, C6, C7 | ask whom they would contact and what they would say |
| Communication difficulty | medium | “What would you do if you could not understand an important instruction?” | C1, C6, C7 | role-play the clarification request, then vary the listener's reply |
| Sponsor / employer problem | situational | “You need help with a work or housing concern. How would you explain it and ask for support?” | C1, C2, C6, C7 | ask what details the listener needs next |
| Follow-up handling | medium | “You said you want cultural exchange. What is one specific example?” | C1, C3, C6, C7 | change from prepared motivation to an unprepared example |

## Host Employer Interview (`host_generic`)

First read available Employer, Position, duties, customer contact, environment, Offer/JD, and current context. Select a task matching the actual job; do not run identical task communication prompts for all positions.

| Position / question type | Difficulty | Example prompt | Targets | Follow-up type |
|---|---|---|---|---|
| Any: why this position | easy | “Why are you interested in this position?” | C1, C2, C3, C7 | ask which listed duty they expect to do most often |
| Any: experience | easy | “Which real experience has prepared you for this job?” | C1, C3, C4, C7 | ask what they personally did; do not invent experience |
| Cashier: transaction/customer | situational | “A customer says the price at the register is different from the shelf. What would you say or do?” | C1, C6, C7 | change to a payment or scanning problem; check when they ask a manager |
| Retail Associate: customer help | situational | “A customer asks where an item is, but you are not sure. How would you respond?” | C1, C6, C7 | ask how they would confirm the information |
| Front Desk: check-in/request | situational | “A guest arrives while you are helping someone else. What would you say?” | C1, C2, C6, C7 | add a missing reservation detail or an upset guest |
| Housekeeping: instructions/room status | situational | “A room is marked ready, but you notice something is unfinished. What would you report?” | C1, C3, C6, C7 | ask whom they would tell and what details matter |
| Kitchen Helper: safety/instructions | situational | “You are not sure whether an item is ready to serve. How would you check?” | C1, C6, C7 | give a changed instruction and ask the participant to confirm it |
| Lifeguard: safety/escalation | situational | “You see a safety rule being ignored. What would you say or do?” | C1, C2, C6, C7 | ask how they would report an incident to a supervisor |
| Any: availability | easy | “What dates are you available to work?” | C1, C3, C4, C7 | compare against the user's known dates; do not guess missing dates |
| Any: manager communication | medium | “You realize you may be late for a shift. How would you contact your manager?” | C1, C3, C6, C7 | ask what information they would include |

## Visa Interview Communication (`visa_interview_generic`)

Use only verified facts already available or facts supplied by the user. If a statement conflicts with DS-160, DS-2019, Offer, or known context, stop and mark `fact_conflict`; `swt-visa` resolves the fact.

| Question type | Difficulty | Example prompt | Targets | Follow-up type |
|---|---|---|---|---|
| Program purpose | medium | “What is the purpose of your trip?” | C1, C2, C3, C4, C7 | ask one short factual detail already in the record |
| Sponsor | medium | “Who is your program Sponsor?” | C1, C3, C4, C7 | check concise direct response against known record, not memory coaching |
| Employer / job | medium | “Where will you work, and what will your job be?” | C1, C3, C4, C7 | ask a factual job-duty follow-up from verified Offer/JD |
| Location / dates | medium | “Where is your job located, and when does your program run?” | C1, C3, C4, C7 | use dates/location from verified documents only |
| School / student identity | medium | “What are you studying, and what will you do after the program?” | C1, C2, C4, C7 | ask only for the user's truthful, verified plan; no coached claims |
| Directness / follow-up | situational | Ask a known, document-grounded factual question with changed wording. | C1, C2, C6, C7 | follow up once; if content conflicts with source, stop factual feedback |

## Comprehensive Assessment (`comprehensive`)

Select a small balanced set across basic profile communication, Sponsor interaction, a role-aware Host task when position context exists, and verified Visa fact expression. Use the same seven criterion evidence for the four profile maps. Each question should add evidence to one or more criteria; do not schedule four profile question sets or repeat answered questions.
