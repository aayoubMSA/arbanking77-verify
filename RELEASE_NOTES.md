# ArBanking77-Verify v0.1.0 — Release Candidate Notes

## Status

Archival release candidate prepared during WP4. No public GitHub release, Zenodo
record, DOI, Software Heritage archival request, or external disclosure is claimed
at this stage.

## Included capabilities

- machine-readable benchmark-state profiles;
- SHA-256 and Git blob SHA-1 source identity checks;
- safe ZIP-member verification for the recovered participant archive;
- fail-closed materialization;
- multiplicity-preserving historical/current text comparison;
- cumulative normalization ladder (`exact`, `nfkc_ws`, `arabic_light`,
  `arabic_light_punct`);
- machine-readable comparison and source-manifest outputs;
- offline rerun using previously verified cached sources;
- deterministic unit tests and a network-backed frozen-evidence CI gate.

## Built-in ArBanking77 evidence profiles

- `ARB77-AraFinNLP2024-participant-input`
- `ARB77-current-public-2026`

For these profiles, the verified historical/current comparison reproduces:

- exact: shared 11,110; historical unmatched 611; current-only 850;
- NFKC + whitespace: shared 11,180; historical unmatched 541; current-only 780;
- Arabic-light: shared 11,180; historical unmatched 541; current-only 780;
- Arabic-light + punctuation: shared 11,220; historical unmatched 501;
  current-only 740.

These values are compatibility observables. They do not establish organizer intent,
leaderboard invalidity, dialect attribution of unmatched participant rows, or the
correctness of unrecovered gold data.

## Redistribution boundary

The package contains software, profiles, tests, metadata and documentation only.
It does not redistribute ArBanking77 datasets, the participant task archive, model
weights, private manuscripts, credentials, or restricted research material. Public
source artifacts are acquired by the user/tool from their declared URLs and checked
against immutable identifiers.

## Runtime

Python 3.11+; standard library only.

## License

MIT for the ArBanking77-Verify software package. Third-party datasets and source
artifacts remain under their own upstream terms and are not relicensed by this
package.
