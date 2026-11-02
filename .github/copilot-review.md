# Code Review — uritools 6.1.3

**Date:** 2026-10-29
**Reviewed:** `develop` at `9739129` ("Update copilot review and instructions.";
`__version__` 6.1.3, released 2026-07-24, no unreleased code changes).

**CI status:** All `tox` environments pass locally on CPython 3.13.17: `py` (45
passed), `pyright` (0 errors; 4 `reportOptionalMemberAccess` warnings, Code #5),
`ruff`, `ruff-format`; `docs` and `doctest` pass given network access for the
intersphinx inventory (Docs #7). GitHub Actions on `tkem-ai/uritools` is green for
`master` at `755daa5` and `develop` at `9739129` on all nine matrix jobs (CPython
3.10–3.14, 3.13t, 3.14t, PyPy 3.10–3.11).

**Coverage:** 100% line coverage of `src/uritools/__init__.py` (394 statements).

**Verified:** `README.rst` examples pass `python -m doctest` (10 tests), though no
`tox` environment runs them (Docs #3). Newline handling by probe: `uricompose()`
leaks `AttributeError` for an `authority` containing a newline, accepts a scheme
with a trailing newline, and `urisplit()` truncates a fragment at a newline so
`geturi()` does not round-trip (Code #2). Every finding below re-checked against
the current tree; line numbers refer to `src/uritools/__init__.py`.

## Type Stubs (`__init__.pyi`)

No issues. Generic types correctly model both `SplitResultString` and
`SplitResultBytes` via `Generic[AnyStr]`. Overload ordering is correct
for dual-input functions (`str` before `bytes`). Design intent is clear:
`getscheme()`, `getfragment()`, and all `get*()` methods intentionally
return `str` (decoding bytes when needed), and type stubs reflect this.

## Code — Potential Issues

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Low | `uriencode()` `_encoded` dict (line 79) | Cache grows without limit when callers pass arbitrary `safe` values; the FIXME acknowledges this. Consider `@functools.lru_cache` or a size cap (*Maintainer Decisions*). |
| 2 | Low | `_SCHEME_RE`, `_AUTHORITY_RE_*` (lines 616–621), `SplitResult._RE` (lines 464, 503) | `.` without `re.DOTALL` and `$` instead of `fullmatch()`: `uricompose(authority="foo\nbar")` raises `AttributeError: 'NoneType' object has no attribute 'groups'` instead of encoding or rejecting; `uricompose(scheme="http\n")` returns `"http\n:"`; `urisplit("#a\nb").fragment` is `"a"`. Fix: `re.DOTALL` on the three regexes and `fullmatch()` for scheme and authority, so newlines are percent-encoded like any other character. |
| 3 | Info | `gethost()` default behavior (line 243) | Returns `""` when host is empty and `default=None`, but returns `default` when default is not None. Edge case (`"file:///"` → `gethost()` returns `""`) is tested and documented; intentional. |
| 4 | Info | `_AUTHORITY_RE_*` port group | Regex `(?::([0-9]*))?$` captures empty port string for URIs like `http://host:`. Handled correctly downstream (`getport()` returns default for empty port). No bug. |
| 5 | Info | `re.match(...).groups()` in `urisplit()` (line 557) and `uricompose()` (lines 758, 760) | `pyright` warns that `match()` may return `None`. `SplitResult._RE` is not end-anchored and every group is optional, so it matches any input; for `uricompose()` the `None` path is reachable only through Code #2. `reportOptionalMemberAccess` is deliberately set to `warning` in `pyproject.toml`; no guard needed. |

No implementation bugs found beyond Code #2.

## Tests — Gaps

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Low | `uricompose` with `fragment` parameter | Only tested implicitly via RFC 3986 example in `test_rfc3986`. No dedicated test for fragment encoding (e.g., `fragment="foo bar"` → `#foo%20bar`). |
| 2 | Low | `uricompose` with non-default `encoding` | No test passes non-default `encoding` to `uricompose()` (e.g., `encoding="latin-1"` with non-ASCII path). |
| 3 | Low | `uricompose` authority override with bytes | `test_authority_override` only uses `str` values. No test for bytes kwargs to authority subcomponents. |
| 4 | Low | `uriunsplit` with mixed types | Type dispatch uses `path` type to select result class. Mixed types (e.g., str scheme + bytes path) untested; consider documenting behavior. |
| 5 | Low | `DefragResult.getfragment()` default parameter | No test passes non-None `default` to `getfragment()` (e.g., `uridefrag("").getfragment(default="fallback")`). |
| 6 | Low | `getauthority()` with bytes default tuple | `test_getauthority` passes only `str` default tuples and `test_encoding_none` passes none. |

## Docs

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Low | `uriencode`/`uridecode` parameter docs | `docs/index.rst` describes input/output types but omits individual parameter docs for `encoding`, `errors`, `safe`. Users must read function signature. |
| 2 | Low | `master_doc` deprecated | Deprecated in Sphinx 4.0+ in favor of `root_doc`. Works fine with Sphinx 9.2 but will eventually warn. |
| 3 | Low | `README.rst` doctests not run by CI | `README.rst` is not included from `docs/index.rst`, so neither `tox -e doctest` nor `tox -e py` executes its examples. `--doctest-glob=README.rst README.rst` on the `pytest` command in `tox.ini` would (verified: 46 passed). |
| 4 | Info | `SplitResult` attribute table | Empty `Index` cells for properties (`userinfo`, `host`, `port`). Intentional (not tuple fields), but could clarify with "n/a". |
| 5 | Info | `DefragResult` / `SplitResult` duplication | Documented twice: inline attribute tables in "URI Decomposition" + `.. autoclass::` in "Structured Parse Results". Provides best reference coverage. |
| 6 | Info | Changelog format | Documented in `copilot-instructions.md`. No separate `CONTRIBUTING.md`, but guidance is clear. |
| 7 | Info | `tox -e docs` / `tox -e doctest` need network | `sphinx.ext.intersphinx` fetches `https://docs.python.org/3/objects.inv`; with `-W`, an unreachable inventory fails the build offline. Not a repository defect. |
