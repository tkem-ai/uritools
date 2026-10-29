# Copilot Instructions for uritools

## Project

- RFC 3986 URI parsing, classification and composition; replaces `urllib.parse`
- Pure Python ≥ 3.10, no runtime dependencies, `setuptools` build
- One module: `src/uritools/__init__.py`; stubs in `__init__.pyi` (+ `py.typed`)
- Tests: `unittest` under `tests/`, run by `pytest`; docs: Sphinx in `docs/`
- Lint/format: `ruff`; type check: `pyright` (`standard` mode)
- Single maintainer; `master` = releases, `develop` = integration (Dependabot target)

## Commands

```bash
tox                                              # everything (CI runs this)
tox -e py -- tests/test_split.py -k ipv6         # tests; posargs go to pytest
tox -e ruff,ruff-format,pyright                  # lint, format check, types
tox -e docs,doctest                              # Sphinx -W; needs network
PYTHONPATH=src python3 -m pytest tests/          # without tox (tests src, not site-packages)
PYTHONPATH=src python3 -m doctest README.rst     # README examples (not run by tox)
```

Pass criteria: all tests green, 100% line coverage, `ruff` clean, `pyright` 0 errors.
`pyright` warnings on `re.match(...).groups()` are expected; do not add guards for them.

## Code style

Every public function takes `str` or `bytes`; dispatch on the input, change both paths:

```python
if isinstance(uristring, bytes):
    result = SplitResultBytes
else:
    result = SplitResultString
return result(*result._match(uristring).groups())
```

Docstrings describe types in prose; no annotations in `.py` files, types go in
`__init__.pyi` with `str` overloads before the keyword-only `encoding: None` ones:

```python
def getport(self, default=None):
    """Return the port subcomponent of the URI authority as an
    :class:`int`, or `default` if the original URI reference did
    not contain a port or if the port was empty.

    """
```

Tests: `unittest.TestCase` with a `check()` helper, a `str` and a `bytes` case per
input, RFC 3986 examples in `test_rfc3986*()`, edge cases in `test_abnormal()`:

```python
cases = [
    ("//example.com:42", "example.com:42"),
    ("//example.com:42", b"example.com:42"),
]
for uri, authority in cases:
    self.check(uri, authority=authority)
```

Docs (`docs/index.rst`): prose wrapped at column 70, two spaces after a sentence,
directive bodies indented 3 spaces, single backticks for parameters, Sphinx roles
for objects:

```rst
.. autofunction:: uricompose

   All components may be specified as either Unicode strings, which
   will be encoded according to `encoding`, or :class:`bytes` objects.
```

Changelog (`CHANGELOG.rst`, release-only): imperative one-liner with a period,
``double backticks``, "(breaking change)" tag, two blank lines between releases:

```rst
- Require Python 3.9 or later (breaking change).
```

## Architecture constraints

- Results are `namedtuple` subclasses: keep tuple access and `get*()` methods working
- `get*()` methods return `str` (or `ipaddress` objects) unless `encoding=None`
- `uricompose()` returns `str`; invalid component types raise `TypeError` or
  `ValueError`, never a leaked `AttributeError`
- Percent-encoding uses uppercase hex; safe sets per component (`_SAFE_PATH`, ...)
- IP literals: `ipaddress` module, output bracketed and compressed; reject IPvFuture
- Hot path: no avoidable Python-level calls in `urisplit()` / `uriencode()`

## Boundaries

- Do not edit `CHANGELOG.rst` or bump `__version__`; both happen in release commits
- Do not add submodules, runtime dependencies, or entries to `__all__`
- Do not rename `SplitResultBytes` / `SplitResultString`; semi-private, stays so
- Do not "fix" these (tested, documented, decided):
  `getscheme()`/`getfragment()` decode `bytes` input to `str`; `gethost()` returns
  `""` for an empty host with `default=None`; an empty port matches as `""` and
  `getport()` returns the default; `_encoded` grows per `safe` value;
  `getauthority()` calls three getters; the FIXME/TODO comments stay
- Feature requests are not accepted; bug reports require the latest release
- This file stays under 150 lines; update it in the same PR as a convention change

## Git workflow

- Branch from `develop`, PR to `develop`; `master` receives releases only
- CI: GitHub Actions on push and PR, CPython 3.10–3.14 (+ `3.13t`, `3.14t`), PyPy
  3.10/3.11; actions pinned by SHA with a `# vX.Y.Z` comment, bump both together
- Adding a Python version: CI matrix and `pyproject.toml` classifiers
- Code reviews amend `.github/copilot-review.md` in place: header (date, commit, CI,
  coverage, one *Verified* paragraph), tables `# | Priority | Location | Finding`
  ordered High → Info, renumbered; resolved rows are removed; a review changes no code
