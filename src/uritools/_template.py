"""RFC 6570 URI Templates, imported on demand by
:func:`uritools.uritemplate`.

"""

import collections.abc
import numbers
import re

from . import RESERVED, uriencode

# RFC 6570 2.2: expression = "{" [ operator ] variable-list "}"
_EXPRESSION_RE = re.compile(r"\{([^{}]*)\}")

# RFC 6570 2.3: varspec = varname [ modifier-level4 ]
_VARSPEC_RE = re.compile(
    r"((?:[A-Za-z0-9_]|%[0-9A-Fa-f]{2})+(?:\.(?:[A-Za-z0-9_]|%[0-9A-Fa-f]{2})+)*)"
    r"(?::([1-9][0-9]{0,3})|(\*))?"
)

_PCT_ENCODED_RE = re.compile(b"%[0-9A-Fa-f]{2}")

# RFC 6570 Appendix A: operator -> (first, sep, named, ifemp, allow reserved)
_OPERATORS = {
    "": (b"", b",", False, b"", False),
    "+": (b"", b",", False, b"", True),
    "#": (b"#", b",", False, b"", True),
    ".": (b".", b".", False, b"", False),
    "/": (b"/", b"/", False, b"", False),
    ";": (b";", b";", True, b"", False),
    "?": (b"?", b"&", True, b"=", False),
    "&": (b"&", b"&", True, b"=", False),
}

# RFC 6570 2.2: op-reserve = "=" / "," / "!" / "@" / "|"
_OP_RESERVE = "=,!@|"


def _encode(value, reserved):
    # RFC 6570 3.2.1: percent-encode everything but unreserved characters,
    # or everything but unreserved and reserved characters and existing
    # percent-encoded triplets for the "+" and "#" operators
    if not reserved:
        return uriencode(value)
    result = []
    pos = 0
    for match in _PCT_ENCODED_RE.finditer(value):
        result.append(uriencode(value[pos : match.start()], RESERVED))
        result.append(match.group())
        pos = match.end()
    result.append(uriencode(value[pos:], RESERVED))
    return b"".join(result)


def _string(value, maxlen):
    # RFC 6570 2.4.1: the prefix modifier applies to characters, not octets
    if isinstance(value, bytes):
        return value[:maxlen]
    elif isinstance(value, str):
        return value[:maxlen].encode("utf-8")
    elif isinstance(value, numbers.Number):
        return str(value)[:maxlen].encode()
    else:
        raise TypeError("Invalid template variable type: %r" % type(value))


def _variable(name, value, maxlen, explode, named, ifemp, reserved):
    # RFC 6570 3.2.1: return the list of expansions, or None if undefined
    if value is None:
        return None
    if isinstance(value, (str, bytes, numbers.Number)):
        encoded = _encode(_string(value, maxlen), reserved)
        if named:
            return [name + (b"=" + encoded if encoded else ifemp)]
        else:
            return [encoded]
    if maxlen is not None:
        raise ValueError("Prefix modifier not applicable to composite value")
    if isinstance(value, collections.abc.Mapping):
        items = [
            (_encode(_string(k, None), reserved), v)
            for k, v in value.items()
            if v is not None
        ]
        if not items:
            return None
        pairs = [(k, _encode(_string(v, None), reserved)) for k, v in items]
        if explode:
            return [k + (b"=" + v if v or not named else ifemp) for k, v in pairs]
        joined = b",".join(k + b"," + v for k, v in pairs)
    elif isinstance(value, collections.abc.Iterable):
        items = [_encode(_string(v, None), reserved) for v in value if v is not None]
        if not items:
            return None
        if explode:
            if named:
                return [name + (b"=" + v if v else ifemp) for v in items]
            else:
                return items
        joined = b",".join(items)
    else:
        raise TypeError("Invalid template variable type: %r" % type(value))
    if named:
        return [name + (b"=" + joined if joined else ifemp)]
    else:
        return [joined]


def _varspec(varspec):
    match = _VARSPEC_RE.fullmatch(varspec)
    if not match:
        raise ValueError("Invalid template variable specification: %r" % varspec)
    name, maxlen, explode = match.groups()
    return name, name.encode("ascii"), int(maxlen) if maxlen else None, bool(explode)


def _expression(expression):
    # RFC 6570 2.2: parse "[ operator ] variable-list" into an operator
    # tuple and a list of varspecs
    operator = expression[:1]
    if operator in _OP_RESERVE and operator:
        raise ValueError("Reserved template operator: %r" % operator)
    elif operator in _OPERATORS and operator:
        varlist = expression[1:]
    else:
        operator, varlist = "", expression
    return _OPERATORS[operator], [_varspec(v) for v in varlist.split(",")]


def _literal(literal):
    # RFC 6570 3.1: copy literals, percent-encoding disallowed characters
    if "{" in literal or "}" in literal:
        raise ValueError("Unbalanced braces in template: %r" % literal)
    return _encode(literal.encode("utf-8"), True)


def _expand(expression, variables):
    (first, sep, named, ifemp, reserved), varspecs = expression
    expansions = []
    for name, encoded_name, maxlen, explode in varspecs:
        expansion = _variable(
            encoded_name, variables.get(name), maxlen, explode, named, ifemp, reserved
        )
        if expansion is not None:
            expansions.extend(expansion)
    return first + sep.join(expansions) if expansions else b""


class URITemplate:
    """An RFC 6570 URI Template, parsed by :func:`uritools.uritemplate`."""

    __slots__ = ("_parts", "template")

    def __init__(self, template):
        if isinstance(template, bytes):
            template = template.decode("utf-8")
        elif not isinstance(template, str):
            raise TypeError("Invalid template type: %r" % type(template))
        self.template = template
        self._parts = parts = []
        pos = 0
        for match in _EXPRESSION_RE.finditer(template):
            parts.append(_literal(template[pos : match.start()]))
            parts.append(_expression(match.group(1)))
            pos = match.end()
        parts.append(_literal(template[pos:]))

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.template)

    def __str__(self):
        return self.template

    def expand(self, variables=None, /, **kwargs):
        """Expand the template with the given variables and return the
        resulting URI reference as a string.

        """
        variables = dict(variables or {}, **kwargs)
        result = []
        for part in self._parts:
            if isinstance(part, bytes):
                result.append(part)
            else:
                result.append(_expand(part, variables))
        return b"".join(result).decode("ascii")
