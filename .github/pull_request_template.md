## Summary

Describe the problem and the change. Link related issues with `Fixes #...` where
applicable.

## Testing

- [ ] `.venv/bin/python -m pytest` passes
- [ ] `python -m compileall -q app.py core ui tests` passes
- [ ] `bash -n install.sh run.sh build_app.sh` passes
- [ ] `./build_app.sh` and launch checked, if packaging changed

## Checklist

- [ ] Behavior and UI changes are covered by tests where practical
- [ ] README, USER_GUIDE, CHANGELOG, or knowledge.md updated when needed
- [ ] `USER_GUIDE.md` and `GUIDE_MARKDOWN` remain in sync
- [ ] No personal resume data, exports, `.venv`, `build/`, or `dist/` committed
- [ ] No new dependency without a clear need and an upper bound in requirements
