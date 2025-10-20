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
import os
import pathlib

import msgspec
import pydantic
import pytest

from confspec import helpers


def test_env_file_name() -> None:
    assert helpers.env_file_name(pathlib.Path("/foo/bar.yml"), "prod") == "bar.prod.yml"
    assert helpers.env_file_name(pathlib.Path("/foo/bar.baz.yml"), "prod") == "bar.prod.baz.yml"
    assert helpers.env_file_name(pathlib.Path("/foo/.baz"), "prod") == ".baz.prod"


class Struct(msgspec.Struct):
    foo: str


class Model(pydantic.BaseModel):
    foo: str


def test_is_msgspec() -> None:
    assert helpers.is_msgspec(Struct) is True
    assert helpers.is_msgspec(Model) is False


def test_is_pydantic() -> None:
    assert helpers.is_pydantic(Model) is True
    assert helpers.is_pydantic(Struct) is False


def test_sets_new_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "TEST_ENV_VAR"
    monkeypatch.delenv(key, raising=False)

    with helpers.temp_set_env(key, "temporary"):
        assert os.getenv(key) == "temporary"

    assert key not in os.environ


def test_overwrites_existing_env_var_and_restores(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "EXISTING_ENV"
    monkeypatch.setenv(key, "original")

    with helpers.temp_set_env(key, "modified"):
        assert os.getenv(key) == "modified"

    assert os.getenv(key) == "original"


def test_unset_value_does_not_set_var(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "SHOULD_NOT_EXIST"
    monkeypatch.delenv(key, raising=False)

    with helpers.temp_set_env(key, None):
        assert key not in os.environ

    assert key not in os.environ


def test_restores_environment_even_if_exception_is_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "EXC_ENV"
    monkeypatch.setenv(key, "before")

    with pytest.raises(RuntimeError), helpers.temp_set_env(key, "during"):
        assert os.getenv(key) == "during"
        raise RuntimeError("intentional error")

    # noinspection PyUnreachableCode
    assert os.getenv(key) == "before"


def test_removes_newly_added_variable_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "NEW_ENV_EXC"
    monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError), helpers.temp_set_env(key, "value"):
        assert os.getenv(key) == "value"
        raise RuntimeError("intentional error")

    # noinspection PyUnreachableCode
    assert key not in os.environ
