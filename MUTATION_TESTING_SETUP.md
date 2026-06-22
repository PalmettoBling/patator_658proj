# Mutation Testing Setup

## Overview

This project now has two new branches configured for mutation testing:
- **Agent-A-Mutate-Tests** - Mutation testing for Agent-A-Copilot test suite
- **Agent-B-Mutate-Tests** - Mutation testing for Agent-B-Claude test suite

## Branch Configuration

### Agent-A-Mutate-Tests
- **Base Branch**: Agent-A-Copilot
- **Test Suite**: `tests/test_patator.py`
- **Target Code**: `src/patator/patator.py`
- **Mutation Configuration**: `mutation_test_simple.py`

### Agent-B-Mutate-Tests
- **Base Branch**: Agent-B-Claude
- **Test Suite**: `tests/test_patator.py`
- **Target Code**: `src/patator/patator.py`
- **Mutation Configuration**: `mutation_test_simple.py`

## Mutation Configuration

Both branches use the **identical mutation testing configuration** with 13 mutations:

1. **M01** - Change bytes encoding from ISO-8859-1 to UTF-8
2. **M02** - Change bytes decoding from ISO-8859-1 to UTF-8
3. **M03** - Disable escaping behavior in repr23
4. **M04** - Replace md5 helper with sha1
5. **M05** - Replace sha1 helper with md5
6. **M06** - Break time formatting divisor constants
7. **M07** - Disable random mode branch in RangeIter
8. **M08** - Return maxint instead of computed RangeIter length
9. **M09** - Stop stripping CRLF in ppstr
10. **M10** - Break query splitting behavior
11. **M11** - Relax FILE key matcher
12. **M12** - Relax NET key matcher
13. **M13** - Break COMBO key second capture matcher

## Running Mutation Tests

To run mutation tests on either branch:

```bash
cd d:\patator_658proj
python mutation_test_simple.py
```

This will:
1. Apply each mutation to `src/patator/patator.py`
2. Run `tests/test_patator.py` against the mutated code
3. Generate a mutation report showing which mutations were killed (test failures) vs survived (test passed)

## Expected Outcomes

- **KILLED Mutations**: Indicate that the test suite caught the defect (good test coverage)
- **SURVIVED Mutations**: Indicate that the test suite missed the defect (gap in coverage)

## File Hashes

Both branches have identical `mutation_test_simple.py`:
- **Hash**: `E2D7CCE617F4CA4343CC0D2D9BFBDA5039E346BE0D42DF6BA58FB07F8B3CE875`

This ensures consistent mutation testing across both branches.

## Key Files

- `mutation_test_simple.py` - The mutation testing harness script
- `tests/test_patator.py` - The test suite for both branches (from their respective base branches)
- `src/patator/patator.py` - The target code being mutated

## Branch Relationships

```
master
├── Agent-A-Copilot (test suite A)
│   └── Agent-A-Mutate-Tests (with mutation testing)
└── Agent-B-Claude (test suite B)
    └── Agent-B-Mutate-Tests (with mutation testing)
```

## Notes

- Each branch maintains the test suite from its base branch
- Mutation testing configuration is identical between branches for fair comparison
- The test suites may differ between branches, allowing for comparative analysis of mutation detection
