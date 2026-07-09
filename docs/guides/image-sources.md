# Image Sources

You do not need image provider credentials to run the local demo.

The demo uses deterministic local/mock candidates to execute the pipeline safely without external dependencies.

## Adapters

Real image providers such as Openverse, Unsplash, DepositPhotos, or private archives should be connected through image source adapters. Provider credentials must live in `.env` or another local secret store and must never be committed.

### Current Implementation Status

- **Implemented**: Local mock folder (used in the credential-free demo).
- **Planned**: Openverse (free, CC-licensed images).
- **Planned**: Unsplash.
- **Planned**: DepositPhotos (*Planned adapter, not active in the credential-free demo.*)
- **Planned**: Visual Memory (local semantic private archive).

## Provenance Packs

Every image that Pictovap evaluates and selects MUST generate a Provenance Pack. 

This pack tracks:
- Image origin and Provider ID
- License status and rights model
- Processing actions (resizing, formatting)
- Cryptographic hash

Each selected/downloaded asset must create a Provenance Pack to ensure a strict audit trail before CMS placement.
