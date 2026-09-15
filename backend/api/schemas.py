"""
Esquemas Pydantic para validação de dados na API.
Cada entidade tem esquemas de Criação, Atualização e Resposta.

Convenção:
  - *Criar     → campos obrigatórios para inserção
  - *Atualizar → todos os campos opcionais (patch parcial)
  - *Resposta  → representação completa retornada pela API
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════════
# PACIENTE
# ═══════════════════════════════════════════════════════════════════════

class PacienteCriar(BaseModel):
    """Dados necessários para cadastrar um novo paciente."""
    codigo_interno: str = Field(
        ..., max_length=50,
        description="Código de prontuário hospitalar (sem CPF — LGPD)",
    )
    nome: str = Field(..., max_length=200, description="Nome completo do paciente")
    data_nascimento: date | None = Field(None, description="Data de nascimento")
    sexo: str | None = Field(None, pattern=r"^[MFO]$", description="M, F ou O")
    leito: str | None = Field(None, max_length=50, description="Leito/quarto atual")


class PacienteAtualizar(BaseModel):
    """Campos opcionais para atualizar um paciente."""
    nome: str | None = Field(None, max_length=200)
    data_nascimento: date | None = None
    sexo: str | None = Field(None, pattern=r"^[MFO]$")
    leito: str | None = Field(None, max_length=50)
    ativo: bool | None = None


class PacienteResposta(BaseModel):
    """Representação completa de um paciente na resposta da API."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo_interno: str
    nome: str
    data_nascimento: date | None
    sexo: str | None
    leito: str | None
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime


# ═══════════════════════════════════════════════════════════════════════
# DISPOSITIVO IoT
# ═══════════════════════════════════════════════════════════════════════

class DispositivoCriar(BaseModel):
    """Dados para cadastrar um novo dispositivo IoT."""
    codigo: str = Field(..., max_length=50, description="Código/etiqueta do dispositivo")
    descricao: str | None = Field(None, description="Descrição livre")
    modelo_camera: str | None = Field(None, max_length=100)
    localizacao: str | None = Field(None, max_length=200)


class DispositivoAtualizar(BaseModel):
    """Campos opcionais para atualizar um dispositivo."""
    descricao: str | None = None
    modelo_camera: str | None = Field(None, max_length=100)
    localizacao: str | None = Field(None, max_length=200)
    status: str | None = Field(None, pattern=r"^(ativo|inativo|manutencao)$")


class DispositivoResposta(BaseModel):
    """Representação completa de um dispositivo IoT."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str
    descricao: str | None
    modelo_camera: str | None
    localizacao: str | None
    status: str
    criado_em: datetime
    atualizado_em: datetime


# ═══════════════════════════════════════════════════════════════════════
# REFEIÇÃO
# ═══════════════════════════════════════════════════════════════════════

class RefeicaoCriar(BaseModel):
    """Dados para registrar uma nova refeição."""
    paciente_id: UUID = Field(..., description="ID do paciente que receberá a refeição")
    tipo: str = Field(
        ...,
        description="Tipo: cafe_da_manha, lanche_manha, almoco, lanche_tarde, jantar, ceia",
    )
    data_refeicao: date | None = Field(None, description="Data da refeição (default: hoje)")
    hora_entrega: datetime | None = Field(None, description="Hora de entrega da bandeja")
    observacoes: str | None = None


class RefeicaoAtualizar(BaseModel):
    """Campos opcionais para atualizar uma refeição."""
    tipo: str | None = None
    status: str | None = None
    hora_entrega: datetime | None = None
    hora_retirada: datetime | None = None
    observacoes: str | None = None


class RefeicaoResposta(BaseModel):
    """Representação completa de uma refeição."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    paciente_id: UUID
    tipo: str
    status: str
    data_refeicao: date
    hora_entrega: datetime | None
    hora_retirada: datetime | None
    observacoes: str | None
    criado_em: datetime
    atualizado_em: datetime


# ═══════════════════════════════════════════════════════════════════════
# IMAGEM
# ═══════════════════════════════════════════════════════════════════════

class ImagemMetadados(BaseModel):
    """Metadados enviados junto com o upload (via form fields)."""
    refeicao_id: UUID
    dispositivo_iot_id: UUID
    momento: str = Field(..., pattern=r"^(pre|pos)$", description="'pre' ou 'pos'")


class ImagemResposta(BaseModel):
    """Representação completa de uma imagem (metadados — o binário está no R2)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    refeicao_id: UUID
    dispositivo_iot_id: UUID
    momento: str
    r2_bucket: str
    r2_object_key: str
    formato: str | None
    tamanho_bytes: int | None
    hash_sha256: str | None
    capturada_em: datetime
    criado_em: datetime


# ═══════════════════════════════════════════════════════════════════════
# RESULTADO (saída da IA)
# ═══════════════════════════════════════════════════════════════════════

class ResultadoCriar(BaseModel):
    """Dados do resultado da análise de IA para uma refeição."""
    refeicao_id: UUID
    alimentos_detectados: list[dict[str, Any]] = Field(
        default_factory=list,
        description='Ex.: [{"nome": "arroz", "confianca": 0.95}]',
    )
    percentual_ingestao: Decimal | None = Field(None, ge=0, le=100)
    calorias_estimadas: Decimal | None = None
    proteinas_g: Decimal | None = None
    carboidratos_g: Decimal | None = None
    gorduras_g: Decimal | None = None
    fibras_g: Decimal | None = None
    modelo_versao: str | None = None
    tempo_processamento_ms: int | None = None


class ResultadoAtualizar(BaseModel):
    """Campos opcionais para atualizar um resultado."""
    alimentos_detectados: list[dict[str, Any]] | None = None
    percentual_ingestao: Decimal | None = Field(None, ge=0, le=100)
    calorias_estimadas: Decimal | None = None
    proteinas_g: Decimal | None = None
    carboidratos_g: Decimal | None = None
    gorduras_g: Decimal | None = None
    fibras_g: Decimal | None = None
    modelo_versao: str | None = None
    tempo_processamento_ms: int | None = None


class ResultadoResposta(BaseModel):
    """Representação completa de um resultado de IA."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    refeicao_id: UUID
    alimentos_detectados: list[dict[str, Any]]
    percentual_ingestao: Decimal | None
    calorias_estimadas: Decimal | None
    proteinas_g: Decimal | None
    carboidratos_g: Decimal | None
    gorduras_g: Decimal | None
    fibras_g: Decimal | None
    modelo_versao: str | None
    tempo_processamento_ms: int | None
    analisado_em: datetime
    criado_em: datetime
