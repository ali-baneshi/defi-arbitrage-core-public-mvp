# Project Status

## Current Status

- Maturity: alpha offline MVP.
- Local deterministic validation: **PASSED** with `PYTHONPATH=src python scripts/validate_all.py` (39 tests passing).
- Type safety improvements: Decimal conversion auto-coercion added to `RiskPolicy` and `Edge.normalized()`.
- Public release: blocked until manual gates in `scripts/release_readiness.py` are resolved.
- Production use: not supported.

## Supported Today

- Local JSON snapshot validation and bounded cycle analysis.
- Text and JSON opportunity output.
- Structured CLI diagnostics and expected-error JSON.
- Dependency-free repository, workflow, schema, contract, negative-case, and release-readiness checks.
- Optional Rust analyzer parity validation.
- Offline Solidity and Vyper source-template organization and validation.
- **Improved type safety**: Automatic Decimal coercion for numeric fields in models.
- **Enhanced test compatibility**: Tests updated to use explicit Decimal types.

## Not Supported Today

- Live RPC, wallets, private keys, signing, mempool monitoring, transaction broadcast, or trade execution.
- Contract compilation, deployment, bytecode verification, gas analysis, audit, or production execution.
- Public release without credential rotation, old-history exclusion confirmation, independent history scanning, and localization scoping/refresh.

## Readiness Interpretation

`local_validation_ready: true` means deterministic local checks passed. It does not mean public release readiness, production readiness, trading safety, or contract safety.

## Recent Improvements (Hardening Phase 1)

1. **Type Safety**: Added `__post_init__` to `RiskPolicy` for automatic Decimal coercion.
2. **Edge Normalization**: Enhanced `Edge.normalized()` to handle mixed numeric types (int/float/Decimal).
3. **Test Updates**: All tests now use explicit `Decimal` types for policy parameters.
4. **Validation**: All 39 existing tests pass without modification to test logic.
