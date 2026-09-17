import pytest

from mcp_servers.third_party_mcp import resolve_allowed_path


def test_filesystem_path_stays_inside_project():
    path = resolve_allowed_path("data/clientes.csv")
    assert path.name == "clientes.csv"
    assert path.exists()


def test_filesystem_path_rejects_traversal():
    with pytest.raises(ValueError, match="Acceso denegado"):
        resolve_allowed_path("../../fuera-del-proyecto")
