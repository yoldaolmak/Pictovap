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
2. Read the completed standalone reference in `examples/adapters/pictovap-pixabay/`.
3. Add the in-tree provider at `src/pictovap/providers/pixabay.py`, including mocked success, empty-result, missing-key, and API-failure fixtures.
4. Run `pytest tests/unit -q` and validate the success fixture with `pictovap.testing.assert_image_source_contract`.

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
2. Read the completed standalone reference in `examples/adapters/pictovap-wikimedia/`.
3. Add the in-tree provider at `src/pictovap/providers/wikimedia.py`, preserving per-file license and attribution metadata and covering malformed items with mocked fixtures.
4. Run `pytest tests/unit -q` and validate the success fixture with `pictovap.testing.assert_image_source_contract`. (Wikimedia does not require an API key.)

Feel free to claim this below. Happy to help if you need pointers on the adapter protocol!
```
