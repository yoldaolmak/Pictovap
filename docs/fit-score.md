# Fit Score

The **Fit Score** primitive provides a transparent, auditable mechanism for evaluating candidate images against a `VisualBrief`. 

Instead of opaque "magic" matching, every image considered by the pipeline receives a broken-down score. This allows publishers to tune the weights of different dimensions according to their editorial guidelines.

## Dimensions

A `FitScore` evaluates:

1. **Contextual Relevance**: How well the image matches the overall article topic.
2. **Section Relevance**: How well it matches the specific `H2` or `H3` section it is targeted for.
3. **Technical Quality**: Resolution, aspect ratio, brightness, and contrast checks.
4. **Duplication Risk**: Has this image been used recently on the site?
5. **Source Trust**: Preference given to owned photography vs stock photography.
6. **License Confidence**: Verification that the image is safe to use commercially.
7. **CMS Suitability**: Does it fit the required dimensions for the CMS theme?

Images that fail critical checks (like licensing) are immediately dropped and logged with a `rejection_reason`.
