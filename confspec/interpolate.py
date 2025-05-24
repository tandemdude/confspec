# -*- coding: utf-8 -*-
# Copyright (c) 2025-present tandemdude
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

__all__ = ["InterpolationVisitor", "try_interpolate"]

import os
import re
import typing as t

_escaped = r"(?P<escaped>\$)"
_name = r"(?P<name>[a-zA-Z_]\w*)"
_delim = r"(?P<delim>[^]}]+)"
_strip = r"(?P<strip>~)"
_default = r"(?P<default>:[^}]*|\?)"

INTERPOLATION_PATTERN: t.Final[re.Pattern[str]] = re.compile(
    rf"{_escaped}?(?P<raw>\${{{_name}(?:\[{_delim}])?{_strip}?{_default}?}})"
)


def _replace_fn(match: re.Match[str]) -> str:
    if match.group("escaped"):
        return str(match.group("raw"))

    if match.group("delim") is not None:
        raise SyntaxError("list expansion is not supported within strings")

    var, is_set = os.getenv(name := match.group("name")), name in os.environ
    if not is_set:
        if (default := match.group("default")) is None:
            raise KeyError(f"environment variable '{name}' is not set and no default was specified")

        if default == "?":
            raise SyntaxError("None-as-default ('?') flag is not supported within strings")

        resolved = str(default)[1:]  # strip the leading colon
    else:
        resolved = str(var)

    return resolved.strip() if match.group("strip") is not None else resolved


def try_interpolate(value: str) -> t.Any:
    match = INTERPOLATION_PATTERN.fullmatch(value)
    matched_and_not_escaped = match is not None and match.group("escaped") is None

    if matched_and_not_escaped:
        assert match is not None
        # If the "?" (None as default) flag is present, and the variable is unset
        # then return None
        if match.group("default") == "?" and os.getenv(match.group("name")) is None:
            return None

        # if a delimiter was specified, split into list - otherwise use the standard substitution function
        if (delim := match.group("delim")) is not None:
            strip = match.group("strip") is not None
            val = os.getenv(match.group("name"), (match.group("default") or "")[1:])
            return [(elem.strip() if strip else elem) for elem in val.split(delim)]

    return INTERPOLATION_PATTERN.sub(_replace_fn, value)


class InterpolationVisitor:
    __slots__ = ()

    def visit_value(self, val: t.Any) -> t.Any:
        if not isinstance(val, str):
            return val
        return try_interpolate(val)

    def visit_list(self, lst: list[t.Any]) -> list[t.Any]:
        for i in range(len(lst)):
            lst[i] = self.visit(lst[i])
        return lst

    def visit_dict(self, dct: dict[str, t.Any]) -> dict[str, t.Any]:
        for k, v in list(dct.items()):
            dct[k] = self.visit(v)
        return dct

    def visit(self, item: t.Any) -> t.Any:
        if isinstance(item, dict):
            return self.visit_dict(t.cast("dict[str, t.Any]", item))
        elif isinstance(item, list):
            return self.visit_list(t.cast("list[t.Any]", item))
        return self.visit_value(item)
