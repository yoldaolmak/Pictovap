# GitHub Issue Templates for Adapters

Copy and paste the markdown below into new GitHub Issues.

---

## Issue Title: `Support Pixabay as an image source adapter`

**Body:**

```markdown
Pictovap orchestrates publisher workflows, but different blogs and newsrooms rely on different image banks. I currently don't have native support for Pixabay, which is a common request for WordPress publishers looking for royalty-free stock.

I designed the adapter architecture specifically so that adding a new provider doesn't require touching the core engine. To save time, I've already scaffolded the boilerplate and tests for a Pixabay adapter in the repository.

If anyone uses Pixabay and wants to wire this up, it's a very straightforward first issue:

1. You can jump right into a pre-configured environment by clicking **Code -> Create codespace on main** (no local setup needed).
2. Open `examples/adapters/pictovap-pixabay/src/pictovap_pixabay/__init__.py`.
3. The `search_candidates` method is currently returning an empty list. All that's needed is to replace it with a standard API call to Pixabay.
4. Run `cd examples/adapters/pictovap-pixabay && pytest` to verify the contract passes.

Drop a comment if you're picking this up or if you run into any API quirks!
```

---

## Issue Title: `Support Wikimedia Commons as an image source adapter`

**Body:**

```markdown
Many open-source publishers and educational blogs prefer pulling images directly from Wikimedia Commons to ensure strict creative commons compliance. Pictovap currently doesn't have a built-in way to query Wikimedia.

Because Pictovap's core just consumes standardized image candidates, adding Wikimedia is isolated entirely to an adapter. I've already scaffolded the base plugin structure and the test contract in the repository.

If you're interested in connecting the Wikimedia API to the framework, this is ready to be picked up:

1. You can launch a ready-to-use dev environment by clicking **Code -> Create codespace on main** (it includes all dependencies and tests).
2. Open `examples/adapters/pictovap-wikimedia/src/pictovap_wikimedia/__init__.py`.
3. The `search_candidates` method is currently returning `[]`. It just needs to be replaced with a real request to the Wikimedia API. (Bonus: Wikimedia doesn't require an API key, so the credential handling is even simpler).
4. Run `cd examples/adapters/pictovap-wikimedia && pytest` to make sure it satisfies the adapter contract.

Feel free to claim this below. Happy to help if you need pointers on the adapter protocol!
```
