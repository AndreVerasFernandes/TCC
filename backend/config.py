"""
Configurações centralizadas do backend.
Variáveis do Supabase (URL/KEY) ficam em database/__init__.py.
Aqui ficam apenas JWT e R2.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ─── Supabase Auth (JWT) ─────────────────────────────────────────────
# O JWT Secret do projeto fica em: Supabase Dashboard → Settings → API → JWT Secret
SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

# ─── Cloudflare R2 (S3-compatível) ───────────────────────────────────
R2_ENDPOINT_URL: str = os.getenv("URL", os.getenv("URL", ""))
R2_ACCESS_KEY: str = os.getenv("<ACCESS_KEY_ID>", os.getenv("<ACCESS_KEY_ID>", ""))
R2_SECRET_KEY: str = os.getenv("<SECRET_ACCESS_KEY>", os.getenv("<SECRET_ACCESS_KEY>", ""))
R2_BUCKET: str = os.getenv("R2_BUCKET", "tcc")
