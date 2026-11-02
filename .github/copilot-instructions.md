# Copilot Instructions for uritools

**uritools** provides RFC 3986 compliant URI parsing, classification and composition,
replacing the most commonly used functions of `urllib.parse`. Pure Python ≥ 3.10, no
runtime dependencies, type stubs (`__init__.pyi`, `py.typed`). Single maintainer;
`master` is the release branch, `develop` the integration branch (Dependabot's
monthly GitHub Actions batch targets it).

## Ground Rules

- **Run everything through `tox`** (`tox -e <env> -- <posargs>`), never bare `pytest`,
  `ruff` or `pyright`. Without `tox`, use `PYTHONPATH=src python3 -m pytest tests/` so
  the workspace source is tested, not an installed package.
- **Do not edit `CHANGELOG.rst` or bump `__version__`**; both are release-only
  (`Prepare vX.Y.Z` / `Release vX.Y.Z` commits). `__version__` in
  `src/uritools/__init__.py` is the single source, read by `pyproject.toml` and
  `docs/conf.py`.
- **Single-file design**: everything lives in `src/uritools/__init__.py`; do not create
  submodules. Apply changes to **both** the `str` and `bytes` variants.
- **Public API is `__all__`**; changes are breaking. Keep `__init__.pyi` in sync with
  the runtime API.
- New behavior needs tests under `tests/`; user-visible features need docs in
  `docs/index.rst` (doctested). Keep `README.rst` examples in sync with it; they are
  valid doctests but no `tox` environment runs them, so check them with
  `PYTHONPATH=src python3 -m doctest README.rst`.
- Docs style: wrap prose paragraphs in `docs/index.rst` at column 70 (tables, code
  examples, directive signatures, titles and link targets excepted); two spaces after
  a sentence; directive body content indented 3 spaces; single backticks for
  parameters and `:func:`/`:class:`/`:attr:`/`:const:`/`:mod:` roles in
  `docs/index.rst`, ``double backticks`` in `CHANGELOG.rst`, whose entries are
  imperative one-liners ending with a period, tagged "(breaking change)" where
  applicable; docs-only work is one "Minor documentation improvements." line,
  tooling one "Update build environment." line; two blank lines between releases.
- Docstrings describe types in prose; no type annotations in `.py` files.
- Prefer clarity over cleverness; this is a hot-path parsing library, so keep
  `urisplit()`/`uriencode()` free of avoidable Python-level calls.
- This file stays at most 150 lines; when adding, drop details the code already shows.

## Architecture

**Parsing** (`urisplit()`, `uridefrag()`): type dispatch on the input selects
`SplitResultString` or `SplitResultBytes`, `namedtuple` subclasses of `SplitResult`
that differ only in their regex and delimiter constants (`_COLON`, `_SLASH`, ...).
`SplitResult._RE` is the RFC 3986 Appendix B regex; every group is optional, so it
matches any input. `userinfo`, `host` and `port` are properties derived from
`authority`, not tuple fields. `get*()` methods decode via `uridecode()` and return
`str` unless `encoding=None`; `getscheme()` lowercases and always returns `str`;
`gethost()` returns an `ipaddress` object for IP literals (IPvFuture, addresses
starting with `v`, raises `ValueError`) and a lowercased string otherwise;
`getport()` returns `int` or `default` for a missing or empty port. `transform()`
implements RFC 3986 5.2 (`urijoin()`); `__remove_dot_segments()` and `__merge()` are
name-mangled helpers. Preserve both tuple access and getter methods.

**Encoding** (`uriencode()`, `uridecode()`): byte-to-bytes lookup tables with uppercase
hex digits per RFC 3986 2.1; `_encoded` caches one table per `safe` value (unbounded,
*Maintainer Decisions*). Safe characters vary by component (`_SAFE_PATH`,
`_SAFE_QUERY`, ...). `uridecode(encoding=None)` returns `bytes`.

**Composition** (`uricompose()`): all components become `bytes`, the result is `str`.
Scheme `[A-Za-z][A-Za-z0-9+.-]*`, lowercased; `authority` is a string or a three-item
sequence, overridden per subcomponent by `userinfo`/`host`/`port` kwargs; invalid
`host`/`authority`/`query` types raise `TypeError`, never a leaked `AttributeError`.
Hosts are lowercased, IPv6 addresses bracketed and compressed (`[2001:db8::1]`). A
path with an authority must be empty or start with `/`, without one must not start
with `//`; a relative path whose first segment contains `:` gets a `./` prefix.
`query` accepts `str`, `bytes`, a mapping or an iterable of pairs, joined by
`querysep`.

## Type Stubs (`__init__.pyi`)

`SplitResult` and `DefragResult` are `Generic[AnyStr]` `NamedTuple`s. `get*()`
methods carry `@overload`s with `str` first (`encoding: str = ...`) and a
keyword-only `encoding: None` variant returning `bytes`; `getscheme()` and
`gethost()` have none, they always return `str`/`ipaddress` objects. `urijoin()`
mixed-type overloads return `str`. pyright runs in `standard` mode;
`reportOptionalMemberAccess` is a warning on purpose: the `re.match(...).groups()`
warnings are expected, do not add guards just to silence them. Only errors fail.

## Development and Tests

```bash
tox                                  # all environments
tox -e py -- tests/test_split.py -k ipv6   # posargs go to pytest
tox -e ruff,ruff-format,pyright,docs,doctest   # comma-separated environments
```

- CI (`.github/workflows/ci.yml`, every push and PR) runs `tox` on CPython 3.10–3.14,
  free-threaded 3.13t/3.14t and PyPy 3.10/3.11 and uploads coverage to Codecov. Add a
  `pyproject.toml` classifier when adding a Python version. Actions are pinned by
  commit SHA with a `# vX.Y.Z` comment; keep both in sync. Without `gh`, check runs
  via `https://api.github.com/repos/tkem-ai/uritools/actions/runs?branch=<branch>`.
- `tox -e docs` and `tox -e doctest` run Sphinx with `-W` and fetch the Python
  intersphinx inventory, so they need network access.
- Tests are `unittest.TestCase` classes with `check()` helpers, one module per
  function (`test_split.py`, `test_compose.py`, ...); not pytest-style. Every case
  has a `str` and a `bytes` variant. RFC 3986 examples live in `test_rfc3986*()`
  methods, edge cases in `test_abnormal()`. Keep 100% line coverage. Do not shadow
  built-ins (`dict`, `input`) in loop variables.

## Code Review

- Reviews **amend `.github/copilot-review.md` in place** (header: date, commit, CI
  status, coverage, one *Verified* paragraph); never new files, dated sections or a
  per-commit change summary (git history is the record).
- Findings are tables ordered High, Medium, Low, Info with columns
  `# | Priority | Location | Finding`; renumber after changes; cross-reference as
  "Code #3". **Resolved issues are removed**, never marked resolved.
- Keep it brief: one or two sentences per row, numbers only where they decide
  something, current snapshot only (no comparisons with earlier releases). Record
  settled matters under *Maintainer Decisions*. A review changes nothing; fix only
  when asked.

## Maintainer Decisions (do not re-raise)

- `getscheme()`, `getfragment()` and all other `get*()` methods decode to `str` by
  default, even for `bytes` input; the FIXMEs in the source are resolved-by-design.
- `gethost()` returns `""` for an empty host when `default=None`, but `default`
  otherwise; tested and documented.
- An empty port (`http://host:`) matches as `""`, not `None`; `getport()` still
  returns the default.
- `_encoded` may grow unbounded for arbitrary `safe` values; known, low-impact.
- `getauthority()` calls three separate getters; the TODO about a dedicated regex is
  a micro-optimization, not a bug.
- `SplitResultBytes` / `SplitResultString` stay semi-private (absent from `__all__`,
  no leading underscore); renaming would break direct importers. The
  `# TODO: make private?` comments stay.
- Feature requests are not accepted (`.github/ISSUE_TEMPLATE/feature_request.md`);
  bug reports require the latest release.
