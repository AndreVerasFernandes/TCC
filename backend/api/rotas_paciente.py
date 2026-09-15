"""
Rotas CRUD para Paciente — usando cliente Supabase (PostgREST).

Endpoints:
  POST   /pacientes/              → cadastrar paciente
  GET    /pacientes/              → listar pacientes (paginação + filtro)
  GET    /pacientes/{id}          → obter paciente por ID
  PUT    /pacientes/{id}          → atualizar paciente
  DELETE /pacientes/{id}          → remover paciente
  GET    /pacientes/{id}/historico → histórico de refeições com resultado da IA
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from backend.api.schemas import PacienteAtualizar, PacienteCriar, PacienteResposta
from database import get_supabase

# TODO: para proteger estas rotas com autenticação Supabase, adicione:
# from backend.auth.dependencias import obter_usuario_atual
# e inclua `usuario: dict = Depends(obter_usuario_atual)` nos parâmetros.

router = APIRouter()


@router.post(
    "/",
    response_model=PacienteResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar paciente",
)
def criar_paciente(dados: PacienteCriar, db: Client = Depends(get_supabase)):
    """Cadastra um novo paciente no sistema."""

    # Verificar duplicidade do código interno (prontuário)
    existente = (
        db.table("paciente")
        .select("id")
        .eq("codigo_interno", dados.codigo_interno)
        .execute()
    )
    if existente.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um paciente com o código interno '{dados.codigo_interno}'.",
        )

    resultado = (
        db.table("paciente")
        .insert(dados.model_dump(exclude_unset=True, mode="json"))
        .execute()
    )
    return resultado.data[0]


@router.get("/", response_model=list[PacienteResposta], summary="Listar pacientes")
def listar_pacientes(
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de registros"),
    apenas_ativos: bool = Query(True, description="Filtrar apenas pacientes internados"),
    db: Client = Depends(get_supabase),
):
    """Lista pacientes com paginação e filtro por status de internação."""
    query = db.table("paciente").select("*")

    if apenas_ativos:
        query = query.eq("ativo", True)

    resultado = (
        query.order("nome").range(skip, skip + limit - 1).execute()
    )
    return resultado.data


@router.get(
    "/{paciente_id}",
    response_model=PacienteResposta,
    summary="Obter paciente",
)
def obter_paciente(paciente_id: UUID, db: Client = Depends(get_supabase)):
    """Retorna os dados de um paciente pelo seu ID."""
    resultado = (
        db.table("paciente")
        .select("*")
        .eq("id", str(paciente_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return resultado.data[0]


@router.put(
    "/{paciente_id}",
    response_model=PacienteResposta,
    summary="Atualizar paciente",
)
def atualizar_paciente(
    paciente_id: UUID,
    dados: PacienteAtualizar,
    db: Client = Depends(get_supabase),
):
    """Atualiza os dados de um paciente existente (atualização parcial)."""
    campos = dados.model_dump(exclude_unset=True, mode="json")
    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    # Registrar data/hora da atualização
    campos["atualizado_em"] = datetime.now(timezone.utc).isoformat()

    resultado = (
        db.table("paciente")
        .update(campos)
        .eq("id", str(paciente_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return resultado.data[0]


@router.delete(
    "/{paciente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover paciente",
)
def remover_paciente(paciente_id: UUID, db: Client = Depends(get_supabase)):
    """
    Remove um paciente do sistema.
    Falha com 409 se houver refeições associadas (ON DELETE RESTRICT).
    """
    # Verificar se há refeições associadas antes de tentar deletar
    refeicoes = (
        db.table("refeicao")
        .select("id")
        .eq("paciente_id", str(paciente_id))
        .limit(1)
        .execute()
    )
    if refeicoes.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paciente possui refeições associadas. Remova-as primeiro.",
        )

    resultado = (
        db.table("paciente")
        .delete()
        .eq("id", str(paciente_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")


@router.get(
    "/{paciente_id}/historico",
    summary="Histórico de refeições",
)
def historico_paciente(
    paciente_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Client = Depends(get_supabase),
):
    """
    Retorna o histórico de refeições de um paciente,
    incluindo o resultado da IA (quando disponível), via join automático do PostgREST.
    """
    # Verificar se o paciente existe
    paciente = (
        db.table("paciente")
        .select("id")
        .eq("id", str(paciente_id))
        .execute()
    )
    if not paciente.data:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    # Buscar refeições com resultado embutido (join via PostgREST)
    resultado = (
        db.table("refeicao")
        .select("*, resultado(*)")
        .eq("paciente_id", str(paciente_id))
        .order("data_refeicao", desc=True)
        .order("criado_em", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    )
    return resultado.data
