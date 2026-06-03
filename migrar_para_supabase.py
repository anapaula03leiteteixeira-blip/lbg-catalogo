"""
Migração: catalog.json → Supabase
Execute UMA VEZ após configurar o Supabase e criar a tabela com o schema SQL.

Uso:
  1. Configure as variáveis SUPABASE_URL e SUPABASE_KEY abaixo
  2. Execute: python migrar_para_supabase.py
"""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ── CONFIGURE AQUI ────────────────────────────────────────────────────────────
SUPABASE_URL = ""   # ex: https://xyzxyz.supabase.co
SUPABASE_KEY = ""   # anon/public key do projeto
CATALOG_FILE = Path(__file__).parent / "catalog.json"
BATCH_SIZE   = 50   # produtos por lote
# ─────────────────────────────────────────────────────────────────────────────

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERRO: Configure SUPABASE_URL e SUPABASE_KEY neste arquivo.")
    sys.exit(1)

if not CATALOG_FILE.exists():
    print(f"ERRO: {CATALOG_FILE} não encontrado.")
    sys.exit(1)

from supabase import create_client

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

with open(CATALOG_FILE, encoding="utf-8") as f:
    data = json.load(f)

produtos = data.get("produtos", [])
print(f"Total de registros no catalog.json: {len(produtos)}")

# Campos que a tabela aceita (descarta campos extras do JSON)
CAMPOS_DB = {
    "sku", "nome_produto", "categoria", "subcategoria", "cor_dominante",
    "angulo", "fundo", "qualidade_foto", "material_aparente", "tags",
    "problemas_foto", "descricao_marketing", "descricao_tecnica",
    "precisa_revisao", "image_url", "hash_sha256", "arquivo_original",
    "ref_encontrada", "processado_em",
}

ok = err = 0
lote = []

for i, p in enumerate(produtos, 1):
    # Filtra só os campos que a tabela conhece
    row = {k: v for k, v in p.items() if k in CAMPOS_DB}

    # Garante que arrays são listas (não strings)
    for campo_array in ("tags", "problemas_foto"):
        val = row.get(campo_array)
        if isinstance(val, str):
            row[campo_array] = [v.strip() for v in val.split(",") if v.strip()]
        elif not isinstance(val, list):
            row[campo_array] = []

    # precisa_revisao deve ser bool
    row["precisa_revisao"] = bool(row.get("precisa_revisao", False))

    lote.append(row)

    if len(lote) >= BATCH_SIZE or i == len(produtos):
        try:
            sb.table("produtos").insert(lote).execute()
            ok += len(lote)
            print(f"  Inseridos {ok}/{len(produtos)}...")
        except Exception as e:
            print(f"  ERRO no lote (registros {i-len(lote)+1}-{i}): {e}")
            err += len(lote)
        lote = []

print(f"\n✅ Migração concluída: {ok} OK | {err} erros")
print("Agora você pode remover o catalog.json do repositório (opcional).")
