import ast
import typing as t

PathT: t.TypeAlias = tuple[str | int, ...]


def parse_path(path: str) -> PathT:
    parts: list[str | int] = []

    node = ast.parse(path, mode="eval").body
    while True:
        if isinstance(node, ast.Name):
            parts.append(node.id)
            break

        if not isinstance(node, (ast.Attribute, ast.Subscript)):
            raise ValueError(f"Unsupported expression node: {ast.dump(node)}")

        if isinstance(node, ast.Attribute):
            parts.append(node.attr)
        else:
            sl = node.slice
            if isinstance(sl, ast.Constant):
                parts.append(sl.value)  # type: ignore[reportArgumentType]
            else:
                parts.append(ast.unparse(sl))

        node = node.value

    return tuple(reversed(parts))
