# Handoff source priority

When two documents appear to disagree, use this order:

1. actual Git state and actual validation output;
2. `CHAT_LIMIT_HANDOFF_2026-09-06.md` for chronological/current-session intent;
3. milestone-specific validation handoff for that milestone's detailed invariants;
4. current implementation source/tests;
5. older planning/design docs;
6. historical chat recollection.

A newer plan never overrides observed test results, and a historical green result never automatically validates a newer commit.
