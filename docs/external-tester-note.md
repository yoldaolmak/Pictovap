# External Tester Note

Use this note when reaching out to 2–3 real people who might be willing to try Pictovap's demo. Copy and adapt as needed.

---

**Subject:** Would you try a 5-minute demo of an open-source visual finishing tool?

Hi,

I'm working on Pictovap, an open-source tool that automates image selection and placement for content publishers. It analyzes a Markdown article, scores candidate images, and generates a placement plan — all locally, without needing any API keys or accounts.

I'd appreciate it if you could spend a few minutes trying the demo and letting me know what you think.

**What to do:**

```bash
git clone https://github.com/yoldaolmak/Pictovap.git
cd Pictovap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
make demo
```

**Try your own article:**

```bash
python -m pictovap.demo --article path/to/your/article.md --output my-plan.json
```

**Then:**

- Look at the JSON output. Does the structure make sense?
- Did the Visual Brief identify reasonable image slots for your article?
- Did anything crash or produce confusing output?

If anything is unclear or broken, please open an issue on the repository:
https://github.com/yoldaolmak/Pictovap/issues

Any feedback at all is helpful — even "it didn't work on my machine" or "the output was confusing."

Thanks for your time.

---

*Note to maintainers: Do not describe anyone as a "user" or "tester" unless they actually respond and engage with the project. This note is an invitation, not a claim of adoption.*
