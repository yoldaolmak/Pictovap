---
name: External validation report
about: Report a real Pictovap run without sharing private article content
title: '[VALIDATION] '
labels: 'feedback, needs external validation'
assignees: ''
---

Thank you for trying Pictovap with a real article or CMS workflow.

Use this template from:
https://github.com/yoldaolmak/Pictovap/issues/new?template=external_validation.md

Generate a safe summary:

```bash
python -m pip install --upgrade pictovap
pictovap plan --article path/to/article.md --output my-plan.json --report my-report.md
pictovap feedback --plan my-plan.json --format markdown
```

Paste the generated Markdown below. It includes coarse OS and Python metadata,
but excludes article text, private paths, image URLs, profile names, and
credentials.

## Pictovap External Validation

### Environment

- Pictovap version:
- Python version:
- OS:

### Anonymous Plan Summary

- Article language:
- Sections:
- Image slots:
- Candidates evaluated:
- Scored candidates:
- Selected images:
- Placements:
- Provider mode:

### Result

- [ ] The command completed successfully.
- [ ] The visual slots matched the article structure.
- [ ] The report was clear enough for editorial review.
- [ ] I found a bug or confusing output.

### Notes

Do not paste private article text, private paths, image URLs, or credentials.
