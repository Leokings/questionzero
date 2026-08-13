# GenLayer Portal submission draft

## Contribution date

08/13/2026

## Suggested title

QuestionZero — Reusable Adjudicability Gate

## Notes / Description — 993/1000 characters

QuestionZero is a reusable GenLayer Intelligent Contract that audits whether a public natural-language rule specification is defined enough for another contract to adjudicate. A caller registers bounded rules, outcomes, an evidence mode, and a deadline. The leader classifies the specification against an 11-code issue taxonomy; validators independently run the same bounded classification and compare the normalized issue mask. GenLayer quorum determines acceptance, followed by protocol finality. Audits return five bounded verdicts with ordered reason codes. Downstream contracts can use matches_resolvable_spec to require a finalized RESOLVABLE audit bound to a SHA-256 fingerprint of the exact creator, policy, rules, outcomes, evidence mode, and deadline. It does not decide real-world events or hold funds. The new Bradbury smoke audit finalized with 4 AGREE votes and 1 TIMEOUT, stored RESOLVABLE with issue mask 0, accepted the exact fingerprint, and rejected a one-nibble alteration.

## Evidence entries

### GitHub Repository — PENDING (PRIVATE; REVIEWER-INACCESSIBLE)

`https://github.com/Leokings/questionzero`

The repository currently requires authentication. Do not submit this entry until
the repository is public and the URL resolves without authentication.

### GitHub File — contract source — PENDING (PRIVATE; REVIEWER-INACCESSIBLE)

`https://github.com/Leokings/questionzero/blob/v0.1.0/contracts/question_zero.py`

### GitHub File — Bradbury proof — PENDING (PRIVATE; REVIEWER-INACCESSIBLE)

`https://github.com/Leokings/questionzero/blob/v0.1.0/deployments/bradbury.json`

### GitHub File — security notes — PENDING (PRIVATE; REVIEWER-INACCESSIBLE)

`https://github.com/Leokings/questionzero/blob/v0.1.0/SECURITY.md`

These immutable links address the annotated `v0.1.0` release tag. The
repository remains private, so reviewers cannot access them. Public visibility
is a separate submission gate; do not submit any pending GitHub entry until
every corresponding URL resolves without authentication.

### GenLayer Explorer Contract — VERIFIED

https://explorer-bradbury.genlayer.com/address/0xcD66c6384d0443746C79889507b6d85fb85Ffa80

### Bradbury deployment transaction — VERIFIED

https://explorer-bradbury.genlayer.com/tx/0x1739fa5e356797ba41a6f2d2b4e38d11dc150d23f739b9fa06a7b73eb53f6525

### Bradbury registration transaction — VERIFIED

https://explorer-bradbury.genlayer.com/tx/0x80e3f7a44ad33709b3144f1ef4359da7d319343d869dc2b0343623f1f863af86

### Bradbury RESOLVABLE audit transaction — VERIFIED

https://explorer-bradbury.genlayer.com/tx/0xf91b5e5e387c8cc55a542b29539ab8398e27262074b4fe4bc4433aebe728f792

## Supporting verification

- [StudioNet contract](https://explorer-studio.genlayer.com/address/0xBc94C882f9a8269A668B07378780E5E2A8689E3A): [deployment](https://explorer-studio.genlayer.com/tx/0x0a42866afc6e77a5f9b19b612c53c757060ae3514a06336f2e1882332249013a), [registration](https://explorer-studio.genlayer.com/tx/0x143c69facc88014b51681279d0f284a94c0012bca349e3cd5c324796cc0eb829), and [RESOLVABLE audit](https://explorer-studio.genlayer.com/tx/0x1b9749c34d766bc256fde177aed6209641deb16e92f2e4da0ce97c64f3a21e23). The audit fingerprint is `sha256:9529a17e3f1d4a1582947c8373d7f5f4967efd9683445f2742b8a3e7f143d53e`; its receipt recorded 3 `AGREE` and 2 `IDLE` validators.
- [Bradbury contract](https://explorer-bradbury.genlayer.com/address/0xcD66c6384d0443746C79889507b6d85fb85Ffa80): [deployment](https://explorer-bradbury.genlayer.com/tx/0x1739fa5e356797ba41a6f2d2b4e38d11dc150d23f739b9fa06a7b73eb53f6525), [registration](https://explorer-bradbury.genlayer.com/tx/0x80e3f7a44ad33709b3144f1ef4359da7d319343d869dc2b0343623f1f863af86), and [RESOLVABLE audit](https://explorer-bradbury.genlayer.com/tx/0xf91b5e5e387c8cc55a542b29539ab8398e27262074b4fe4bc4433aebe728f792). The audit fingerprint is `sha256:84c22cd3e30a708fb6b829b2ab6aaa9136bac952a406dda59a9f309893edd137`; its final round recorded 4 `AGREE` and 1 `TIMEOUT`.
- Both deployments exactly match reviewed source SHA-256 `1B8672668E7AFB0F14205D98A53D2B64BF250A7323A9708ADC2A5F49E5B3A6B5`.

The Portal submission category should be **Builder → Intelligent Contracts**.
