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
import pytest

from confspec import interpolate


def test_interpolate_variable_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "bar")

    assert interpolate.try_interpolate("${FOO}") == "bar"


def test_interpolate_variable_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOO", raising=False)

    with pytest.raises(KeyError):
        interpolate.try_interpolate("${FOO}")


def test_interpolate_escaped() -> None:
    assert interpolate.try_interpolate("$${FOO}") == "${FOO}"


def test_interpolate_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "     bar      ")

    assert interpolate.try_interpolate("${FOO}") != "bar"
    assert interpolate.try_interpolate("${FOO~}") == "bar"


def test_interpolate_list_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "bar,baz,bork")

    assert interpolate.try_interpolate("${FOO[,]}") == ["bar", "baz", "bork"]


def test_interpolate_list_expansion_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "  bar   ,     baz ,bork   ")

    assert interpolate.try_interpolate("${FOO[,]~}") == ["bar", "baz", "bork"]


def test_interpolate_default_variable_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOO", "bar")

    assert interpolate.try_interpolate("${FOO:baz}") == "bar"


def test_interpolate_default_variable_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FOO", raising=False)

    assert interpolate.try_interpolate("${FOO:baz}") == "baz"
