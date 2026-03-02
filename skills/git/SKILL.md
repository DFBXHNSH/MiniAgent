---
name: git
description: Git operations for version control: commits, branches, merges, etc.
---

# Git Skill

## Overview

Use this skill when the user requests any Git operations including commits, branching, merging, history inspection, or conflict resolution.

## Common Git Operations

### Checking Status
```bash
git status
```

### Viewing History
```bash
# Show commit history with one line per commit
git log --oneline

# Show detailed history
git log

# Show file changes in a commit
git show <commit-hash>
```

### Staging and Committing
```bash
# Stage specific files
git add <file1> <file2>

# Stage all changes
git add .

# Commit with message
git commit -m "Your commit message"

# Amend the last commit (for fixing typos, not changing content)
git commit --amend
```

### Branching
```bash
# List branches
git branch

# Create new branch
git branch <branch-name>

# Switch to branch
git checkout <branch-name>

# Create and switch in one command
git checkout -b <branch-name>

# Delete branch
git branch -d <branch-name>
```

### Merging
```bash
# Merge branch into current branch
git merge <branch-name>

# View merge conflicts
git status

# After resolving conflicts, stage and commit
git add .
git commit
```

### Remote Operations
```bash
# Push changes to remote
git push

# Pull changes from remote
git pull

# Fetch all remote branches
git fetch --all

# Show remote branches
git branch -r
```

### Undoing Changes
```bash
# Unstage a file
git reset <file>

# Discard local changes to a file
git checkout -- <file>

# Reset to a previous commit (use with caution)
git reset --hard <commit-hash>

# Revert a commit (creates new commit that undoes changes)
git revert <commit-hash>
```

## Commit Message Format

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or tool changes

Examples:
```
feat(auth): add OAuth2 login support

fix(api): resolve null pointer exception in user lookup

docs(readme): update installation instructions
```

## Best Practices

1. **Commit Frequently**: Small, focused commits are easier to review and revert
2. **Write Clear Messages**: Explain why, not just what
3. **Use Meaningful Branch Names**: `feature/user-auth`, `bugfix/login-error`
4. **Don't Commit Unwanted Files**: Use `.gitignore` properly
5. **Pull Before Push**: Fetch and merge remote changes first
6. **Resolve Conflicts Promptly**: Don't let merge conflicts linger

## Conflict Resolution

When conflicts occur:

1. Open affected files and look for `<<<<<<<`, `=======`, `>>>>>>>` markers
2. Decide which version to keep or merge both
3. Remove the conflict markers
4. Stage the resolved files: `git add <file>`
5. Commit: `git commit`

Example conflict resolution:
```python
<<<<<<< HEAD
def calculate(x, y):
    return x + y
=======
def calculate(a, b):
    return a + b
>>>>>>> feature-branch
```

Resolved:
```python
def calculate(a, b):
    return a + b
```
