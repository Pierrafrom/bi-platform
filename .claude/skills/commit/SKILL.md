---
name: commit
description: Use this skill any time the user asks to commit, create a git commit, write a commit message, or stage and save changes. Writes clean Conventional Commits with atomic splitting when changes span multiple themes.
allowed-tools: Bash
---

# Clean Conventional Commits

Analyze staged/unstaged changes and produce well-formatted, atomic commits.

## Steps

### 1. Analyze
```bash
git status
git diff --staged --stat
git diff --staged
git diff --stat
git diff
```
Nothing to commit → inform the user and stop.

### 2. Respect pre-staged files
If `git diff --staged` shows changes, the user has explicitly staged specific files.
**Do not modify the staging area** — commit only what is already staged, unless the user asks to stage more.

If nothing is staged yet: cluster unstaged diffs by functional theme (auth, UI, API, DB, config, tests, docs…) and change type (feat, fix, refactor, chore…).

**One theme → one commit. Multiple distinct themes → propose a split plan and wait for confirmation before staging or committing.**

### 3. Message format — Conventional Commits
```
<type>(<scope>): <imperative title, 50 chars max>

<body: why + what, 72 chars/line, blank line after title>

<footer: Closes #N | BREAKING CHANGE: … | Co-authored-by: …>
```

**Types:** `feat` `fix` `refactor` `perf` `test` `docs` `style` `chore` `build` `ci` `revert`

**Title rules:** imperative ("Add", not "Added"), no period, no capital after the colon, English by default.

**Body rules:** explain *why* and *what*, not how (the diff shows how). Mention impacts and side effects.

### 4. Stage and commit
Stage specific files only — never blind `git add .`.

**Show the full commit message to the user and wait for their approval before executing the commit command.**

After approval: run `git commit`. If the commit fails (e.g. pre-commit hook blocks it): stop immediately and display the full error output to the user — do not retry or bypass hooks.

Confirm success with `git log --oneline -1`.

### 5. Summary
```
N commit(s) created
────────────────────────
<hash> <title>
```
Then ask: "Push to remote? (`git push origin <branch>`)"

## Examples
```
feat(auth): add Google OAuth2 login

Adds /auth/google and /auth/google/callback via passport-google-oauth20.
User profile created automatically on first login.

Closes #42
```
```
chore(deps): upgrade Next.js 14 → 15

App Router now requires Suspense around useSearchParams(). Updated 3 layouts.

BREAKING CHANGE: layouts using useSearchParams must wrap with Suspense
```
