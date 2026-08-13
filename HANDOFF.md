# QuestionZero handoff

This is a contract-only project. Its standalone GitHub repository currently
remains private; no frontend, provider adapter, database, or hosted service is
required.

## Standalone repository handoff

The intended release artifact is the tagged standalone GitHub repository. The
current private repository and its file URLs must remain marked `PENDING` and
must not be submitted to the Portal until they are public and resolve without
authentication. The repository must exclude `node_modules`, `.venv`,
`.artifacts`, `artifacts`, `.env`, `.pytest_cache`, `.gltest_cache`,
`__pycache__`, `*.pyc`, logs, `.tools`, compiled deployment scripts, and wallet
material. Dependencies are reproducible from `requirements.txt`, `package.json`,
and `pnpm-lock.yaml`.

### `v0.1.0` release state

The release artifact is the annotated `v0.1.0` tag on the clean standalone
QuestionZero release root. It includes the finalized StudioNet and Bradbury
records and their matching documentation. The release is valid only when all of
these checks hold:

1. `git rev-parse --show-toplevel` resolves to
   `C:/Users/leoki/Genlayer/QuestionZero`, not its parent workspace.
2. The documented local checks pass, both deployment JSON files parse, the
   Portal copy remains 993 characters, the packaged contract remains 19,705
   bytes with the SHA-256 below, and tracked files contain no ignored artifacts
   or secrets.
3. The worktree is empty and local `main`, remote `main`, and the peeled
   `v0.1.0` commit are the same release commit.
4. The annotated tag is present on the remote. Verify its tag object and peeled
   commit with `git ls-remote --tags origin v0.1.0 v0.1.0^{}`. Never move or
   reuse this release tag.

The repository remains private, so the immutable `blob/v0.1.0/...` links in
`SUBMISSION.md` are reviewer-inaccessible and remain marked `PENDING`. Public
visibility is a separate, future submission gate: after it is explicitly
authorized, verify the repository and every tagged evidence URL without
authentication before submitting them to the Portal.

## Reproduce local verification

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\genvm-lint.exe check contracts\question_zero.py --json
.\.venv\Scripts\genvm-lint.exe typecheck contracts\question_zero.py --strict --json
.\.venv\Scripts\python.exe -m pytest tests\direct -q -p no:cacheprovider
```

For the network simulation, use the two-terminal commands in [README.md](README.md).

## Deployment order

1. Run `pnpm install` and `pnpm run typecheck:deploy`. This installs the pinned
   project-local GenLayer CLI.
2. Create or select an encrypted CLI account outside the project. Do not put a
   private key, recovery phrase, keystore, or account password into the repository.
3. Set the CLI network to StudioNet and set the stage in the same PowerShell
   session:

   ```powershell
   pnpm exec genlayer network set studionet
   $env:QUESTIONZERO_DEPLOY_STAGE = 'studionet'
   ```

4. Deploy and exercise a public fixture on StudioNet first. Record the finalized
   transaction, address, a `register_spec` transaction, and an `audit_spec`
   transaction.
5. Inspect the finalized StudioNet evidence.
6. Only then select Bradbury, set the new stage, and repeat the same verification:

   ```powershell
   pnpm exec genlayer network set testnet-bradbury
   $env:QUESTIONZERO_DEPLOY_STAGE = 'bradbury'
   ```

The source hash to confirm before deployment is recorded in [SECURITY.md](SECURITY.md).

## Included live evidence

The package includes finalized, machine-readable records for both deployments:

- [StudioNet contract](https://explorer-studio.genlayer.com/address/0xBc94C882f9a8269A668B07378780E5E2A8689E3A)
- [Bradbury contract](https://explorer-bradbury.genlayer.com/address/0xcD66c6384d0443746C79889507b6d85fb85Ffa80)

Both deployments and both smoke-test records belong to
`0x797d3B25fB2cCA0Ff93F60df1910267f3822D655`. StudioNet finalized a
`RESOLVABLE` audit with issue mask `0` and three `AGREE` votes plus two `IDLE`
validators after quorum. Bradbury finalized the same bounded result with four
`AGREE` votes plus one `TIMEOUT`; its deployment and registration were each
five-of-five `AGREE`.

Both records, the deployment guard, and the packaged contract must report
source SHA-256
`1B8672668E7AFB0F14205D98A53D2B64BF250A7323A9708ADC2A5F49E5B3A6B5`.
Their registration and audit transactions are linked from [README.md](README.md).
