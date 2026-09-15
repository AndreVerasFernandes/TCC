"""
Rotas para Imagem — usando cliente Supabase (PostgREST) + R2.
O upload envia o arquivo para o Cloudflare R2 e salva metadados no Supabase.

Endpoints:
  POST /imagens/upload     → upload de imagem (multipart) + metadados no banco
  GET  /imagens/           → listar metadados de imagens
  GET  /imagens/{id}       → obter metadados de uma imagem
  GET  /imagens/{id}/url   → gerar URL temporária para download da imagem no R2
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from supabase import Client

from backend.api.schemas import ImagemResposta
from backend.storage import gerar_url_temporaria, upload_imagem
from database import get_supabase

router = APIRouter()


@router.post(
    "/upload",
    response_model=ImagemResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de imagem",
)
async def fazer_upload(
    refeicao_id: UUID = Form(..., description="ID da refeição"),
    dispositivo_iot_id: UUID = Form(..., description="ID do dispositivo que capturou"),
    momento: str = Form(..., pattern=r"^(pre|pos)$", description="'pre' ou 'pos'"),
    arquivo: UploadFile = File(..., description="Arquivo da imagem (JPEG/PNG)"),
    db: Client = Depends(get_supabase),
):
    """
    Recebe a imagem via multipart form, faz upload para o Cloudflare R2
    e salva os metadados no Supabase (PostgREST).

    Atualiza automaticamente o status da refeição:
      - Após imagem pré → status = 'aguardando_imagem_pos'
      - Após imagem pós → status = 'aguardando_analise'
    """
    # ─── Validações ──────────────────────────────────────────────────
    refeicao = (
        db.table("refeicao")
        .select("id, status")
        .eq("id", str(refeicao_id))
        .execute()
    )
    if not refeicao.data:
        raise HTTPException(status_code=404, detail="Refeição não encontrada.")

    dispositivo = (
        db.table("dispositivo_iot")
        .select("id")
        .eq("id", str(dispositivo_iot_id))
        .execute()
    )
    if not dispositivo.data:
        raise HTTPException(status_code=404, detail="Dispositivo IoT não encontrado.")

    # Verificar se já existe imagem para esse momento (constraint UNIQUE)
    existente = (
        db.table("imagem")
        .select("id")
        .eq("refeicao_id", str(refeicao_id))
        .eq("momento", momento)
        .execute()
    )
    if existente.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe uma imagem '{momento}' para esta refeição.",
        )

    # ─── Upload para o R2 ───────────────────────────────────────────
    conteudo = await arquivo.read()

    # Determinar extensão do arquivo
    extensao = "jpg"
    if arquivo.content_type and "png" in arquivo.content_type:
        extensao = "png"

    dados_r2 = upload_imagem(
        conteudo=conteudo,
        refeicao_id=str(refeicao_id),
        momento=momento,
        extensao=extensao,
    )

    # ─── Salvar metadados no Supabase ────────────────────────────────
    resultado = (
        db.table("imagem")
        .insert({
            "refeicao_id": str(refeicao_id),
            "dispositivo_iot_id": str(dispositivo_iot_id),
            "momento": momento,
            "r2_bucket": dados_r2["r2_bucket"],
            "r2_object_key": dados_r2["r2_object_key"],
            "formato": dados_r2["formato"],
            "tamanho_bytes": dados_r2["tamanho_bytes"],
            "hash_sha256": dados_r2["hash_sha256"],
        })
        .execute()
    )

    # ─── Atualizar status da refeição ────────────────────────────────
    novo_status = "aguardando_imagem_pos" if momento == "pre" else "aguardando_analise"
    db.table("refeicao").update({"status": novo_status}).eq("id", str(refeicao_id)).execute()

    return resultado.data[0]


@router.get("/", response_model=list[ImagemResposta], summary="Listar imagens")
def listar_imagens(
    refeicao_id: UUID | None = Query(None, description="Filtrar por refeição"),
    dispositivo_iot_id: UUID | None = Query(None, description="Filtrar por dispositivo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Client = Depends(get_supabase),
):
    """Lista metadados de imagens com filtros opcionais."""
    query = db.table("imagem").select("*")

    if refeicao_id:
        query = query.eq("refeicao_id", str(refeicao_id))
    if dispositivo_iot_id:
        query = query.eq("dispositivo_iot_id", str(dispositivo_iot_id))

    resultado = (
        query.order("criado_em", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    )
    return resultado.data


@router.get("/{imagem_id}", response_model=ImagemResposta, summary="Obter imagem")
def obter_imagem(imagem_id: UUID, db: Client = Depends(get_supabase)):
    """Retorna os metadados de uma imagem pelo seu ID."""
    resultado = (
        db.table("imagem")
        .select("*")
        .eq("id", str(imagem_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    return resultado.data[0]


@router.get("/{imagem_id}/url", summary="Gerar URL temporária")
def obter_url_temporaria(imagem_id: UUID, db: Client = Depends(get_supabase)):
    """
    Gera uma URL pré-assinada (1h) para download da imagem no R2.
    Útil para exibir a imagem no dashboard ou em aplicações externas.
    """
    resultado = (
        db.table("imagem")
        .select("r2_object_key")
        .eq("id", str(imagem_id))
        .execute()
    )
    if not resultado.data:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    url = gerar_url_temporaria(resultado.data[0]["r2_object_key"])
    return {"url": url, "expira_em_segundos": 3600}
