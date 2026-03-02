---
name: code-review
description: Review code for bugs, security issues, and best practices violations
---

# Code Review Skill

## Overview

Use this skill when the user asks you to review code for quality, bugs, security issues, or best practices violations.

## Review Checklist

When reviewing code, check for the following:

### 1. Correctness
- Logic errors or typos
- Off-by-one errors in loops
- Missing edge case handling
- Incorrect variable types or scope issues

### 2. Security Issues
- SQL injection vulnerabilities
- Cross-site scripting (XSS)
- Command injection
- Path traversal attacks
- Sensitive data exposure

### 3. Performance
- Unnecessary loops or computations
- Inefficient data structures
- Missing caching opportunities
- N+1 query problems in database code

### 4. Best Practices
- PEP 8 compliance for Python
- Proper error handling
- Meaningful variable names
- Code duplication
- Missing type hints (where applicable)

### 5. Maintainability
- Clear function/class documentation
- Appropriate code organization
- Test coverage considerations
- Configuration vs hardcoding

## Review Format

Structure your review as:

1. **Summary**: Brief overview of findings
2. **Critical Issues**: Bugs or security vulnerabilities that must be fixed
3. **Suggestions**: Improvements for performance or readability
4. **Best Practices**: Deviations from coding standards
5. **Positive Notes**: What the code does well

Be specific and actionable. Don't just say "fix this" - explain why and suggest how.

## Examples

### Good Review:
\`\`\`
**Summary**: The function handles user authentication but has a security vulnerability.

**Critical Issues**:
- Line 15: Password stored in plaintext - use bcrypt or Argon2 for hashing
- Line 22: SQL query is vulnerable to injection - use parameterized queries

**Suggestions**:
- Consider adding rate limiting to prevent brute force attacks
- Add logging for failed authentication attempts

**Best Practices**:
- Function name `check_pw` is cryptic - use `verify_password` instead
- Missing docstring explaining the authentication flow

**Positive Notes**:
- Good use of early return on authentication failure
- Clear error messages for debugging
\`\`\`

### Bad Review:
\`\`\`
The code is bad. Fix the bugs.
\`\`\`
