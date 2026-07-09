# Release Checklist

Follow this final pre-release sequence before publishing a new Pictovap release.

## Final Pre-Release Sequence

- [ ] 1. clean git status
- [ ] 2. tests pass
- [ ] 3. demo runs
- [ ] 4. docs links pass
- [ ] 5. package builds
- [ ] 6. README checked
- [ ] 7. changelog updated
- [ ] 8. release notes prepared
- [ ] 9. no secrets
- [ ] 10. no fake adoption claims
- [ ] 11. CI green
- [ ] 12. tag created only after explicit approval
- [ ] 13. GitHub release published manually

## Package Build Verification

Verify that the wheel and source distribution build correctly without uploading them:

```bash
python -m pip install --upgrade build
python -m build
```
