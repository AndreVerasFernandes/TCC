"""
Cliente para o Cloudflare R2 (S3-compatível).
Centraliza o upload e geração de URLs para o object storage.
"""

import hashlib
import uuid

import boto3
from botocore.exceptions import ClientError

from backend.config import R2_ACCESS_KEY, R2_BUCKET, R2_ENDPOINT_URL, R2_SECRET_KEY


def _criar_cliente_s3():
    """Cria e retorna um cliente boto3 para o Cloudflare R2."""
    return boto3.client(
        service_name="s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto",
    )


def upload_imagem(
    conteudo: bytes,
    refeicao_id: str,
    momento: str,
    extensao: str = "jpg",
) -> dict:
    """
    Faz upload de uma imagem para o R2 e retorna os metadados.

    Parâmetros:
        conteudo: bytes da imagem
        refeicao_id: UUID da refeição (usado no caminho)
        momento: 'pre' ou 'pos'
        extensao: extensão do arquivo (default: jpg)

    Retorna:
        dict com bucket, object_key, tamanho_bytes e hash_sha256
    """
    # Gerar um caminho organizado: refeicoes/<refeicao_id>/<momento>_<uuid>.jpg
    nome_arquivo = f"{momento}_{uuid.uuid4().hex[:8]}.{extensao}"
    object_key = f"refeicoes/{refeicao_id}/{nome_arquivo}"

    # Calcular hash para verificação de integridade
    hash_sha256 = hashlib.sha256(conteudo).hexdigest()

    # Fazer o upload
    s3 = _criar_cliente_s3()
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=object_key,
        Body=conteudo,
        ContentType=f"image/{extensao}",
    )

    return {
        "r2_bucket": R2_BUCKET,
        "r2_object_key": object_key,
        "tamanho_bytes": len(conteudo),
        "hash_sha256": hash_sha256,
        "formato": f"image/{extensao}",
    }


def gerar_url_temporaria(object_key: str, expira_segundos: int = 3600) -> str:
    """
    Gera uma URL pré-assinada para download temporário de uma imagem.

    Parâmetros:
        object_key: caminho do objeto no R2
        expira_segundos: tempo de validade da URL (default: 1h)

    Retorna:
        URL pré-assinada como string.
    """
    s3 = _criar_cliente_s3()
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": R2_BUCKET, "Key": object_key},
            ExpiresIn=expira_segundos,
        )
        return url
    except ClientError as e:
        raise RuntimeError(f"Erro ao gerar URL temporária: {e}") from e
