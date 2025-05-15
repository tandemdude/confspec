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
from confspec import loader

JSON_SAMPLE = """
{"foo": "bar", "baz": 123}
"""


def test_loads_json() -> None:
    parsed = loader.loads(JSON_SAMPLE, "json")

    assert isinstance(parsed, dict)
    assert parsed["foo"] == "bar"
    assert parsed["baz"] == 123


YAML_SAMPLE = """
foo: bar
baz: 123
"""


def test_loads_yaml() -> None:
    parsed = loader.loads(YAML_SAMPLE, "yaml")

    assert isinstance(parsed, dict)
    assert parsed["foo"] == "bar"
    assert parsed["baz"] == 123


TOML_SAMPLE = """
foo = "bar"
baz = 123
"""


def test_loads_toml() -> None:
    parsed = loader.loads(TOML_SAMPLE, "toml")

    assert isinstance(parsed, dict)
    assert parsed["foo"] == "bar"
    assert parsed["baz"] == 123
