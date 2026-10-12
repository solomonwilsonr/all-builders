# Team Hashes: AI Builder Cup 2026

**Core project: SafeShelf Global** (theme: Retail & Commerce)

> SafeShelf checks any product listing and answers two questions: **Is it safe?** (hazards spotted in buyer reviews and photos before an official recall, plus recall and certification checks) and **Is it real?** (copied photos, an impossible price, a brand-new website). All of this runs on one product-identity engine that recognises the same product under different brand names. A SafeShelf agent (Google ADK) can also investigate for the shopper: it clicks through photos, reviews and seller details, checks official registries, answers questions in a chat, suggests a safer genuine alternative and watches products after purchase. It is accessible to every shopper: it works with screen readers and the keyboard, and it can read the answer aloud, in plain language or in Hindi.

Deadline: **Oct 18, 2026, 11:59 PM IST** (we aim for Oct 17).

## Files
| File | What it is |
|---|---|
| [`SAFESHELF.md`](SAFESHELF.md) | Full product and technical design, hackathon scope, demo, evaluation, build plan |
| [`SafeShelf_Global.pdf`](SafeShelf_Global.pdf) | The same document as a PDF |
| [`PROGRESS.md`](PROGRESS.md) | Everything done so far, the feasibility test results and next steps |
| [`PARALLEL_PLAN.md`](PARALLEL_PLAN.md) | Day-by-day plan for Person A (Brain) and Person B (Face), with time estimates and join points |
| [`MODULES.md`](MODULES.md) | The 19 build modules: steps, dependencies, prerequisites, done-when checks |
| [`feasibility/`](feasibility/) | Scripts for the feasibility test (CPSC recalls vs Amazon reviews) |
| [`BACKTEST.md`](BACKTEST.md) | Plan for the make-or-break backtest (do reviews warn before recalls?) |
| [`TOOLS.md`](TOOLS.md) | Google tools, data sources and open-source tools we plan to use |
| [`HACKATHON.md`](HACKATHON.md) | Rules, judging criteria, submission requirements, deck template, submission estimate |
| [`COMPETITOR_ENTRIES.md`](COMPETITOR_ENTRIES.md) | Public cup entries (~125, five scans) and the top-10 ranking with links |
| `Submission Template _ AI Builder Cup.pptx` | Official deck template |

## Next step
Make-or-break backtest (about 2 hours). Do hazard reviews and photos appear at least 2 weeks before past CPSC recalls? Does pooling evidence across rebranded twins make the warning earlier? See [`BACKTEST.md`](BACKTEST.md).

## Earlier research
Earlier work was ClearSight (satellite check, passed on Oct 11), SolventGate+, Witness, PitStop and the Retail/Media idea scan. It was removed from this branch but is kept in git:

```
git checkout archive/pre-safeshelf -- <path>
```
