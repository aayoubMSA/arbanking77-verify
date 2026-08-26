# ArBanking77-Verify — Tool Positioning

ArBanking77-Verify is a compact reference implementation of a state-profile and
compatibility contract, instantiated for ArBanking77.

It is not a replacement for DVC, DataLad, Croissant, Frictionless, or dataset
cards.

## Boundary against neighboring tools

| Tool / standard | Primary role | What ArBanking77-Verify adds here |
|---|---|---|
| DVC | data/version and pipeline management | compatibility decision between independently identified benchmark states |
| DataLad | dataset versioning/distribution/provenance | lightweight verification over already-existing external artifacts |
| Croissant | machine-readable dataset metadata | executable cross-state compatibility evidence |
| Frictionless | tabular schema/package validation | historical/current state comparison |
| Hugging Face Dataset Cards | human-readable/structured dataset documentation | byte-pinned state identity and compatibility evidence |

## Engineering contribution

The release combines:

1. explicit benchmark-state profiles;
2. immutable source bindings;
3. fail-closed materialization;
4. multiplicity-preserving cross-state matching;
5. a declared normalization ladder;
6. machine-readable evidence for compatibility decisions.

The implementation intentionally avoids pipeline orchestration, dataset hosting,
large-file storage, generic metadata governance, and automatic data repair.
