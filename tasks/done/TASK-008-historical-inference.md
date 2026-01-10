# TASK-008: Historical Pattern Inference

**Status**: todo
**Priority**: high

## Description
Infer earnings announcement time from historical patterns using pykabutan.

## Acceptance Criteria
- [ ] Create `inference/historical.py`
- [ ] Use `pykabutan.Ticker(code).profile.past_earnings_times` or equivalent
- [ ] Detect patterns: "always 15:00", "always zaraba", "varies"
- [ ] Return inferred time with confidence level
- [ ] Add `time_inferred` column to output
- [ ] Handle missing historical data gracefully

## Notes
- Historical patterns are reliable for companies with consistent timing
- Companies announcing after 15:30 are not significant for trading decisions
- Trading hours (zaraba): 9:00-11:30, 12:30-15:30
