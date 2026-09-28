## Description
Provide a concise explanation of what this pull request changes and why.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring / Performance optimization

## Pre-Merge Verification Checklist
Please verify the following before submitting:
- [ ] Backend test suite passes: `cd backend && .venv/bin/pytest tests/ -v`
- [ ] Frontend static type check passes: `cd frontend && npm run type-check`
- [ ] Frontend linter passes: `cd frontend && npm run lint`
- [ ] Frontend unit tests pass: `cd frontend && npm run test`
- [ ] Frontend production build succeeds: `cd frontend && npm run build`
- [ ] No secrets, keys, or `.env` files are included in this PR
- [ ] New or modified code is covered with relevant test cases
- [ ] Documentation has been updated (if applicable)

## Related Issues
Closes #(issue number)
