"""
Rotas CRUD para Refeição — usando cliente Supabase (PostgREST).

Endpoints:
  POST   /refeicoes/           → registrar nova refeição
  GET    /refeicoes/pendentes  → fila de refeições aguardando análise da IA
  GET    /refeicoes/           → listar refeições (com filtros)
  GET    /refeicoes/{id}       → obter refeição (com imagens e resultado via join)
  PUT    /refeicoes/{id}       → atualizar refeição
  DELETE /refeicoes/{id}       → remover refeição
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from backend.api.schemas import RefeicaoAtualizar, RefeicaoCriar, RefeicaoResposta
from database import get_supabase

router = APIRouter()


@router.post(
    "/",
    response_model=RefeicaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar refeição",
)
def criar_refeicao(dados: RefeicaoCriar, db: Client = Depends(get_supabase)):
    """
    Registra uma nova refeição para um paciente.
    O status inicial é 'aguardando_imagem_pre'.
    """
    # Verificar se o paciente existe
    paciente = (
        db.table("paciente")
        .select("id")
        .eq("id", str(dados.paciente_id))
        .execute()
    )
    if not paciente.data:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    resultado = (
        db.table("refeicao")
        .insert(dados.model_dump(exclude_unset=True, mode="json"))
        .execute()
    )
    return resultado.data[0]


@router.get(
    "/pendentes",
    response_model=list[RefeicaoResposta],
    summary="Fila de análise da IA",
)
def listar_pendentes(
    limit: int = Query(20, ge=1, le=100),
    db: Client = Depends(get_supabase),
):
    """
    Lista refeições com status 'aguardando_analise' — ou seja,
    que já têm as duas imagens (pré e pós) e aguardam processamento da IA.
    Ordenadas da mais antiga para a mais recente (FIFO).
    """
    resultado = (
        db.table("refeicao")
        .select("*")
        .eq("status", "aguardando_analise")
        .order("criado_em")
        .limit(limit)
        .execute()
    )
    return resultado.data


@router.get("/", response_model=list[RefeicaoResposta], summary="Listar refeições")
def listar_refeicoes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    paciente_id: UUID | None = Query(None, description="Filtrar por paciente"),
    status_filtro: str | None = Query(None, alias="status", description="Filtrar por status"),
    db: Client = Depends(get_supabase),
):
    """Lista refeições com paginação e filtros opcionais."""
    query = db.table("refeicao").select("*")

    if paciente_id:
        query = query.eq("paciente_id", str(paciente_id))
    if status_filtro:
        query = query.eq("status", status_filtro)

    resultado = (
        query.order("data_refeicao", desc=True)
        .order("criado_em", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    )
    return resultado.data


@router.get("/{refeicao_id}", summary="Obter refeição com detalhes")
def obter_refeicao(refeicao_id: UUID, db: Client = Depends(get_supabase)):
    """
    Retorna uma refeição pelo ID, incluindo imagens e resultado da IA
    via join automático do PostgREST (embedded resources).
    """
    resultado = (
        db.table("refeicao")
        .select("*, imagem(*), resultado(*)")
        .eq("id", str(refeicao_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Refeição não encontrada.")
    return resultado.data[0]


@router.put(
    "/{refeicao_id}",
    response_model=RefeicaoResposta,
    summary="Atualizar refeição",
)
def atualizar_refeicao(
    refeicao_id: UUID,
    dados: RefeicaoAtualizar,
    db: Client = Depends(get_supabase),
):
    """Atualiza os dados de uma refeição existente (atualização parcial)."""
    campos = dados.model_dump(exclude_unset=True, mode="json")
    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    campos["atualizado_em"] = datetime.now(timezone.utc).isoformat()

    resultado = (
        db.table("refeicao")
        .update(campos)
        .eq("id", str(refeicao_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Refeição não encontrada.")
    return resultado.data[0]


@router.delete(
    "/{refeicao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover refeição",
)
def remover_refeicao(refeicao_id: UUID, db: Client = Depends(get_supabase)):
    """Remove uma refeição e seus dados associados (imagens e resultado via CASCADE)."""
    resultado = (
        db.table("refeicao")
        .delete()
        .eq("id", str(refeicao_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Refeição não encontrada.")
