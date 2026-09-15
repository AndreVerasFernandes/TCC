"""
Ponto de entrada da aplicação FastAPI.
Para rodar: uvicorn backend.main:app --reload
"""

from fastapi import FastAPI

from backend.api import (
    rotas_dispositivo,
    rotas_imagem,
    rotas_paciente,
    rotas_refeicao,
    rotas_resultado,
)

app = FastAPI(
    title="Monitoramento Nutricional Hospitalar",
    description=(
        "API REST para monitoramento do consumo nutricional de pacientes internados. "
        "Integra IoT, visão computacional e IA para estimar ingestão alimentar. "
        "Banco de dados via Supabase (PostgREST), imagens no Cloudflare R2."
    ),
    version="0.1.0",
)

# ─── Rotas ───────────────────────────────────────────────────────────
app.include_router(rotas_paciente.router, prefix="/pacientes", tags=["Pacientes"])
app.include_router(rotas_refeicao.router, prefix="/refeicoes", tags=["Refeições"])
app.include_router(rotas_imagem.router, prefix="/imagens", tags=["Imagens"])
app.include_router(rotas_resultado.router, prefix="/resultados", tags=["Resultados"])
app.include_router(rotas_dispositivo.router, prefix="/dispositivos", tags=["Dispositivos IoT"])


@app.get("/", tags=["Saúde"])
def raiz():
    """Endpoint de verificação de saúde da API."""
    return {
        "status": "ok",
        "projeto": "Monitoramento Nutricional Hospitalar",
        "versao": "0.1.0",
        "banco": "Supabase (PostgREST)",
        "storage": "Cloudflare R2",
    }
