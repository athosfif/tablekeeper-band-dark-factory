# Factory design

Three existing BAND identities cooperate in one new execution room: `athoss.felipe/figueira-planner`, `athoss.felipe/figueira-builder`, and `athoss.felipe/figueira-reviewer`. Each uses Codex with the inherited `gpt-6-astra` model. The planner decomposes requirements and acceptance criteria; the builder implements; the reviewer derives independent checks, runs the harness, and returns evidence-based defects.

The standing mandates remain product-independent. Product requirements arrive in the room task. The reviewer is not the implementer. Handoffs must include the complete requirements and a committed revision. Agents coordinate repairs themselves. A failed run or blocker is preserved, never relabeled successful.

No scored stage was dispatched at initialization. Actual costs, timings, results and recovery examples will be added from recorded evidence. Runtime uses the existing subscription; no new paid provider was enabled.
