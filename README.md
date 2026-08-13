# QuestionZero

QuestionZero is a reusable GenLayer Intelligent Contract that audits whether a
public, natural-language rule specification is sufficiently defined for another
contract to adjudicate. It does **not** decide the external event itself and it
does not hold user funds.

## Why it exists

Many on-chain workflows begin with a rule such as “pay if the milestone is
complete” or “approve if the supplier is eligible.” The expensive failure is
often earlier: the rule has overlapping outcomes, an undefined material term,
participant-controlled evidence, or an authority that can decide anything it
wants. QuestionZero turns that readiness question into an immutable,
consensus-backed on-chain record before a downstream contract relies on it.

## What it returns

A caller registers public rule text, an outcome schema, an evidence mode, and a
decision deadline. Anyone can request one audit. The leader proposes a canonical
issue bitmask. Each validator independently re-runs the same bounded
classification and votes `AGREE` only when its normalized bitmask exactly
matches the leader result. GenLayer's protocol quorum determines acceptance;
protocol finality follows, and unanimity is not required.

| Verdict | Meaning |
| --- | --- |
| `RESOLVABLE` | No defined issue was found by the policy. |
| `INCOMPLETE` | A material term or temporal rule is incomplete. |
| `AMBIGUOUS` | Outcomes overlap, leave gaps, conflict, or lack a tie rule. |
| `MANIPULABLE` | A participant, circular authority, or unbounded discretion controls the result. |
| `UNVERIFIABLE` | The stated evidence cannot be checked under the declared evidence mode. |

The stored audit includes both the ordered `issue_codes` and the deterministic
`issue_mask` that consensus actually compared.

## Contract surface

Writes:

- `register_spec(spec_key, rules_text, outcome_schema, evidence_mode, decision_deadline_unix)` creates an immutable public specification. The ID is creator-address plus normalized key; an exact duplicate is idempotent.
- `audit_spec(spec_id)` runs one conservative, network-consensus audit. The audit is immutable.

Important views:

- `get_spec(spec_id)` and `get_audit(spec_id)` return the canonical records.
- `has_resolvable_audit(spec_id)` is a status-only convenience view.
- `matches_resolvable_spec(spec_id, expected_spec_fingerprint)` returns `true` only when a `RESOLVABLE` audit is bound to the expected compact SHA-256 fingerprint.
- `get_spec_count` / `get_spec_id` and `get_audit_count` / `get_audit_id` allow deterministic discovery.
- `get_policy()` exposes the immutable policy revision and schema versions.

## Safe downstream use

Use `matches_resolvable_spec` for an automated downstream gate. The fingerprint
is included in both the canonical specification and audit. It commits to the
fingerprint schema, creator, normalized key, policy version, rules, outcomes,
evidence mode, and deadline. A downstream contract **must independently
precompute and hard-code** that expected fingerprint and pin the QuestionZero
deployment address before activation. Reading the fingerprint from an arbitrary
record and immediately passing it back provides no substitution protection. The shorter
`has_resolvable_audit` view deliberately does **not** mean activation is safe on
its own. A consumer should pin the QuestionZero deployment address and use the
bound view or independently enforce every expected field. It should act only
after finality.

```text
audit = QuestionZero.get_audit(spec_id)
spec  = QuestionZero.get_spec(spec_id)

require audit.schema == expected_audit_schema
require audit.policy_version == expected_policy_version
require audit.verdict == "RESOLVABLE"
require audit.spec_fingerprint == expected_spec_fingerprint
require spec.spec_fingerprint == expected_spec_fingerprint
```

Fingerprint construction is versioned and deterministic. Normalize the creator
to lowercase; normalize the key, rules, outcomes, and evidence mode exactly as
registration does; then canonicalize this object with JSON keys sorted and
separators `,` and `:` (no extra whitespace):

```json
{"creator":"<lowercase address>","decision_deadline_unix":1900000000,"evidence_mode":"<normalized mode>","outcome_schema":"<normalized labels>","policy_version":1,"rules_text":"<normalized ASCII rules>","schema":"questionzero/spec-fingerprint/v1","spec_id":"<lowercase creator>:<normalized key>","spec_key":"<normalized key>"}
```

Hash the canonical JSON's ASCII bytes with SHA-256 and prefix the lowercase hex
digest with `sha256:`. The test suite includes a fixed digest vector so other
languages can verify compatible implementations.

The contract's audit is a structural, consensus-backed signal—not legal advice,
an oracle for real-world facts, or a guarantee that a human will agree with the
classification.

## Local verification

The project uses a pinned GenVM runner in
[`contracts/question_zero.py`](contracts/question_zero.py). On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\genvm-lint.exe check contracts\question_zero.py --json
.\.venv\Scripts\genvm-lint.exe typecheck contracts\question_zero.py --strict --json
.\.venv\Scripts\python.exe -m pytest tests\direct -q -p no:cacheprovider
```

For five-validator local consensus, start GLSim in one terminal:

```powershell
.\.venv\Scripts\python.exe tests\run_glsim.py --port 4000 --validators 5 --no-browser
```

Then run this in another:

```powershell
.\.venv\Scripts\gltest.exe tests\integration -v -s --network localnet -p no:cacheprovider
```

`tests/gltest_windows_compat.py` is test-only code for two upstream Windows
runner issues; it is never deployed.

## Deployment sequence

1. Install the pinned local CLI and deployment dependencies with `pnpm install`.
2. Create or select an encrypted GenLayer CLI account. Keep its password and private key outside this repository.
3. Select StudioNet, set the fail-closed stage in the same PowerShell session,
   and deploy:

   ```powershell
   pnpm exec genlayer network set studionet
   $env:QUESTIONZERO_DEPLOY_STAGE = 'studionet'
   pnpm run deploy
   ```

4. Register/audit a public fixture and inspect the finalized StudioNet transactions.
5. Only then select Bradbury, change the stage, and repeat:

   ```powershell
   pnpm exec genlayer network set testnet-bradbury
   $env:QUESTIONZERO_DEPLOY_STAGE = 'bradbury'
   pnpm run deploy
   ```

The deployment script requires the explicit stage variable and rejects the
wrong chain ID or RPC host (Bradbury and Asimov share chain ID `4221`). Its only
constructor argument is the immutable policy version. It
prints the transaction hash immediately, then accepts an address only after
`FINALIZED` and `FINISHED_WITH_RETURN`, and reports the deployed source hash.

## Verified deployments

Both deployments use policy version `1` and reviewed contract source SHA-256
`1B8672668E7AFB0F14205D98A53D2B64BF250A7323A9708ADC2A5F49E5B3A6B5`.

- **StudioNet:** [contract](https://explorer-studio.genlayer.com/address/0xBc94C882f9a8269A668B07378780E5E2A8689E3A), [deployment](https://explorer-studio.genlayer.com/tx/0x0a42866afc6e77a5f9b19b612c53c757060ae3514a06336f2e1882332249013a), [registration](https://explorer-studio.genlayer.com/tx/0x143c69facc88014b51681279d0f284a94c0012bca349e3cd5c324796cc0eb829), and [audit](https://explorer-studio.genlayer.com/tx/0x1b9749c34d766bc256fde177aed6209641deb16e92f2e4da0ce97c64f3a21e23) are finalized. The audit returned `RESOLVABLE`, issue mask `0`, and the exact fingerprint `sha256:9529a17e3f1d4a1582947c8373d7f5f4967efd9683445f2742b8a3e7f143d53e` matched while a one-nibble alteration did not. Its final receipt recorded three `AGREE` votes and two `IDLE` validators after quorum.
- **Bradbury:** [contract](https://explorer-bradbury.genlayer.com/address/0xcD66c6384d0443746C79889507b6d85fb85Ffa80), [deployment](https://explorer-bradbury.genlayer.com/tx/0x1739fa5e356797ba41a6f2d2b4e38d11dc150d23f739b9fa06a7b73eb53f6525), [registration](https://explorer-bradbury.genlayer.com/tx/0x80e3f7a44ad33709b3144f1ef4359da7d319343d869dc2b0343623f1f863af86), and [audit](https://explorer-bradbury.genlayer.com/tx/0xf91b5e5e387c8cc55a542b29539ab8398e27262074b4fe4bc4433aebe728f792) are finalized with `FINISHED_WITH_RETURN`. Deployment and registration each finalized with five `AGREE` votes. The audit returned `RESOLVABLE`, issue mask `0`, and the exact fingerprint `sha256:84c22cd3e30a708fb6b829b2ab6aaa9136bac952a406dda59a9f309893edd137` matched while a one-nibble alteration did not; its final round recorded four `AGREE` votes and one `TIMEOUT`.

Machine-readable evidence is stored in
[`deployments/studionet.json`](deployments/studionet.json) and
[`deployments/bradbury.json`](deployments/bradbury.json).

## Privacy and limits

All registered specifications, outcomes, evidence modes, deadlines, creator
addresses, and audit records are public on-chain. Do not register private
commercial terms or personal data. LLM classification can differ across
validators. A different or invalid validator result produces a non-`AGREE`
vote; GenLayer's protocol quorum determines acceptance, after which protocol
finality rules apply.
The published Bradbury smoke audit finalized with four `AGREE` votes and one
`TIMEOUT`, so consumers must not interpret finality as
unanimous model agreement. See [SECURITY.md](SECURITY.md) for the threat model.

## License

[MIT](LICENSE)
