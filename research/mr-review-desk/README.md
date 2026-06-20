# Mr. Review desk — the-stable

Where the keeper leaves notes and review requests for the cold-review dispatcher
(`~/personal-projects/review-scheduler`). The dispatcher watches `research/review-bundle/*`
for new rounds and, for each, runs a **fresh cold reviewer** scoped to a clone of this
(public-tracked) repo only — the keeper's private cognition tree (`improvements/`, the
memory-management instance) is gitignored and never reaches the reviewer's desk. The
standing brief is injected as the reviewer's system prompt (method-as-text).

**Cross-project context:** this project is registered with `context_repos: [worldweaver]`,
so the reviewer also mounts the **worldweaver** research program read-only — the parent
pen-vs-substrate work this experiment claims to be a frontier of. The reviewer reviews only
*this* repo's round; worldweaver is context for the frontier judgment.

## To request a review
- **Auto:** publish a round under `research/review-bundle/<date-name>/` with a `REVIEW-PROMPT.md`,
  commit it; the dispatcher picks it up on its next poll.
- **By hand / amendment:** drop a request in the dispatcher's `requests/` queue (see its README).

Reviews land in `research/mr-review-history/<date>-mr-review-feedback-N.md`, preserved on the
record like worldweaver's rounds — including the ones that go against us.
