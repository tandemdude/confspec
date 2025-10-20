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

__all__ = ["env_file_name", "is_msgspec", "is_pydantic"]

import contextlib
import os
import typing as t

if t.TYPE_CHECKING:
    import pathlib
    from collections.abc import Generator

    import msgspec
    import pydantic
    import typing_extensions as t_ex


def env_file_name(path: pathlib.Path, env: str) -> str:
    base = path.name[: path.name.find(".") or len(path.name)]
    return f"{base}.{env}{''.join(path.suffixes)}"


def is_msgspec(cls: t.Any) -> t_ex.TypeGuard[type[msgspec.Struct]]:
    try:
        import msgspec

        return issubclass(cls, msgspec.Struct)
    except ImportError:
        return False


def is_pydantic(cls: t.Any) -> t_ex.TypeGuard[type[pydantic.BaseModel]]:
    try:
        import pydantic

        return issubclass(cls, pydantic.BaseModel)
    except ImportError:
        return False


@contextlib.contextmanager
def temp_set_env(key: str, value: str | None) -> Generator[None, t.Any, t.Any]:
    old_value = os.getenv(key, None)

    if value is not None:
        os.environ[key] = value

    try:
        yield
    finally:
        if old_value is not None:
            os.environ[key] = old_value
        else:
            os.environ.pop(key, None)
