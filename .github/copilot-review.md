# Code Review — uritools 6.1.3

**Date:** 2026-11-02

**Reviewed:** `develop` at `6395596` ("Extend and improve various unit
tests."), five commits ahead of the last-reviewed `c0aee0d` ("Update
copilot-review.md.", which reviewed v6.1.1). Scope: `dac3428` and
`2d021ec` (CI/tooling only — Python 3.15 added to the CI matrix and
`pyproject.toml` classifiers, `pyright` config tightened to
`reportUnnecessaryTypeIgnoreComment = "error"`, `pytest-cov` gains
`--cov-branch`), `3393638` ("Fix newline handling in uricompose() and
urisplit()"), `e17be96` ("Improve type correctness."), `6395596`
("Extend and improve various unit tests."). `docs/` and `README.rst`
are unchanged since `c0aee0d`, so their rows are carried over. Local
`develop` is 6 ahead and 10 behind `origin/develop` (`6d5c6bd`), which
carries a parallel line of the same work; its `src/` differs from this
tree only in the final `uricompose()` return being split across lines
831–832 here. This review covers the local branch only.

**CI status:** `tox` (`py`, `docs`, `doctest`, `pyright`, `ruff`,
`ruff-format`) passes locally on CPython 3.14.4 (`py` 49 passed under
pytest 9.1.1; `pyright` 1.1.411 0 errors, 0 warnings — a newer 1.1.414
is available but not installed; Sphinx 9.1.0 `-W` clean; `doctest` 10
passed). `PYTHONPATH=src python3 -m doctest README.rst` passes. GitHub
Actions not re-checked for this review.

**Coverage:** 100% line and branch coverage of
`src/uritools/__init__.py` (392 statements, 186 branches;
`--cov-branch` was added by `2d021ec`).

**Verified:** `3393638` fixes a real bug, not just a style issue:
unanchored `$` in `_SCHEME_RE` and `_AUTHORITY_RE_*` let a trailing
newline silently pass validation (Python's `$`, without `re.MULTILINE`,
matches just before a trailing `\n`), and the `SplitResult` regexes'
fragment group (`(.*)`) excluded embedded newlines without
`re.DOTALL`, silently truncating fragments that contained one. Both
are fixed by switching `_scheme()` and the `uricompose()` authority
parsing to `.fullmatch()` with the anchors removed, and adding
`re.DOTALL` to all four regexes (`SplitResultBytes`/
`SplitResultString._RE`, `_AUTHORITY_RE_BYTES`/`_AUTHORITY_RE_STR`).
`test_compose.py` (`test_scheme`, `test_authority`) and
`test_split.py` (`test_abnormal`) round-trip embedded-newline cases;
the `bytes` side of `urisplit()` is covered only by a manual check
(see *Tests — Gaps*). `e17be96` reacts to the stricter `pyright`
config from `2d021ec`: it declares the per-subclass constants
(`_RE: re.Pattern`, `_COLON: str | bytes`, ...) on `SplitResult`,
hoists the `_match()` classmethod from both subclasses into the base,
and adds the two `uricompose()` authority `# type: ignore` comments
that the config now requires to be exactly where `pyright` flags
them — the previously-overridden `reportAttributeAccessIssue`/
`reportOptionalMemberAccess` settings had been masking these sites.
Removing the three source ignores on a scratch copy reproduces
exactly three errors (`reportOptionalMemberAccess` at lines 769 and
771, `reportAttributeAccessIssue` at line 832) and nothing else, so
each ignore is load-bearing and none is redundant. `6395596` closes
all six test gaps from the previous review: `fragment` encoding
(`test_fragment`), non-default `encoding` (`test_encoding`), `bytes`
authority overrides (`test_authority_override`), mixed-type
`uriunsplit()` (`test_mixed_types`), `DefragResult.getfragment()` with
`default` (`test_getfragment_default`), and `bytes` default tuples for
`getauthority()` (`test_getauthority`); all six rows are removed. The
error-type probe in Code row 1 and the `bytes` newline round-trips in
Tests rows 1–2 were run against `src/` by hand. Line numbers below
refer to `HEAD` (`6395596`).

## Type Stubs (`__init__.pyi`)

No issues. Generic types correctly model both `SplitResultString` and
`SplitResultBytes` via `Generic[AnyStr]`. Overload ordering is correct
for dual-input functions (`str` before `bytes`; `encoding: None`
overloads are keyword-only where a `default` parameter precedes them,
positional in `uridecode()` and `getpath()`). Design intent is clear:
`getscheme()`, `getfragment()`, and all `get*()` methods intentionally
return `str` (decoding bytes when needed), and type stubs reflect
this. Note that `pyright` does not consult the stubs while checking
`__init__.py` itself; inside the module every call resolves to the
unannotated `.py` definition, which is why the three source ignores
exist (Code rows 4–5).

## Code — Potential Issues

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Low | `uricompose()` component type checks (lines 760–763, 776–781, 787, 813–820, 827–828) | Only `authority` (line 772), `host` (line 664) and `query` (line 819) validate their type and raise `TypeError`. Every other component of the wrong type leaks `AttributeError: 'int' object has no attribute 'encode'` from `uriencode()` or `_scheme()`: `scheme=42`, `userinfo=42`, `path=42`, `path=None`, `fragment=42`, `port=[1]`, `query={1: 2}`, `query=[(1, 2)]` and `authority=[42, None, None]` all do (`port=True` is a `numbers.Number` and raises `ValueError`). The stubs type all of these, so a checker catches misuse; `copilot-instructions.md` *Architecture constraints* now states the narrower guarantee. No change unless the maintainer wants uniform `TypeError`s. |
| 2 | Info | `uriencode()` `_encoded` dict (lines 62, 79) | Cache grows without limit when callers pass arbitrary `safe` values; the FIXME at line 79 acknowledges this. Decided in `copilot-instructions.md` *Boundaries*; no change. |
| 3 | Info | `gethost()` default behavior (line 258) | Returns `""` when host is empty and `default=None`, but returns `default` when default is not `None`. Edge case (`"file:///"` → `gethost()` returns `""`) is tested and documented; intentional. |
| 4 | Info | `_AUTHORITY_RE_*` port group (lines 631–632) | Regex `(?::([0-9]*))?` captures an empty port string for URIs like `http://host:`. Handled correctly downstream (`getport()` returns `default` for an empty port). No bug. |
| 5 | Info | `fullmatch(...).groups()` in `uricompose()` (lines 769, 771) | `pyright` reports `"groups" is not a known attribute of "None"` (`reportOptionalMemberAccess`) at both sites, each silenced by `# type: ignore`. `urisplit()`'s `result._match(uristring).groups()` (line 568) needs none: `_match()` is an unannotated classmethod reached through a `type[SplitResultBytes] \| type[SplitResultString]` union, so `pyright` infers the call as `Unknown` and reports nothing. All three regexes always match: `SplitResult._RE` is not end-anchored and every group is optional, and the `_AUTHORITY_RE_*` groups are optional with `(.*?)`/`re.DOTALL` absorbing any remainder. No guard needed. |
| 6 | Info | `uricompose()` final `.decode()` (line 832) | `pyright` reports `Cannot access attribute "decode" for class "str"` (`reportAttributeAccessIssue`), hence the `# type: ignore`. Inside the module `uriunsplit()` is the unannotated `.py` function, whose return is inferred from `SplitResult.geturi()` → `self._EMPTY.join(result)` with `_EMPTY: str \| bytes` (line 155), so the call is typed `bytes \| str` regardless of the `bytes`-only `parts` tuple. Narrowing it would need a return annotation or `typing` import in the `.py`; accepted to keep both out. |
| 7 | Info | All twelve `# type: ignore` in the repo (3 in `src/uritools/__init__.py`: lines 769, 771, 832; 9 in `tests/`: `test_compose.py` lines 76, 124, 126, 136, 138, 252, `test_split.py` lines 317, 319, 341) | Unscoped, as documented in `copilot-instructions.md`: each silences every rule on its line. `# pyright: ignore[<rule>]` would keep other rules live if that convention changes. |

No implementation bugs found.

## Tests — Gaps

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Low | `test_split.py` `test_abnormal` (lines 51–52 vs. 61–81) | The two embedded-newline inputs (`"#foo\nbar"`, `"?foo\nbar#baz\n"`) exist only as `str`. No `bytes` case exercises the `re.DOTALL` added to `SplitResultBytes._RE` (line 491) by `3393638`, and branch coverage cannot show it because a regex flag is not a branch. Checked by hand: `urisplit(b"#foo\nbar")` and `urisplit(b"?foo\nbar#baz\n")` round-trip; adding the two `bytes` tuples would pin that. |
| 2 | Low | `test_compose.py` `test_authority` (line 69) | `("//example.com%3A42%0A", "example.com:42\n")` — the trailing-newline authority that `3393638` fixed — has no `bytes` twin, unlike the neighbouring newline cases (lines 65–68). Checked by hand: `uricompose(authority=b"example.com:42\n")` gives the same result. |

## Docs

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Low | `uricompose` prose (`docs/index.rst` lines 103–104) | "All components ... will be encoded according to `encoding`" does not hold for `host`: a `str` host is always encoded as UTF-8 (`_authority()`), which `test_encoding` now pins. One sentence in the prose would match the behavior. |
| 2 | Low | `uriunsplit` (`docs/index.rst` line 123) | Bare `autofunction` with no prose. The result type follows `path`, and mixed `str`/`bytes` parts raise `TypeError` (now tested in `test_mixed_types`); neither is documented. |
| 3 | Low | `uriencode`/`uridecode` parameter docs | `docs/index.rst` describes input/output types but omits individual parameter docs for `encoding`, `errors`, `safe`. Users must read the function signature. |
| 4 | Low | `master_doc` deprecated (`docs/conf.py` line 16) | Deprecated in Sphinx 4.0+ in favor of `root_doc`. Sphinx 9.1.0 builds with `-W` and no warning, but it may eventually warn. |
| 5 | Low | `README.rst` doctests not run by CI | `README.rst` is not included from `docs/index.rst`, so neither `tox -e doctest` nor `tox -e py` executes its examples. `--doctest-glob=README.rst README.rst` on the `pytest` command in `tox.ini` would. `python3 -m doctest README.rst` passes. |
| 6 | Info | `SplitResult` attribute table (`docs/index.rst`) | Empty `Index` cells for properties (`userinfo`, `host`, `port`). Intentional (not tuple fields), but could clarify with "n/a". |
| 7 | Info | `DefragResult` / `SplitResult` duplication | Documented twice: inline attribute tables in "URI Decomposition" + `.. autoclass::` with `:members:` in "Structured Parse Results". Provides the best reference coverage. |
| 8 | Info | Changelog format | Documented in `copilot-instructions.md`. No separate `CONTRIBUTING.md`, but guidance is clear. |
| 9 | Info | `tox -e docs` / `tox -e doctest` need network | `sphinx.ext.intersphinx` fetches `https://docs.python.org/3/objects.inv`; with `-W`, an unreachable inventory fails the build offline. Not a repository defect. |
