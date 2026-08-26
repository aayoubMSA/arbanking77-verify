# ArBanking77-Verify v0.1.1

ArBanking77-Verify is a compact, publication-oriented reference implementation
for checking whether two declared benchmark states are materially compatible
for record-level historical comparison.

Version 0.1.1 is a publication-hygiene update of v0.1.0. The verifier logic,
normalization rules, source identities, and frozen comparison observables are
unchanged. This version removes stale pre-publication wording and aligns the
historical profile terminology with the manuscript's evidence boundary.

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

The historical profile pins a participant-retained task archive by SHA-256 and
Git blob SHA-1, and independently pins the embedded blind-test CSV by SHA-256.
It does not treat the participant artifact as organizer-certified gold or infer
dialect membership from QueryID.

The current-public profile pins every public dialect file by both SHA-256 and
Git blob SHA-1 at the manuscript's audited upstream commit.

No benchmark dataset bytes are redistributed with this software. The built-in
profiles materialize declared public sources at runtime and verify their
identities before comparison.

## Usage

Validate a profile:

```bash
python arbanking77_verify.py validate-profile profiles/ARB77-AraFinNLP2024-participant-input.json
```

Materialize and verify one state:

```bash
python arbanking77_verify.py materialize profiles/ARB77-current-public-2026.json --out artifacts/current-public.json
```

Run the historical/current comparison:

```bash
python arbanking77_verify.py compare --historical profiles/ARB77-AraFinNLP2024-participant-input.json --current profiles/ARB77-current-public-2026.json --out artifacts/comparison
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

The tool does not infer dialect membership, causal mechanisms, organizer intent,
score impact, leaderboard validity, or correctness of unrecovered gold data.

## Extending to another benchmark

Create another JSON profile conforming to `profile.schema.json`. A profile
declares a stable profile identifier, benchmark/state role, text column,
expected row count, one or more source files, immutable source identifiers when
available, and an optional ZIP member.

No ArBanking77-specific branching exists in the comparison engine.

## Failure behavior

The CLI fails closed with a non-zero exit code for hash mismatch, Git blob
mismatch, missing archive member, unavailable uncached upstream source, Git LFS
pointer content, malformed/missing CSV header or text column, unexpected row
count, or invalid profile structure.

UTF-8 BOM is accepted. Byte hashing is independent of platform newline
translation because files are hashed before text decoding.

## Tests

```bash
python -m unittest -v tests/test_arbanking77_verify.py
```

## Frozen reference observables

The bundled profiles reproduce:

- exact: shared 11,110; historical unmatched 611; current-only 850;
- NFKC + whitespace: shared 11,180; historical unmatched 541; current-only 780;
- Arabic-light: shared 11,180; historical unmatched 541; current-only 780;
- Arabic-light + punctuation: shared 11,220; historical unmatched 501; current-only 740.

## Release status

Version `0.1.1` is the sanitized archival successor to `v0.1.0`.
The earlier version remains part of the public version history and is not
rewritten.

- Public repository: `https://github.com/aayoubMSA/arbanking77-verify`
- Zenodo concept DOI: `10.5281/zenodo.22103289`
- Previous version DOI (`v0.1.0`): `10.5281/zenodo.22103290`

The v0.1.1-specific Zenodo DOI is recorded in Zenodo's version metadata when
the new version is published.
