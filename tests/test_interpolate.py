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
import graphlib

import pytest

from confspec import interpolate


@pytest.fixture
def itp() -> interpolate.Interpolator:
    return interpolate.Interpolator({})


def test_interpolate_variable_set(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "bar")

    assert itp._interpolate_value((), "${FOO}") == "bar"


def test_interpolate_variable_unset(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.delenv("FOO", raising=False)

    with pytest.raises(KeyError):
        itp._interpolate_value((), "${FOO}")


def test_interpolate_escaped(itp: interpolate.Interpolator) -> None:
    assert itp._interpolate_value((), "$${FOO}") == "${FOO}"


def test_interpolate_stripped(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "     bar      ")

    assert itp._interpolate_value((), "${FOO}") != "bar"
    assert itp._interpolate_value((), "${FOO~}") == "bar"


def test_interpolate_list_expansion(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "bar,baz,bork")

    assert itp._interpolate_value((), "${FOO[,]}") == ["bar", "baz", "bork"]


def test_interpolate_list_expansion_stripped(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "  bar   ,     baz ,bork   ")

    assert itp._interpolate_value((), "${FOO[,]~}") == ["bar", "baz", "bork"]


def test_interpolate_default_variable_set(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "bar")

    assert itp._interpolate_value((), "${FOO:baz}") == "bar"


def test_interpolate_default_variable_unset(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.delenv("FOO", raising=False)

    assert itp._interpolate_value((), "${FOO:baz}") == "baz"


def test_interpolate_default_none_variable_set(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "bar")

    assert itp._interpolate_value((), "${FOO?}") == "bar"


def test_interpolate_default_none_variable_unset(
    monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator
) -> None:
    monkeypatch.delenv("FOO", raising=False)

    assert itp._interpolate_value((), "${FOO?}") is None


def test_interpolate_composite_string(monkeypatch: pytest.MonkeyPatch, itp: interpolate.Interpolator) -> None:
    monkeypatch.setenv("FOO", "bar")
    monkeypatch.setenv("BAZ", "bork")

    assert itp._interpolate_value((), "${FOO} qux ${BAZ}") == "bar qux bork"


def test_interpolate_simple_refrence() -> None:
    itp = interpolate.Interpolator({"foo": "bar", "baz": "${.foo}"})
    assert itp.interpolate()["baz"] == "bar"


def test_interpolate_nested_refrence() -> None:
    itp = interpolate.Interpolator({"foo": {"bar": "baz"}, "bork": "${.foo.bar}"})
    assert itp.interpolate()["bork"] == "baz"


def test_interpolate_array_refrence() -> None:
    itp = interpolate.Interpolator({"foo": ["bar"], "baz": "${.foo[0]}"})
    assert itp.interpolate()["baz"] == "bar"


def test_interpolate_nested_array_reference() -> None:
    itp = interpolate.Interpolator({"foo": {"bar": ["baz"]}, "bork": "${.foo.bar[0]}"})
    assert itp.interpolate()["bork"] == "baz"


def test_interpolate_reference_preserves_type() -> None:
    itp = interpolate.Interpolator({"foo": 1234, "baz": "${.foo}"})
    assert itp.interpolate()["foo"] == 1234


def test_interpolate_circular_refrence() -> None:
    itp = interpolate.Interpolator({"foo": "${.bar}", "bar": "${.foo}"})
    with pytest.raises(graphlib.CycleError):
        itp.interpolate()


def test_interpolate_composite_reference() -> None:
    itp = interpolate.Interpolator({"foo": 1234, "bar": "baz", "bork": "${.foo} ${.bar}"})
    assert itp.interpolate()["bork"] == "1234 baz"


def test_interpolate_double_nested_array_reference() -> None:
    itp = interpolate.Interpolator({"foo": [[{"bar": "baz"}]], "bork": "${.foo[0][0].bar}"})
    assert itp.interpolate()["bork"] == "baz"
