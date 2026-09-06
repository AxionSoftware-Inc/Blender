# Spectra handoff status labels

Use these labels consistently across new chats, agent prompts, reports, and docs:

- **VERIFIED GREEN** — exact commit has actually passed the stated compile/test/native validation and the results were recorded.
- **IMPLEMENTED / PENDING VALIDATION** — runtime code exists but the current promotion gate has not been completed.
- **SPECIFIED** — architecture/API/design contract exists in documentation; runtime support may be partial or absent.
- **AUDITED** — relevant source/capability paths were inspected and the safe implementation direction is known, but the milestone is not complete.
- **PLANNED** — roadmap concept only.

Never upgrade a label because code "looks correct" or because a previous commit was green. Validation status belongs to the exact tested commit and exact tested scope.
