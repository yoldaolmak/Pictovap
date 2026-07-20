# How to Automate WordPress Gutenberg Image Uploads with Python

If you run a WordPress blog or newsroom, you already know the most tedious part of publishing isn't writing the content—it's formatting the images. 

Every publisher runs the same manual routine before an article can go live: finding images that fit the text, checking licenses, downloading, resizing, writing alt text, uploading to the WordPress media library, and placing Gutenberg blocks. This process scales linearly with your publishing volume. It takes 15-30 minutes per article, forever.

In this tutorial, we will show you how to completely automate the WordPress Gutenberg image pipeline using **Pictovap**, an open-source orchestration tool for publishers.

## What is Pictovap?

[Pictovap](https://github.com/yoldaolmak/Pictovap) is a CMS-neutral visual planning framework. Instead of being a closed SaaS product, it runs directly in your CI/CD pipeline or local environment. 

It reads your Markdown article, decides where images are needed based on your headings, searches providers (like Unsplash or Pexels) for appropriate stock photos, and generates a plan that gets pushed directly to your WordPress site.

## Step 1: Install Pictovap

You can install Pictovap directly from PyPI. You need Python 3.10 or higher.

```bash
pip install pictovap
```

## Step 2: Configure Your Publisher Profile

Pictovap uses a `profile.yaml` to understand your blog's rules. This dictates how many images to find and what resolution to use.

Create a `publisher.yaml` file:

```yaml
# publisher.yaml
language: "en"
resolution: "1200x800"
max_images_per_article: 5
```

## Step 3: Set Your API Keys

You will need an application password from your WordPress site, and optionally an API key for your image source (e.g., Unsplash).

```bash
export WP_URL="https://yourblog.com"
export WP_TOKEN="your-wordpress-application-password"
export UNSPLASH_API_KEY="your-unsplash-key"
```

## Step 4: Run the Automation Pipeline

With your credentials set, you can run the entire pipeline with a single command. 
First, we generate the plan:

```bash
pictovap plan \
  --article draft-post.md \
  --profile publisher.yaml \
  --provider unsplash \
  --provider-option api_key=@UNSPLASH_API_KEY \
  --output plan.json
```

This reads `draft-post.md`, finds the best images from Unsplash, and writes the decisions to `plan.json`.

Now, push it to WordPress:

```bash
pictovap publish \
  --plan plan.json \
  --cms wordpress \
  --cms-option api_url=$WP_URL \
  --cms-option api_token=@WP_TOKEN
```

Pictovap will automatically upload the images to your Media Library, generate SEO-friendly Alt Text, and insert the `wp:image` Gutenberg blocks directly into your post!

## Using it in GitHub Actions

You don't even need to run this locally. Pictovap provides an official GitHub Action and a Pre-commit hook. 
You can add it to your repository so every time you commit a Markdown file, the images are planned and placed automatically.

```yaml
name: "Visual Planning"
on: [push]

jobs:
  plan_images:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: yoldaolmak/Pictovap@v0.7.5
        with:
          article: 'posts/*.md'
```

## Stop Uploading Images Manually

By integrating Pictovap into your publishing workflow, you ensure consistent SEO metadata, legal image provenance, and you save hundreds of hours of editorial time. 

Check out the [GitHub Repository](https://github.com/yoldaolmak/Pictovap) to get started!
