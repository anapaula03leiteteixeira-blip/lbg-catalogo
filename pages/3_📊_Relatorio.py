"""
La Bella Griffe — Relatório do Catálogo
Métricas, gráficos e lista de revisão — dados do Supabase.
"""

import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Relatório | LBG", page_icon="📊", layout="wide")
st.title("📊 Relatório do Catálogo")

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=60)
def load():
    sb = get_supabase()
    all_rows, offset, batch = [], 0, 1000
    while True:
        resp = sb.table("produtos").select("*").range(offset, offset + batch - 1).execute()
        rows = resp.data or []
        all_rows.extend(rows)
        if len(rows) < batch:
            break
        offset += batch
    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

df = load()

if df.empty:
    st.info("Catálogo vazio. Cadastre produtos na página **📦 Novo Produto**.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total de fotos",      len(df))
k2.metric("SKUs únicos",         df["sku"].nunique() if "sku" in df.columns else "—")
k3.metric("Categorias",          df["categoria"].nunique() if "categoria" in df.columns else "—")
k4.metric("Qualidade excelente", int((df["qualidade_foto"] == "excelente").sum()) if "qualidade_foto" in df.columns else "—")
k5.metric("Para revisão",        int(df["precisa_revisao"].sum()) if "precisa_revisao" in df.columns else "—")

st.divider()

# ── Gráficos ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Por Categoria")
    if "categoria" in df.columns:
        st.bar_chart(df["categoria"].value_counts().rename_axis("Categoria").reset_index(name="Fotos").set_index("Categoria"))

with col2:
    st.subheader("Por Qualidade da Foto")
    if "qualidade_foto" in df.columns:
        order = ["excelente", "boa", "regular", "ruim"]
        st.bar_chart(
            df["qualidade_foto"].value_counts()
            .reindex(order).dropna()
            .rename_axis("Qualidade").reset_index(name="Fotos")
            .set_index("Qualidade")
        )

st.subheader("Detalhamento por Categoria e Qualidade")
if "categoria" in df.columns and "qualidade_foto" in df.columns:
    pivot = df.groupby(["categoria", "qualidade_foto"]).size().unstack(fill_value=0)
    cols_order = [c for c in ["excelente", "boa", "regular", "ruim"] if c in pivot.columns]
    st.dataframe(pivot[cols_order], use_container_width=True)

st.subheader("Ângulos Mais Fotografados")
if "angulo" in df.columns:
    st.bar_chart(df["angulo"].value_counts().rename_axis("Ângulo").reset_index(name="Fotos").set_index("Ângulo"))

# ── Revisão ───────────────────────────────────────────────────────────────────
st.divider()
st.subheader("⚠️ Produtos para Revisão Manual")

revisao_df = df[df["precisa_revisao"] == True].copy() if "precisa_revisao" in df.columns else pd.DataFrame()

if revisao_df.empty:
    st.success("✅ Nenhum produto aguardando revisão!")
else:
    st.warning(f"{len(revisao_df)} foto(s) aguardando revisão.")
    show_cols = [c for c in ["sku", "nome_produto", "categoria", "qualidade_foto", "image_url"] if c in revisao_df.columns]
    st.dataframe(revisao_df[show_cols].rename(columns={
        "sku": "SKU", "nome_produto": "Nome", "categoria": "Categoria",
        "qualidade_foto": "Qualidade", "image_url": "URL Imagem",
    }), use_container_width=True, hide_index=True)

    csv = revisao_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Exportar lista de revisão (CSV)", csv, "lbg-revisao.csv", "text/csv")

st.divider()
st.subheader("Top 10 SKUs com mais fotos")
if "sku" in df.columns:
    st.bar_chart(df["sku"].value_counts().head(10).rename_axis("SKU").reset_index(name="Fotos").set_index("SKU"))

# ── Exportar tudo ─────────────────────────────────────────────────────────────
st.divider()
csv_all = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 Exportar catálogo completo (CSV)", csv_all, "lbg-catalogo-completo.csv", "text/csv")
