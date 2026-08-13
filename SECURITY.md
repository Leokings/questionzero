# Security notes

## Scope and verification status

QuestionZero is a contract-only readiness registry. It classifies a public rule
specification; it does not evaluate an external event, custody assets, make an
EVM payment, fetch URLs, or accept secrets.

Local verification after the current implementation:

- GenVM lint and contract-schema validation pass.
- Strict typecheck passes with zero diagnostics.
- The TypeScript deployment helper passes strict typechecking.
- The portable toolchain pins GenLayer CLI `0.39.2`, `genlayer-js` `1.1.8`,
  TypeScript `7.0.2`, and reports zero pnpm audit advisories.
- 35 direct tests cover registration, normalization, bounded specification
  matching, immutable state, malformed LLM output, taxonomy verdict priority,
  and manual validator tampering paths.
- 3 five-validator GLSim tests cover a resolvable audit, ambiguous audit, and
  failed invalid-output quorum with no persisted state.
- Reviewed source SHA-256: `1B8672668E7AFB0F14205D98A53D2B64BF250A7323A9708ADC2A5F49E5B3A6B5`
  for `contracts/question_zero.py`.

This is an internal engineering review, not a third-party security audit.

## Security properties

| Risk | Control |
| --- | --- |
| Leader proposes a favorable classification | Each validator independently re-runs the classification and votes `AGREE` only for an exact canonical issue-mask match; GenLayer protocol quorum determines acceptance. |
| LLM response is malformed or differs | A malformed leader result cannot become a valid stored audit. A validator-side error or mismatch becomes a non-`AGREE` vote; unsuccessful consensus or execution writes no audit state. |
| Model returns extra fields, duplicate codes, strings in place of arrays, or unknown codes | Strict normalization rejects the response. |
| Caller tries to overwrite an audit | Each specification can be audited once; later attempts revert. |
| Caller tries to change a registered key's rule text | The same creator/key must be byte-for-byte equivalent after normalization or it reverts. |
| Another wallet front-runs a readable key | The specification ID includes the creator address. |
| Untrusted caller injects an arbitrary verdict | The contract never accepts caller-supplied verdicts; it only persists the consensus result. |
| Consumer substitutes an unrelated benign audit | `matches_resolvable_spec` requires the expected SHA-256 fingerprint, which commits to the creator, key, policy, rules, outcomes, evidence mode, and deadline. |
| Wrong network or changed source is deployed | The deploy helper requires an explicit StudioNet/Bradbury stage, checks both chain ID and RPC host (Bradbury and Asimov share `4221`), and checks the reviewed source SHA-256 before submission. |

The live StudioNet preflight also exercised a long eight-argument binding view
and exposed a `gen_call` SDK/RPC-path interoperability error for the large
payload. The production ABI replaces that call with a two-string fingerprint
comparison; direct and five-validator tests cover the replacement.

## Live deployment verification

Read-only network retrieval confirmed that the current StudioNet contract
`0xBc94C882f9a8269A668B07378780E5E2A8689E3A` and Bradbury contract
`0xcD66c6384d0443746C79889507b6d85fb85Ffa80`, both deployed by
`0x797d3B25fB2cCA0Ff93F60df1910267f3822D655`, exactly match reviewed SHA-256
`1B8672668E7AFB0F14205D98A53D2B64BF250A7323A9708ADC2A5F49E5B3A6B5`.
StudioNet also exposes the compact `matches_resolvable_spec` ABI and no retired
long-argument binding view.

Deployment, registration, and audit transactions finalized successfully on
both networks. Each smoke audit persisted `RESOLVABLE` with issue mask `0`;
the exact precommitted fingerprint matched and a one-nibble alteration did not.
The StudioNet audit receipt recorded three `AGREE` votes and two `IDLE`
validators after quorum. The Bradbury deployment and registration each recorded
five `AGREE` votes; its audit reports `FINISHED_WITH_RETURN` and finalized with
four `AGREE` votes and one `TIMEOUT`.

## Residual risks and required consumer controls

- **LLM semantics and quorum:** Per-validator exact comparison plus protocol
  quorum is an integrity and liveness control, not proof of semantic truth or
  unanimous model agreement. The Bradbury smoke audit finalized with four
  `AGREE` votes and one `TIMEOUT`. Carefully crafted text
  can still influence multiple models in the same way. Treat `RESOLVABLE` as a
  bounded policy classification, not a legal or business guarantee.
- **Prompt injection:** Specifications are untrusted data and are explicitly
  delimited in the prompt, and the closed taxonomy includes
  `ADVERSARIAL_INSTRUCTION`. Those controls reduce but cannot eliminate
  common-mode model-level prompt injection risk. Never include secrets in a
  specification.
- **Evidence availability:** The contract classifies what the rules claim about
  evidence; it does not fetch a URL or prove that a stated source exists. A
  downstream adjudicator must independently retrieve and validate evidence.
- **Public data:** Every stored rule, deadline, creator address, and audit is
  public. This contract is unsuitable for confidential terms or personal data.
- **Finality:** A downstream contract must act only after audit finality. It
  must independently precommit the expected fingerprint and pin the expected
  QuestionZero deployment. Fetching a fingerprint and echoing it back does not
  prevent record substitution. The
  status-only `has_resolvable_audit` boolean is insufficient.
- **Immutability:** The contract has no application-level appeal or refresh
  method. Protocol appeals still govern a transaction before finality. After
  finality, deploy a new policy version for a changed taxonomy or corrected
  policy.
- **Gas griefing:** Anyone can pay to request an audit. The caller pays the
  transaction cost; the contract does not pool or reimburse funds.

## Disclosure

Do not publish private keys, passwords, account keystores, or live secrets in an
issue or source file. For a serious vulnerability, contact the project owner
privately before public disclosure.
