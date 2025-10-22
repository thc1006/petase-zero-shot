# PETase Zero-Shot Test Suite

## Overview

Comprehensive TDD (Test-Driven Development) test suite for the PETase zero-shot prediction system.

## Test Structure

```
tests/
├── __init__.py
├── README.md                    # This file
├── test_solubility.py          # Solubility proxy tests
├── test_priors.py              # Biochemical priors tests
├── test_ensemble.py            # Ensemble aggregation tests
├── test_pipeline.py            # Integration tests
└── fixtures/
    ├── test_sequences.fasta    # Real PETase test sequences
    └── wt_test.fasta           # WT reference (created during tests)
```

## Running Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run specific test file
```bash
python -m pytest tests/test_priors.py -v
```

### Run with coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Run specific test
```bash
python -m pytest tests/test_solubility.py::TestSolubilityProxy::test_hydrophobic_penalty -v
```

## Test Coverage

### test_solubility.py (11 tests)
- Basic functionality (dict return, all sequences scored, numeric scores)
- Hydrophobic penalty validation
- Length penalty validation
- Charge balance effects
- Edge cases (empty sequences)
- Real PETase sequence integration

### test_priors.py (12 tests)
- Dual output validation (activity & stability)
- YAML loading and structure validation
- Catalytic triad penalty enforcement
- Oxyanion hole constraints
- Favorable region rewards
- WT alignment functionality
- Real PETase fixture integration

### test_ensemble.py (11 tests)
- DataFrame conversion
- Robust (median/MAD) scaling
- Channel fusion with/without weights
- Missing channel handling
- Empty channel fallback
- Complete score fusion pipeline
- Rank averaging validation
- Edge cases (NaN, Inf, single sequence)

### test_pipeline.py (10 tests)
- End-to-end pipeline execution
- Output format validation (CSV columns, no NaN, [0,1] range)
- METHODS.md content verification
- Figure generation validation
- Sequence count/ID preservation
- Score differentiation between variants
- Single sequence handling
- Graceful channel failure recovery

## Test Fixtures

### test_sequences.fasta
Real PETase sequences used for testing:
- **IsPETase_WT**: Wild-type from Ideonella sakaiensis (~290 aa)
- **FAST_PETase**: 5-mutation variant (S121E/D186H/R224Q/N233K/R280E)
- **S121E**: Single mutation
- **D186H**: Single mutation
- **H218N**: β6-β7 loop mutation (favorable in priors)

## TDD Principles Applied

1. **Test First**: Tests written before/alongside implementation
2. **Red-Green-Refactor**: Write failing test → Make it pass → Optimize
3. **Comprehensive**: Unit tests + Integration tests
4. **Edge Cases**: Empty sequences, NaN, Inf, single variants
5. **Real Data**: Tests use actual PETase sequences from literature

## Continuous Integration

Tests should be run:
- Before committing code
- After modifying scoring channels
- Before creating pull requests
- As part of CI/CD pipeline

## Expected Test Results

**Target**: All tests pass (39/39)

Current status:
- ✅ Ensemble tests: 11/11 passed
- 🔄 Pipeline tests: Running (PLM model may take time)
- 🔄 Priors tests: Pending completion
- 🔄 Solubility tests: Pending completion

## Dependencies

```bash
pip install pytest pytest-cov
```

## Notes

- PLM tests may take 2-5 minutes (model download + inference)
- Tests create temporary directories (cleaned up automatically)
- Real sequence fixtures are version-controlled
- Test output is excluded from git (.gitignore)

## Troubleshooting

### Tests take too long
- PLM model downloads ~600MB on first run
- Use `pytest -k "not pipeline"` to skip integration tests

### ImportError
- Ensure `src/` is in Python path: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
- Or run from project root: `python -m pytest tests/`

### YAML not found
- Tests expect `data/priors/priors_petase_2024_2025.yaml`
- Ensure working directory is project root

## Future Enhancements

- [ ] Add performance benchmarks
- [ ] Mock PLM for faster unit tests
- [ ] Add FoldX integration tests (when implemented)
- [ ] Mutation effect regression tests
- [ ] Cross-validation with ProteinGym

---

**Maintained as part of PETase Zero-Shot prediction system**
**Following TDD best practices for scientific software**
