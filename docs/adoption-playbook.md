# Pictovap Adoption Playbook

Welcome to Pictovap. If you are reading this, you are likely among the first external users trying this project outside of its original dogfooding environment. 

This playbook is designed to help you understand if Pictovap is right for you, and how you can try it without complex setup or private credentials.

## Who Should Try Pictovap First?

Pictovap is an early infrastructure project. You should consider trying it if you belong to one of these groups and are comfortable with a command-line interface:
* Independent publishers
* WordPress bloggers
* Travel publishers
* Recipe publishers
* Local guides
* Affiliate publishers
* Small editorial teams

## What You Can Do in 10 Minutes

Without needing any API keys or CMS credentials, you can:
1. Clone the repository and install the dependencies.
2. Run the local deterministic demo to see how the engine scores and selects images.
3. Test the engine against one of your own Markdown articles to see what visual brief it generates.

## How to Run the Demo

Run the credential-free demo using the provided mock data:
```bash
make demo
```
This runs a complete simulation of the pipeline (analysis, selection, provenance tracking, and placement planning) and outputs a JSON file with the results.

## How to Test Your Own Markdown Article

You can pass your own article to the demo to see how Pictovap parses its structure and generates a visual brief.

```bash
python -m pictova.demo --article path/to/your/article.md --output my-plan.json
```
*Note: This mode still uses the deterministic local mock image candidate pool, so the selected images will be placeholders, but the generated slots and placement instructions will be specific to your text.*

## How to Create a Publisher Profile

Publisher profiles define your site's specific rules (e.g., maximum images per post, preferred image aspect ratios, quality thresholds). Look at `examples/profiles/sample-publisher.yaml` to understand the schema. You can create your own YAML file and pass it to the demo:

```bash
python -m pictova.demo --article my-article.md --profile my-profile.yaml --output my-plan.json
```

## How to Use Local Image Metadata

If you want to simulate selection with your own images, you can place a JSON file containing mock image metadata into the pipeline. (Detailed documentation on the local provider adapter is pending).

## How to Request a CMS Adapter

Currently, only the WordPress adapter is production-ready. If you use a different CMS (like Ghost, Strapi, or Hugo), please check the [Starter Issues](contributing/starter-issues.md) list. You can open an issue on GitHub requesting an adapter, providing details about the target CMS's REST or GraphQL API for media uploading and block injection.

## How to Open a Useful Issue

If you encounter a bug or have a feature request:
1. Use the provided Issue Templates in the repository.
2. Include the output of the demo run or the specific error trace.
3. If reporting an issue with a specific article structure, include an anonymized excerpt of the Markdown.

## How to Contribute a Sample Article or Profile

We welcome PRs that add diverse content types to the `examples/` directory. If you have a specific editorial format (like a complex recipe or a product review) that Pictovap struggles to parse, contributing a sanitized version of it helps improve the engine.
