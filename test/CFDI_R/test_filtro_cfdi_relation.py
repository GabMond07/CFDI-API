import pytest
from pydantic import ValidationError
from src.Models.filtro_cfdi_relation import FiltroCFDIRelation  # Ajusta el import según tu estructura


def test_filtro_cfdi_relation_valido():
    filtro = FiltroCFDIRelation(
        related_uuid="123e4567-e89b-12d3-a456-426614174000",
        relation_type="04",
        ordenar_por="id",
        ordenar_dir="asc",
        pagina=2,
        por_pagina=20
    )
    assert filtro.related_uuid == "123e4567-e89b-12d3-a456-426614174000"
    assert filtro.ordenar_por == "id"
    assert filtro.pagina == 2


def test_filtro_cfdi_relation_uuid_invalido():
    with pytest.raises(ValidationError) as exc:
        FiltroCFDIRelation(related_uuid="UUID_invalido")
    assert "related_uuid debe ser un UUID v4 válido" in str(exc.value)


def test_filtro_cfdi_relation_ordenar_por_invalido():
    with pytest.raises(ValidationError) as exc:
        FiltroCFDIRelation(ordenar_por="no_existe")
    assert "ordenar_por inválido" in str(exc.value)


def test_filtro_cfdi_relation_ordenar_dir_invalido():
    with pytest.raises(ValidationError) as exc:
        FiltroCFDIRelation(ordenar_dir="sube")
    assert "ordenar_dir debe ser 'asc' o 'desc'" in str(exc.value)


def test_filtro_cfdi_relation_paginacion_invalida():
    with pytest.raises(ValidationError):
        FiltroCFDIRelation(pagina=0)

    with pytest.raises(ValidationError):
        FiltroCFDIRelation(por_pagina=200)
