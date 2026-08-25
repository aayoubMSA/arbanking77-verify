# ArBanking77-Verify v0.1

ArBanking77-Verify is a small, publication-oriented reference implementation for
checking whether two declared benchmark states are materially compatible for
record-level comparison.

The built-in profiles reproduce the paper's historical-vs-current ArBanking77
comparison. The state-profile contract is intentionally generic so the checker
can be reused with other tabular benchmark states without changing the core
comparison engine.

## What the tool does

1. validates a machine-readable state profile;
2. retrieves either local files or pinned public URLs;
3. verifies SHA-256 and/or Git blob SHA-1 identities when supplied;
4. safely reads an exact ZIP member without extracting the archive;
5. rejects Git LFS pointer files instead of mistaking them for dataset bytes;
6. checks declared row counts and text columns;
7. performs multiplicity-preserving multiset comparison through a fixed,
   cumulative normalization ladder;
8. emits machine-readable `comparison.json` and `source_manifest.json`.

A source-identity PASS means the tool used the declared bytes. It does **not**
prove that the upstream dataset is semantically correct.

## Dependencies

Python 3.11+; Python standard library only.

## Built-in profiles

- `profiles/ARB77-AraFinNLP2024-participant-input.json`
- `profiles/ARB77-current-public-2026.json`

The historical profile pins the participant archive by both SHA-256 and Git blob
SHA-1, and independently pins the embedded blind-test CSV by SHA-256. The
current-public profile pins every public dialect file by both SHA-256 and Git
blob SHA-1 at the manuscript's audited upstream commit.

No benchmark dataset bytes are redistributed with this software. The built-in
profiles materialize declared public sources at runtime and verify their identities
before comparison.

## Usage

Validate a profile:

```bash
python arbanking77_verify.py validate-profile \
  profiles/ARB77-AraFinNLP2024-participant-input.json
```

Materialize and verify one state:

```bash
python arbanking77_verify.py materialize \
  profiles/ARB77-current-public-2026.json \
  --out artifacts/current-public.json
```

Run the historical/current comparison:

```bash
python arbanking77_verify.py compare \
  --historical profiles/ARB77-AraFinNLP2024-participant-input.json \
  --current profiles/ARB77-current-public-2026.json \
  --out artifacts/comparison
```

Re-run without network access after sources have been cached:

```bash
python arbanking77_verify.py compare \
  --historical profiles/ARB77-AraFinNLP2024-participant-input.json \
  --current profiles/ARB77-current-public-2026.json \
  --cache .cache/arbanking77-verify \
  --offline \
  --out artifacts/comparison-offline
```

Hash a local artifact:

```bash
python arbanking77_verify.py hash path/to/file
```

## Output semantics

The normalization ladder is cumulative and explicit:

1. `exact`
2. `nfkc_ws`
3. `arabic_light`
4. `arabic_light_punct`

`shared_multiset_rows` preserves duplicate multiplicity. Therefore
`historical_unmatched` and `current_only` are not set-membership counts.

The tool does not infer dialect membership, causal mechanisms, or whether one
state is a deliberate replacement of another. Those remain scientific claims
that require independent evidence.

## Extending to another benchmark

Create another JSON profile conforming to `profile.schema.json`. A profile
declares:

- stable `profile_id`;
- benchmark and state role;
- text column and expected row count;
- one or more source files;
- immutable source identifiers when available;
- optional ZIP member.

No ArBanking77-specific branching exists in the comparison engine.

## Failure behavior

The CLI fails closed with a non-zero exit code for:

- hash mismatch;
- Git blob mismatch;
- missing archive member;
- unavailable uncached upstream source;
- Git LFS pointer content;
- malformed/missing CSV header or text column;
- unexpected row count;
- invalid profile structure.

UTF-8 BOM is accepted. Byte hashing is independent of platform newline
translation because files are hashed before text decoding.

## Tests

```bash
python -m unittest -v tests/test_arbanking77_verify.py
```

The release-candidate CI additionally builds a standalone whitelist package,
runs its unit tests from that package, performs the full network-backed
historical/current comparison, checks the frozen manuscript-level totals, and
verifies deterministic packaging.

## Release status

Version `0.1.0` is an archival **release candidate**. The source and packaging
have been prepared for a public software/DOI release, but no public repository,
Zenodo DOI, Software Heritage archival request, or external disclosure is claimed
until the explicit release gate is approved.
