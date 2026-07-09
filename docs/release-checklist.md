# Release Checklist

Follow these steps before publishing a new release:

- [ ] clean git status
- [ ] version selected
- [ ] changelog updated
- [ ] README checked
- [ ] docs links checked
- [ ] tests pass
- [ ] demo runs
- [ ] CI green
- [ ] package build succeeds
- [ ] no secrets
- [ ] no fake adoption claims
- [ ] GitHub release notes drafted
- [ ] tag created only with explicit approval

## Package Build Verification

Verify that the wheel and source distribution build correctly without uploading them:

```bash
python -m pip install --upgrade build
python -m build
```
