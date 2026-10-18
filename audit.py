
import ast


BLOCKED_IMPORTS = {
    "inspect", "pytest", "sys", "traceback", "os",
    "subprocess", "gc", "builtins", "importlib", "ctypes",
}

BLOCKED_ATTRS = {
    "_getframe", "currentframe", "stack", "argv",
    "f_back", "__code__",
}


def audit_patch(patched_source):
    """Return reasons a patch may be trying to game its tests."""
    problems = []

    try:
        tree = ast.parse(patched_source)
    except SyntaxError as exc:
        return [f"invalid Python syntax: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in BLOCKED_IMPORTS:
                    problems.append(
                        f"imports blocked module: {alias.name}"
                    )

        elif isinstance(node, ast.ImportFrom):
            if (
                node.module
                and node.module.split(".")[0] in BLOCKED_IMPORTS
            ):
                problems.append(
                    f"imports from blocked module: {node.module}"
                )

        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRS:
                problems.append(
                    f"uses introspection attribute: {node.attr}"
                )

        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "test_" in node.value or "pytest" in node.value:
                problems.append("mentions test names in a string")

    return problems
