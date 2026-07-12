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

__all__ = ["Interpolator"]

import collections
import functools
import graphlib
import os
import re
import typing as t

from confspec import path

if t.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable

_escaped = r"(?P<escaped>\$)"
_env_name = r"(?P<name>[a-zA-Z_]\w*)"
_env_delim = r"(?P<delim>[^]}]+)"
_env_strip = r"(?P<strip>~)"
_env_default = r"(?P<default>:[^}]*|\?)"

ENV_INTERPOLATION_PATTERN: t.Final[re.Pattern[str]] = re.compile(
    rf"{_escaped}?(?P<raw>\${{{_env_name}(?:\[{_env_delim}])?{_env_strip}?{_env_default}?}})"
)


def _env_replace_fn(match: re.Match[str]) -> str:
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


_ref_path = r"(?P<path>[\w\-]+(?:\[\d+]|\.[\w\-]+)*)"

REF_INTERPOLATION_PATTERN: t.Final[re.Pattern[str]] = re.compile(rf"{_escaped}?(?P<raw>\${{\.{_ref_path}}})")


def extract_refs(key: path.PathT, value: t.Any, *, refs: dict[path.PathT, set[path.PathT]]) -> t.Any:
    if not isinstance(value, str):
        return value

    for match in REF_INTERPOLATION_PATTERN.finditer(value):
        if match.group("escaped") is not None:
            continue

        refs[key].add(path.parse_path(match.group("path")))

    return value


def _ref_replace_fn(match: re.Match[str], *, get_ref: Callable[[path.PathT], t.Any]) -> str:
    if match.group("escaped"):
        return str(match.group("raw"))

    ref = path.parse_path(raw_ref := match.group("path"))
    value = get_ref(ref)

    if isinstance(value, (dict, list)):
        tn = type(t.cast("t.Any", value)).__name__
        raise ValueError(f"cannot expand reference {raw_ref!r} as it evaluates to non-primitive type {tn!r}")

    return str(value)


class Visitor:
    __slots__ = ("_skip_keys", "_value_fn")

    def __init__(self, value_fn: Callable[[path.PathT, t.Any], t.Any], skip_keys: Iterable[path.PathT] = ()) -> None:
        self._value_fn = value_fn
        self._skip_keys = set(skip_keys)

    def visit_value(self, key: path.PathT, val: t.Any) -> t.Any:
        if not isinstance(val, str) or key in self._skip_keys:
            return val
        return self._value_fn(key, val)

    def visit_list(self, key: path.PathT, lst: list[t.Any]) -> list[t.Any]:
        for i in range(len(lst)):
            lst[i] = self.visit(lst[i], key=(*key, i))
        return lst

    def visit_dict(self, key: path.PathT, dct: dict[str, t.Any]) -> dict[str, t.Any]:
        for k, v in list(dct.items()):
            dct[k] = self.visit(v, key=(*key, k))
        return dct

    def visit(self, item: t.Any, *, key: path.PathT = ()) -> t.Any:
        if isinstance(item, dict):
            return self.visit_dict(key, t.cast("dict[str, t.Any]", item))
        elif isinstance(item, list):
            return self.visit_list(key, t.cast("list[t.Any]", item))
        return self.visit_value(key, item)


class Interpolator:
    __slots__ = ("_data",)

    def __init__(self, data: dict[str, t.Any]) -> None:
        self._data = data

    def _set(self, key_path: path.PathT, val: t.Any) -> None:
        this = self._data
        for elem in key_path[:-1]:
            this = this[elem]  # type: ignore[reportArgumentType]
        this[key_path[-1]] = val  # type: ignore[reportArgumentType]

    def _get(self, key_path: path.PathT) -> t.Any:
        this = self._data
        for elem in key_path:
            this = this[elem]  # type: ignore[reportArgumentType]
        return this

    def _interpolate_value(self, _: path.PathT, value: str) -> t.Any:
        ref_match = REF_INTERPOLATION_PATTERN.fullmatch(value)
        if ref_match is not None and ref_match.group("escaped") is not None:
            # return the current value at the key to preserve the type
            return self._get(path.parse_path(ref_match.group("path")))

        env_match = ENV_INTERPOLATION_PATTERN.fullmatch(value)
        if env_match is not None and env_match.group("escaped") is None:
            # If the "?" (None as default) flag is present, and the variable is unset
            # then return None
            if env_match.group("default") == "?" and os.getenv(env_match.group("name")) is None:
                return None

            # if a delimiter was specified, split into list - otherwise use the standard substitution function
            if (delim := env_match.group("delim")) is not None:
                strip = env_match.group("strip") is not None
                val = os.getenv(env_match.group("name"), (env_match.group("default") or "")[1:])
                return [(elem.strip() if strip else elem) for elem in val.split(delim)]

        value = ENV_INTERPOLATION_PATTERN.sub(_env_replace_fn, value)
        return REF_INTERPOLATION_PATTERN.sub(functools.partial(_ref_replace_fn, get_ref=self._get), value)

    def _get_resolution_order(self) -> list[path.PathT]:
        refs: dict[path.PathT, set[path.PathT]] = collections.defaultdict(set)
        Visitor(functools.partial(extract_refs, refs=refs)).visit(self._data)
        return list(graphlib.TopologicalSorter(refs).static_order())

    def interpolate(self) -> dict[str, t.Any]:
        prereqs = self._get_resolution_order()

        visitor = Visitor(self._interpolate_value)
        for p in prereqs:
            self._set(p, visitor.visit(self._get(p)))

        visitor = Visitor(self._interpolate_value, skip_keys=prereqs)
        return visitor.visit(self._data)
