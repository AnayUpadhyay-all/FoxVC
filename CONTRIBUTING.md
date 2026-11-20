# Contributing to FoxVC

Welcome, and thank you for considering a contribution to FoxVC! FoxVC is a compact, zero-external-dependency scripting language with a native C bytecode VM. Contributions should preserve its small footprint, deterministic behavior, and stable 25-keyword language.

## Development setup

Requirements:

- Python 3.10 or newer.
- GCC or Clang with a C99-compatible toolchain.
- Git.

Clone the repository:

```bash
git clone https://github.com/AnayUpadhyay-all/FoxVC.git
cd FoxVC
```

FoxVC has no third-party Python runtime dependencies for its core test/build path. Compile the native VM shared library from the repository root:

```bash
gcc -Wall -Wextra -Werror -O3 -shared -fPIC engine/foxvm.c -o engine/foxvm.so -lm
```

The VM links against the standard C library and math library only. On systems using Clang, replace `gcc` with `clang`.

## Build and test

Run a source file and build a standalone native executable:

```bash
python3 foxvc run examples/hello.fox
python3 foxvc build examples/math.fox -o math_app
./math_app
```

Run the Python unit/differential tests, FoxVC source test suites, and example linter:

```bash
python3 -m unittest discover tests
python3 foxvc test
python3 foxvc lint examples/
```

The `foxvc test` command discovers FoxVC test files with the official `.fox` extension. The requested `tests/tco_and_core_stress.fvc` fixture is intentionally exercised by the CI harness through `engine.runner.run_foxvc`: its tail-recursive section runs on the native C VM, while its `trap ... otherwise` section runs on the authoritative interpreter. The native C VM does not currently implement the `SETUP_TRAP` opcode, so combining both sections into one native-VM execution would test an unsupported feature rather than TCO.

## Language syntax and compatibility

Use the v2.0.0 syntax in `FOXVC_SPEC.md` and `GRAMMAR.md`:

- Single-line comments start with `#`.
- Declare functions with `act name(parameters)`; return with `emit value`.
- Branch with `pick condition`, optional `alt condition`, and optional `otherwise`.
- Use `trap` followed by an `otherwise` recovery block for recoverable runtime errors.
- Use `guard condition` for an assertion and `say expression` for output.

`recover` is not a v2.0.0 keyword. Do not introduce it as an alias: the recovery clause is `otherwise`.

## Architecture and contribution priorities

Please keep these project constraints in mind:

- Keep C code warning-free under `-Wall -Wextra -Werror`.
- Preserve the zero-external-dependency core; do not add third-party runtime libraries without an agreed design discussion.
- Keep the native VM small, portable, and suitable for constrained devices.
- Preserve the exact 25-keyword language grammar. New language keywords require a separate design/RFC discussion.
- Keep native C VM and interpreter behavior aligned where the native VM claims feature support; document unsupported opcodes rather than silently falling back.

High-impact areas for contributions:

- VM edge-case, bytecode, memory-safety, and TCO regression tests.
- Reproducible Lua/Python benchmark comparisons with methodology and machine details.
- Clear, source-located lexer, parser, compiler, and runtime diagnostics.
- Small standard-library shelf helpers that do not duplicate existing APIs.
- Cross-platform build and CI reliability.

## Pull request checklist

Before opening a PR:

- [ ] Keep the change focused and explain the user-visible or engineering benefit.
- [ ] Add regression tests for changed behavior and edge cases.
- [ ] Run `python3 -m unittest discover tests`.
- [ ] Run `python3 foxvc test` and `python3 foxvc lint examples/` when relevant.
- [ ] Compile the C VM with `-Wall -Wextra -Werror`.
- [ ] Update the relevant specification, changelog, or documentation.
- [ ] Confirm no new language keyword or external dependency was added unintentionally.
- [ ] Include actual test results and any known limitations in the PR description.

Thank you for helping keep FoxVC lean, reliable, and welcoming to contributors.
