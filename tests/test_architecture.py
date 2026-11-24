import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "boxoffice"
FORBIDDEN = {
    "domain": {"sqlalchemy", "fastapi", "pydantic", "jwt", "starlette", "boxoffice.audit",
               "boxoffice.application", "boxoffice.infrastructure", "boxoffice.presentation"},
    "application": {"sqlalchemy", "fastapi", "pydantic", "jwt", "boxoffice.audit",
                    "boxoffice.infrastructure", "boxoffice.presentation"},
    "infrastructure": {"fastapi", "boxoffice.presentation", "boxoffice.audit.service", "boxoffice.audit.storage"},
    "presentation": {"sqlalchemy", "boxoffice.infrastructure", "boxoffice.audit.service", "boxoffice.audit.storage"},
    "audit": {"fastapi", "boxoffice.domain", "boxoffice.application", "boxoffice.infrastructure",
              "boxoffice.presentation"},
}


def imports_of(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_layers_do_not_import_forbidden_modules():
    violations = []
    for layer, forbidden in FORBIDDEN.items():
        for file in (SRC / layer).glob("*.py"):
            for module in imports_of(file):
                if any(module == f or module.startswith(f + ".") for f in forbidden):
                    violations.append(f"{layer}/{file.name} imports {module}")
    assert not violations, "\n".join(violations)
