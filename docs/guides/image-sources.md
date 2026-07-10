# Image Sources

You do not need image provider credentials to run the local demo.

The demo uses deterministic local/mock candidates to execute the pipeline safely without external dependencies.

## Adapters

Real image providers such as Openverse, Unsplash, DepositPhotos, or private archives should be connected through image source adapters. Provider credentials must live in `.env` or another local secret store and must never be committed.

### Current Implementation Status

- **Implemented**: Local folder (`PICTOVAP_LOCAL_IMAGE_DIR`) — also what the
  credential-free demo uses, via deterministic mock candidates.
- **Implemented**: Unsplash (`UNSPLASH_ACCESS_KEY`).
- **Implemented**: DepositPhotos (`DEPOSIT_API_KEY`).
- **Implemented**: Openverse (no key required — free, CC-licensed images).
- **Implemented**: Pexels (`PEXELS_API_KEY`).
- **Open for contribution**: Pixabay, Wikimedia Commons — see
  [Good First Issues](../contributing/good-first-issues.md).

See [Image Source Adapters](../adapters/image-sources.md) for the exact interface
contract and how to write a new one.

## Provenance Packs

Every image that Pictovap evaluates and selects MUST generate a Provenance Pack. 

This pack tracks:
- Image origin and Provider ID
- License status and rights model
- Processing actions (resizing, formatting)
- Cryptographic hash

Each selected/downloaded asset must create a Provenance Pack to ensure a strict audit trail before CMS placement.
