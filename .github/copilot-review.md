# Code Review — uritools 6.1.3

**Date:** 2026-11-02
**Reviewed:** `develop` at `905d4a6` ("Update copilot instructions and review.").
`85a3307` ("Ignore typing errors locally.") adds the file-level `# pyright:`
comment and the `# type: ignore` on `tests/test_split.py:319`. Scope:
`type: ignore` comments and `pyright` configuration; other rows carried over.

**CI status:** `tox -e py,ruff,ruff-format,pyright` passes locally on CPython 3.11
(`py` 45 passed; `pyright` 1.1.414 0 errors, 0 warnings). `8ff6d84` alone fails
`pyright` (38 errors) until `85a3307`. GitHub Actions on `tkem-ai/uritools` is green
for `develop` at `905d4a6` (run 25) on all eleven matrix jobs (CPython 3.10–3.15,
3.13t–3.15t, PyPy 3.10–3.11), each running the full `tox` envlist including `docs`
and `doctest`.

**Coverage:** 100% line and branch coverage of `src/uritools/__init__.py` (394
statements, 186 branches).

**Verified:** All ten `type: ignore` comments are needed: with
`enableTypeIgnoreComments = false`, `pyright` reports 12 errors, each on an ignored
line, and `reportUnnecessaryTypeIgnoreComment = "error"` passes. The nine in
`tests/` pass deliberately invalid types to exercise runtime `TypeError` /
`ValueError` (`reportArgumentType`) or access `Optional` `authority`
(`reportOptionalMemberAccess`); `__init__.py` line 89 stems from the unannotated
`safe`, iterated as `int | str` (`reportCallIssue`, `reportArgumentType`). The
former newline finding is fixed by `dfe83cf` (probe: `//foo%0Abar`, `ValueError`
for `scheme="http\n"`, fragment `'a\nb'`) and removed, as is the red-`pyright`
finding. Line numbers refer to `HEAD`.

## Type Stubs (`__init__.pyi`)

No issues. Generic types correctly model both `SplitResultString` and
`SplitResultBytes` via `Generic[AnyStr]`. Overload ordering is correct
for dual-input functions (`str` before `bytes`). Design intent is clear:
`getscheme()`, `getfragment()`, and all `get*()` methods intentionally
return `str` (decoding bytes when needed), and type stubs reflect this.

## Code — Potential Issues

| # | Priority | Location | Finding |
|---|----------|----------|---------|
| 1 | Info | `uriencode()` `_encoded` dict (lines 64, 81) | Cache grows without limit when callers pass arbitrary `safe` values; the FIXME acknowledges this. Decided in `copilot-instructions.md` *Boundaries*; no change. |
| 2 | Info | `gethost()` default behavior (line 245) | Returns `""` when host is empty and `default=None`, but returns `default` when default is not None. Edge case (`"file:///"` → `gethost()` returns `""`) is tested and documented; intentional. |
| 3 | Info | `_AUTHORITY_RE_*` port group | Regex `(?::([0-9]*))?` captures empty port string for URIs like `http://host:`. Handled correctly downstream (`getport()` returns default for empty port). No bug. |
| 4 | Info | `match(...).groups()` in `urisplit()` (line 559), `fullmatch(...).groups()` in `uricompose()` (lines 760, 762) | `pyright` would report that the match may be `None`. `SplitResult._RE` is not end-anchored and every group is optional; the `_AUTHORITY_RE_*` groups are optional and `(.*?)` with `re.DOTALL` absorbs any remainder, so all three always match. No guard needed; the rule is off (Code #5). |
| 5 | Info | `# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false` (line 9) | Documented in `copilot-instructions.md`. Trade-off: unlike the former `pyproject.toml` downgrades, both rules are off for the whole module, so an attribute typo such as `self._SLAHS` is no longer reported; tests catch it only on a covered path. |
| 6 | Info | All ten `# type: ignore` (line 89; `tests/test_compose.py` lines 76, 124, 126, 136, 138, 233; `tests/test_split.py` lines 295, 297, 319) | Unscoped, as documented in `copilot-instructions.md`: each silences every rule on its line. `# pyright: ignore[<rule>]` would keep other rules live if that convention changes. |

No implementation bugs found.

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
