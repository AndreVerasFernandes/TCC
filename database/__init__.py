"""
Cliente Supabase centralizado.
Acessa o PostgreSQL via PostgREST (API REST do Supabase).

Usa a service_role key para acesso completo (sem RLS) no backend.
A anon key deve ser usada apenas no frontend.
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase() -> Client:
    """
    Dependência FastAPI que retorna o cliente Supabase.
    Uso: db: Client = Depends(get_supabase)
    """
    return supabase
