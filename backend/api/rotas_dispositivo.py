"""
Rotas CRUD para Dispositivo IoT — usando cliente Supabase (PostgREST).

Endpoints:
  POST   /dispositivos/      → cadastrar dispositivo
  GET    /dispositivos/      → listar dispositivos
  GET    /dispositivos/{id}  → obter dispositivo por ID
  PUT    /dispositivos/{id}  → atualizar dispositivo
  DELETE /dispositivos/{id}  → remover dispositivo
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from backend.api.schemas import DispositivoAtualizar, DispositivoCriar, DispositivoResposta
from database import get_supabase

router = APIRouter()


@router.post(
    "/",
    response_model=DispositivoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar dispositivo",
)
def criar_dispositivo(dados: DispositivoCriar, db: Client = Depends(get_supabase)):
    """Cadastra um novo dispositivo IoT (Raspberry Pi + câmera)."""

    # Verificar duplicidade do código do dispositivo
    existente = (
        db.table("dispositivo_iot")
        .select("id")
        .eq("codigo", dados.codigo)
        .execute()
    )
    if existente.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um dispositivo com o código '{dados.codigo}'.",
        )

    resultado = (
        db.table("dispositivo_iot")
        .insert(dados.model_dump(exclude_unset=True, mode="json"))
        .execute()
    )
    return resultado.data[0]


@router.get(
    "/",
    response_model=list[DispositivoResposta],
    summary="Listar dispositivos",
)
def listar_dispositivos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filtro: str | None = Query(
        None,
        alias="status",
        description="Filtrar por status (ativo, inativo, manutencao)",
    ),
    db: Client = Depends(get_supabase),
):
    """Lista dispositivos IoT com paginação e filtro opcional por status."""
    query = db.table("dispositivo_iot").select("*")

    if status_filtro:
        query = query.eq("status", status_filtro)

    resultado = (
        query.order("codigo").range(skip, skip + limit - 1).execute()
    )
    return resultado.data


@router.get(
    "/{dispositivo_id}",
    response_model=DispositivoResposta,
    summary="Obter dispositivo",
)
def obter_dispositivo(dispositivo_id: UUID, db: Client = Depends(get_supabase)):
    """Retorna os dados de um dispositivo IoT pelo seu ID."""
    resultado = (
        db.table("dispositivo_iot")
        .select("*")
        .eq("id", str(dispositivo_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado.")
    return resultado.data[0]


@router.put(
    "/{dispositivo_id}",
    response_model=DispositivoResposta,
    summary="Atualizar dispositivo",
)
def atualizar_dispositivo(
    dispositivo_id: UUID,
    dados: DispositivoAtualizar,
    db: Client = Depends(get_supabase),
):
    """Atualiza os dados de um dispositivo existente (atualização parcial)."""
    campos = dados.model_dump(exclude_unset=True, mode="json")
    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    campos["atualizado_em"] = datetime.now(timezone.utc).isoformat()

    resultado = (
        db.table("dispositivo_iot")
        .update(campos)
        .eq("id", str(dispositivo_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado.")
    return resultado.data[0]


@router.delete(
    "/{dispositivo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover dispositivo",
)
def remover_dispositivo(dispositivo_id: UUID, db: Client = Depends(get_supabase)):
    """
    Remove um dispositivo IoT.
    Falha com 409 se houver imagens capturadas por este dispositivo.
    """
    # Verificar se há imagens associadas (ON DELETE RESTRICT)
    imagens = (
        db.table("imagem")
        .select("id")
        .eq("dispositivo_iot_id", str(dispositivo_id))
        .limit(1)
        .execute()
    )
    if imagens.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dispositivo possui imagens associadas. Remova-as primeiro.",
        )

    resultado = (
        db.table("dispositivo_iot")
        .delete()
        .eq("id", str(dispositivo_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado.")
