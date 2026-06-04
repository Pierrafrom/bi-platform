---
name: git-sync
description: Use this skill when the user wants to pull remote changes, sync with the distant repo, update their local branch, or get a recap of what changed and who did what.
allowed-tools: Bash
---

# Sync & Recap

Pull all remote changes and produce a structured recap of what changed and who did it.

## State management

**Execute this process one step at a time.** If any step requires user input or encounters a stop condition, **halt all tool execution and respond to the user immediately.** Do not proceed to the next step until the user replies.

## Steps

### 1. Check local state
Run `git status`. If uncommitted changes exist: **stop and warn the user**. Offer to stash (`git stash`) or commit first.

### 2. Fetch and pull
```bash
OLD_HEAD=$(git rev-parse HEAD)
git fetch --all --prune
git pull --rebase
```
If a conflict occurs: stop, list conflicting files with `git diff --name-only --diff-filter=U`, guide resolution.

If the pull results in no new commits (HEAD equals `OLD_HEAD`): notify the user that the branch is already up to date and stop — skip the recap.

### 3. Cleanup stale local branches
```bash
git branch -vv | grep ': gone]'
```
If the command returns no output: notify the user that there are no stale branches and proceed to Step 4.
Otherwise show the list and ask confirmation before deleting.

### 4. Produce the recap

```bash
git log ${OLD_HEAD}..HEAD --pretty=format:"%h | %ad | %an <%ae> | %s" --date=short --name-only --reverse
```

Output format:

**Overview** — commits pulled, branches updated, branches pruned

**Commits** (oldest first) — hash · date · author · message · files touched

**By author** — name, commit count, areas touched, one-line summary of work

**By domain** — group changed files by folder/type; flag notable areas (new dependencies in `pyproject.toml`/`package.json`/`requirements.txt`, database migrations, CI/CD config changes, authentication logic, entry-point files)

**Watch out** — new dependencies, migrations, config changes, potential breaking changes
