import pytest

from confspec import path


@pytest.mark.parametrize("expr,expected", [
    ("foo", ("foo",)),
    ("foo.bar", ("foo", "bar")),
    ("foo[0]", ("foo", 0)),
    ("foo.bar[0]", ("foo", "bar", 0)),
    ("foo[0][0]", ("foo", 0, 0)),
    ("foo[0].bar[0].baz", ("foo", 0, "bar", 0, "baz"))
])
def test_parse_path(expr: str, expected: path.PathT) -> None:
    assert path.parse_path(expr) == expected


def test_parse_path_fails_unknown_node() -> None:
    with pytest.raises(ValueError):
        path.parse_path("foo()")
    with pytest.raises(ValueError):
        path.parse_path("{foo, bar}")
