# ArBanking77-Verify — Tool Positioning

**Purpose of this note:** define the narrow engineering contribution and avoid
claiming that ArBanking77-Verify replaces established data-management or
metadata tools.

Sources were re-checked against official documentation on 2026-08-25.

## Boundary against existing tools

| Tool / standard | Primary capability supported by its official documentation | What ArBanking77-Verify adds in this paper |
|---|---|---|
| DVC | Git-like data/version management for data and ML projects | A frozen, paper-specific compatibility decision between independently recovered benchmark states, with explicit source identities and multiplicity-preserving record matching |
| DataLad | Version-controlled datasets, source tracking, distribution, and provenance capture | A lightweight verifier that can operate on already-existing external Git artifacts without requiring those historical states to have been managed in DataLad beforehand |
| Croissant 1.1 | Standardized machine-readable dataset metadata, provenance, interoperability, and governance | An executable state-comparison rule over two concrete recovered benchmark profiles; the profile schema is complementary and could later be mapped to richer Croissant provenance |
| Frictionless Framework | Validation of tabular resources/packages, schemas, metadata, and data-quality constraints | Cross-state historical/current compatibility testing rather than validating one table/package against a schema |
| Hugging Face Dataset Cards | Human-readable dataset documentation plus structured Hub metadata | Byte-pinned historical-state reconstruction and executable compatibility evidence; a card can document a state but does not itself establish cross-version equivalence |

## Claim discipline

ArBanking77-Verify should be described as:

> a compact reference implementation of the paper's state-profile and
> compatibility contract, instantiated for ArBanking77.

It should **not** be described as a general replacement for DVC, DataLad,
Croissant, Frictionless, or dataset cards.

The engineering novelty is the combination of:

1. explicit benchmark-state profiles;
2. immutable source bindings;
3. fail-closed materialization;
4. multiplicity-preserving cross-state matching;
5. a declared normalization ladder;
6. machine-readable evidence for compatibility decisions.

The current release candidate intentionally avoids pipeline orchestration,
dataset hosting, large-file storage, generic metadata governance, and broad data
quality repair.

## Official references

- DVC: https://dvc.org/
- DataLad Handbook: https://handbook.datalad.org/
- MLCommons Croissant: https://mlcommons.org/working-groups/data/croissant/
- Croissant 1.1 announcement: https://mlcommons.org/2026/02/croissant-1-1-standard/
- Frictionless validation: https://framework.frictionlessdata.io/docs/guides/validating-data.html
- Hugging Face Dataset Cards: https://huggingface.co/docs/hub/datasets-cards
