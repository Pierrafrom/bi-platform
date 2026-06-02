---
name: pr
description: Use this skill when the user wants to open a pull request, create a PR, submit their branch for review, or prepare a GitHub pull request. Checks pipeline status, enforces PR template, and flags blockers before opening.
allowed-tools: Bash
---

# Pull Request — Pre-flight + Creation

Verify the branch is ready, then create a well-formed PR following the repo's template and GitHub conventions.

## Step 1 — Pre-flight checks

Run ALL of the following commands and output their results. **Do not create the PR yet. Wait to evaluate the output.**

```bash
# 1. Uncommitted changes
git status --short

# 2. Unpushed commits
git log origin/$(git rev-parse --abbrev-ref HEAD)..HEAD --oneline 2>/dev/null || echo "no upstream set"

# 3. Discover default branch and check if current branch is behind
default_branch=$(git remote show origin 2>/dev/null | sed -n '/HEAD branch/s/.*: //p')
git fetch origin
git log HEAD..origin/${default_branch} --oneline

# 4. Check for merge conflicts in working tree
git diff --name-only --diff-filter=U

# 5. CI status (skip gracefully if gh CLI unavailable or CI not configured)
gh run list --branch $(git rev-parse --abbrev-ref HEAD) --limit 5 2>/dev/null || echo "CI check unavailable"

# 6. PR template
ls .github/PULL_REQUEST_TEMPLATE* 2>/dev/null || ls .github/pull_request_template* 2>/dev/null || echo "no template"
```

## Step 2 — Evaluate blockers

**Hard blockers — stop and warn the user, do not proceed:**
- Uncommitted changes exist (Step 1 output is non-empty)
- Branch is behind base branch (Step 3 output has commits)
- Merge conflicts detected (Step 4 output is non-empty)

**Soft condition — use `--draft` flag:**
- CI is still running or the last run failed → create a draft PR instead of a ready-for-review PR
- If `gh run list` failed or returned no output → treat CI as passed, do not block

If no hard blockers: proceed to Step 3.

## Step 3 — Write PR description

If a template was found → fill every section, leave no placeholder unfilled.
If no template → use this structure:

```markdown
## Summary
<!-- What this PR does and why -->

## Changes
<!-- Bullet list of key changes grouped by theme -->

## Testing
<!-- How it was tested: unit, integration, manual steps -->

## Screenshots / Demo
<!-- If UI changes -->

## Breaking changes
<!-- Any API/contract changes, migration steps needed -->

## Related issues
Closes #N
```

**Title format:** same as Conventional Commits → `feat(scope): short imperative title`

## Step 4 — Create the PR

```bash
gh pr create \
  --title "<type>(<scope>): <title>" \
  --body "<filled description>" \
  --base ${default_branch}
  # add --draft if CI is not green
```

**If `gh` is not available:**
Extract owner and repo from the remote URL:
```bash
git remote -v | grep origin | head -1
# e.g. origin  git@github.com:owner/repo.git (fetch)
```
Then output this link (URL-encode title and body — replace spaces with `%20`, newlines with `%0A`, `#` with `%23`):
`https://github.com/<owner>/<repo>/compare/<default_branch>...<branch>?quick_pull=1&title=<encoded-title>&body=<encoded-body>`

## Post-creation checklist (show to user)
- [ ] Reviewers assigned
- [ ] Labels applied (feature / bug / chore…)
- [ ] Milestone set if relevant
- [ ] Linked to project board
- [ ] CI passes — check `gh run watch` or the Actions tab
