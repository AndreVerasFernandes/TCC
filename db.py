import os
from supabase import create_client, Client
import dotenv

dotenv.load_dotenv()


url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Initialize the synchronous client
supabase: Client = create_client(url, key)

# Insert a new row into the 'countries' table
response = supabase.table("teste").insert({"Envio": "New Zealand"}).execute()
print(response.data)
