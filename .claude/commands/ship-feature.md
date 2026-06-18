---
description: Run a feature request through the planner -> coder -> tester -> reviewer pipeline end to end.
argument-hint: <feature description>
---

You are orchestrating the four-stage ship pipeline for this feature request:

> $ARGUMENTS

## Setup
1. Create the `.pipeline/` directory if it doesn't exist, and clear out any files left over from a previous run.
2. Write the feature request to `.pipeline/request.md`, including the current branch (`git branch --show-current`) and HEAD commit (`git rev-parse HEAD`).

## Run the stages in order — each one must finish and write its file before the next starts
1. **Plan** — launch the `pipeline-planner` agent (via the Task tool) with the feature request. It reads `.pipeline/request.md` and writes `.pipeline/specs.md`.
2. **Code** — launch the `pipeline-coder` agent. It reads `.pipeline/specs.md` and writes the code changes plus `.pipeline/changes.md`.
3. **Test** — launch the `pipeline-tester` agent. It reads `.pipeline/specs.md` and `.pipeline/changes.md`, writes tests, and writes `.pipeline/tests.md`.
4. **Review** — launch the `pipeline-reviewer` agent (read-only). It reads all three prior files plus the live `git diff`, and writes `.pipeline/review.md` with a verdict.

Pass each agent the paths of the files it should read rather than re-pasting their contents — the whole point of `.pipeline/` is that every stage hands context to the next through these files instead of through your own context window.

## Report back
After all four stages finish, read `.pipeline/review.md` and summarize for the human:
- The verdict (`APPROVE` / `REQUEST_CHANGES` / `BLOCK`)
- The files changed
- Anything under "Risks" or "Next action" that needs a human decision

Do not commit, push, or merge anything yourself. This pipeline only prepares a reviewed diff on the current branch — a human decides what happens to it next.
