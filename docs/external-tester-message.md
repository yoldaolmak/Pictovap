# External Tester Message

Copy and adapt this message when inviting a real person to try Pictovap.

---

**Subject:** Would you try a 5-minute demo of an open-source visual finishing tool?

Hi,

I'm working on Pictovap, an open-source tool that automates image selection and placement for content publishers. It analyzes a Markdown article, scores candidate images, and generates a placement plan — all locally, without needing any API keys or accounts.

I'd appreciate it if you could spend a few minutes trying the demo and letting me know what you think.

**What to do:**

```bash
python3 --version  # Python 3.10 or newer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pictovap==0.7.10
pictovap demo
```

**Try your own article (if possible):**

```bash
pictovap plan \
  --article path/to/your/article.md \
  --output my-plan.json \
  --report my-plan.md
```

**Then:**

- Open `my-plan.json` and `my-plan.md`. Does the structure make sense?
- Did the Visual Brief identify reasonable image slots for your article?
- Did anything crash or produce confusing output?

Please report the result in [issue #8](https://github.com/yoldaolmak/Pictovap/issues/8).
Redact private article content; the Python version, operating system, command,
and traceback (if any) are enough.

Any feedback at all is helpful — even "it didn't work on my machine" or "the output was confusing."

Thanks for your time.
