# External Adoption Playbook

Welcome to Pictovap! This playbook is designed to help you quickly understand, run, and test Pictovap in your own environment without needing API keys, cloud accounts, or complex setup.

## 1. Who Should Try Pictovap First

Pictovap is an early-stage open-source infrastructure project. You are an ideal early tester if you are:
- An independent publisher
- A WordPress blogger
- A travel or recipe publisher
- A local guide publisher
- Part of a small editorial team seeking to automate visual finishing

*Note: Pictovap does not currently provide a consumer-friendly UI. It is for publishers comfortable running Python scripts or integrating APIs.*

## 2. What You Can Test in 10 Minutes

In just 10 minutes, without any credentials, you can:
- Clone the repository and install it locally.
- Run the core pipeline (Visual Brief → Fit Score → Provenance Pack → CMS Placement).
- Test how Pictovap evaluates images against a mock dataset.
- Run a custom Markdown article through the engine.

## 3. Run the Default Demo

Clone the repo, set up a virtual environment, and run the standard demo:

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .

make demo
```

This runs the engine against `examples/sample-article.md` using deterministic scoring.

## 4. Try Your Own Markdown Article

You can test Pictovap against your own content:

```bash
python -m pictovap.demo --article path/to/your/article.md --profile examples/profiles/sample-publisher.yaml --output my-plan.json
```

It will parse your article, identify sections, and evaluate mock candidates for placement.

## 5. Create a Publisher Profile

Publisher profiles tell Pictovap about your site's tone and requirements. Try creating your own profile based on `examples/profiles/sample-publisher.yaml`. Copy the file, edit the tone rules, and pass it to the demo using the `--profile` flag.

## 6. Review the Output JSON

Open the generated JSON (for example, `sample-output.json` in your current
directory or your custom output). Look for the four primitives:
- `visual_brief`: What the engine thinks your article needs.
- `fit_scores`: How candidate images were ranked.
- `provenance_packs`: The selected images and their audit trail.
- `cms_placement`: The final placement instructions.

## 7. Report a Useful Issue

If you encounter bugs or confusing outputs, please open an issue. Good issues include:
- The `visual_brief` completely misunderstood my article structure.
- The demo crashed when parsing a specific Markdown element.

## 8. Contribute a Sample Article/Profile

Help us make Pictovap more publisher-agnostic! If you have a unique article format (e.g., a heavily structured recipe), consider opening a Pull Request to add it to `examples/articles/` along with a corresponding profile in `examples/profiles/`.

## 9. Request an Adapter

Pictovap is built around adapters. If you use a specific image source (like Openverse) or CMS (like Ghost or Strapi), open an "Adapter Request" issue. Check our existing requests before submitting.

## 10. Current Limitations

- The credential-free demo relies on mock assets and deterministic scoring, not live APIs.
- Real API runs (with external model providers) require configuration not covered in this quick playbook.
- We currently only offer a WordPress CMS adapter (reference implementation).
- Pictovap has no external adoption yet; you are on the bleeding edge.
