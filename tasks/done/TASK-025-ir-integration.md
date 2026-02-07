# TASK-025: IR Integration with Calendar

**Status**: done
**Priority**: high
**Depends on**: TASK-022, TASK-023, TASK-024

## Description
Integrate IR discovery into main `get_calendar()` function.

## Acceptance Criteria
- [x] Update `calendar.py` to include IR source
- [x] New column: `ir_datetime`
- [x] New priority order: ir > inferred > sbi > matsui > tradersweb
- [x] Parameter: `include_ir: bool = True`
- [x] Parameter: `ir_eager: bool = False` (bypass cache)
- [x] Graceful fallback if IR discovery fails
- [x] Update `_build_candidates()` with new priority
- [x] Update tests
- [ ] Update documentation

## Notes
- IR discovery can be slow - consider async/parallel
- Don't block on IR failures
- Log IR discovery stats
