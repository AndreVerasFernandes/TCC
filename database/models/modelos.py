"""
Referência dos modelos de dados.

Com Supabase, NÃO usamos ORM (SQLAlchemy). As tabelas são criadas
via schema.sql (database/sql/schema.sql) e acessadas via PostgREST.

Este arquivo documenta os valores válidos dos ENUMs para referência.
"""

# ─── Valores válidos dos ENUMs do PostgreSQL ─────────────────────────

TIPOS_REFEICAO = [
    "cafe_da_manha",
    "lanche_manha",
    "almoco",
    "lanche_tarde",
    "jantar",
    "ceia",
]

STATUS_REFEICAO = [
    "aguardando_imagem_pre",
    "aguardando_imagem_pos",
    "aguardando_analise",
    "analisada",
    "erro",
]

MOMENTOS_IMAGEM = ["pre", "pos"]

STATUS_DISPOSITIVO = ["ativo", "inativo", "manutencao"]
