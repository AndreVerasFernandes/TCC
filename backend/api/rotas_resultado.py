"""
Rotas CRUD para Resultado (saída da IA) — usando cliente Supabase (PostgREST).

Endpoints:
  POST /resultados/        → registrar resultado de análise
  GET  /resultados/        → listar resultados
  GET  /resultados/{id}    → obter resultado por ID
  PUT  /resultados/{id}    → atualizar resultado (re-processamento)
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from backend.api.schemas import ResultadoAtualizar, ResultadoCriar, ResultadoResposta
from database import get_supabase

router = APIRouter()


@router.post(
    "/",
    response_model=ResultadoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar resultado da IA",
)
def criar_resultado(dados: ResultadoCriar, db: Client = Depends(get_supabase)):
    """
    Registra o resultado da análise de IA para uma refeição.
    Cada refeição pode ter no máximo um resultado (relação 1:1 — UNIQUE).
    Atualiza automaticamente o status da refeição para 'analisada'.
    """
    # Verificar se a refeição existe
    refeicao = (
        db.table("refeicao")
        .select("id")
        .eq("id", str(dados.refeicao_id))
        .execute()
    )
    if not refeicao.data:
        raise HTTPException(status_code=404, detail="Refeição não encontrada.")

    # Verificar se já existe resultado (UNIQUE constraint)
    existente = (
        db.table("resultado")
        .select("id")
        .eq("refeicao_id", str(dados.refeicao_id))
        .execute()
    )
    if existente.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um resultado para esta refeição. Use PUT para atualizar.",
        )

    # Inserir resultado
    resultado = (
        db.table("resultado")
        .insert(dados.model_dump(exclude_unset=True, mode="json"))
        .execute()
    )

    # Atualizar status da refeição para 'analisada'
    db.table("refeicao").update({
        "status": "analisada",
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }).eq("id", str(dados.refeicao_id)).execute()

    return resultado.data[0]


@router.get("/", response_model=list[ResultadoResposta], summary="Listar resultados")
def listar_resultados(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Client = Depends(get_supabase),
):
    """Lista todos os resultados de análise com paginação."""
    resultado = (
        db.table("resultado")
        .select("*")
        .order("analisado_em", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    )
    return resultado.data


@router.get(
    "/{resultado_id}",
    response_model=ResultadoResposta,
    summary="Obter resultado",
)
def obter_resultado(resultado_id: UUID, db: Client = Depends(get_supabase)):
    """Retorna um resultado de análise pelo seu ID."""
    resultado = (
        db.table("resultado")
        .select("*")
        .eq("id", str(resultado_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Resultado não encontrado.")
    return resultado.data[0]


@router.put(
    "/{resultado_id}",
    response_model=ResultadoResposta,
    summary="Atualizar resultado",
)
def atualizar_resultado(
    resultado_id: UUID,
    dados: ResultadoAtualizar,
    db: Client = Depends(get_supabase),
):
    """
    Atualiza um resultado existente (ex.: re-processamento pela IA).
    Atualiza automaticamente o timestamp de análise.
    """
    campos = dados.model_dump(exclude_unset=True, mode="json")
    if not campos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    # Atualizar timestamp de análise
    campos["analisado_em"] = datetime.now(timezone.utc).isoformat()

    resultado = (
        db.table("resultado")
        .update(campos)
        .eq("id", str(resultado_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Resultado não encontrado.")
    return resultado.data[0]
