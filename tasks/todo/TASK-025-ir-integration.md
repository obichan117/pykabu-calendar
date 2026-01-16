# TASK-025: IR Integration with Calendar

**Status**: todo
**Priority**: high
**Depends on**: TASK-022, TASK-023, TASK-024

## Description
Integrate IR discovery into main `get_calendar()` function.

## Acceptance Criteria
- [ ] Update `calendar.py` to include IR source
- [ ] New column: `ir_datetime`
- [ ] New priority order: ir > inferred > sbi > matsui > tradersweb
- [ ] Parameter: `include_ir: bool = True`
- [ ] Parameter: `ir_eager: bool = False` (bypass cache)
- [ ] Graceful fallback if IR discovery fails
- [ ] Update `_build_candidates()` with new priority
- [ ] Update tests
- [ ] Update documentation

## Notes
- IR discovery can be slow - consider async/parallel
- Don't block on IR failures
- Log IR discovery stats
