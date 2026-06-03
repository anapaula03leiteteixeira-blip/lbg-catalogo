"""
La Bella Griffe — Relatório do Catálogo
Resumo por categoria, qualidade e lista de revisão.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Relatório | LBG", page_icon="📊", layout="wide")
st.title("📊 Relatório do Catálogo")

# ─── Dados ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load():
    p = Path(__file__).parent.parent / "catalog.json"
    if not p.exists():
        return pd.DataFrame(), {}
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    return pd.DataFrame(raw.get("produtos", [])), raw


df, raw = load()

if df.empty:
    st.warning("Catálogo vazio ou não encontrado.")
    st.stop()

# ─── KPIs ─────────────────────────────────────────────────────────────────────

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total de fotos",       len(df))
k2.metric("SKUs únicos",          df["sku"].nunique() if "sku" in df.columns else "—")
k3.metric("Categorias",           df["categoria"].nunique() if "categoria" in df.columns else "—")
k4.metric("Qualidade excelente",  int((df["qualidade_foto"] == "excelente").sum()) if "qualidade_foto" in df.columns else "—")
k5.metric("Para revisão",         int(df["precisa_revisao"].sum()) if "precisa_revisao" in df.columns else "—")

st.divider()

# ─── Gráficos ─────────────────────────────────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    st.subheader("Por Categoria")
    if "categoria" in df.columns:
        cat_df = df["categoria"].value_counts().rename_axis("Categoria").reset_index(name="Fotos")
        st.bar_chart(cat_df.set_index("Categoria"))
    else:
        st.info("Coluna 'categoria' não encontrada.")

with col2:
    st.subheader("Por Qualidade da Foto")
    if "qualidade_foto" in df.columns:
        order = ["excelente", "boa", "regular", "ruim"]
        qual_df = (
            df["qualidade_foto"]
            .value_counts()
            .reindex(order)
            .dropna()
            .rename_axis("Qualidade")
            .reset_index(name="Fotos")
        )
        st.bar_chart(qual_df.set_index("Qualidade"))
    else:
        st.info("Coluna 'qualidade_foto' não encontrada.")

# ─── Detalhe por categoria ────────────────────────────────────────────────────

st.subheader("Detalhamento por Categoria")
if "categoria" in df.columns and "qualidade_foto" in df.columns:
    pivot = (
        df.groupby(["categoria", "qualidade_foto"])
        .size()
        .unstack(fill_value=0)
    )
    # Reordena colunas
    cols_order = [c for c in ["excelente", "boa", "regular", "ruim"] if c in pivot.columns]
    pivot = pivot[cols_order]
    st.dataframe(pivot, use_container_width=True)

# ─── Ângulos mais fotografados ────────────────────────────────────────────────

st.subheader("Ângulos Mais Fotografados")
if "angulo" in df.columns:
    ang_df = df["angulo"].value_counts().rename_axis("Ângulo").reset_index(name="Fotos")
    st.bar_chart(ang_df.set_index("Ângulo"))

# ─── Produtos para revisão ────────────────────────────────────────────────────

st.divider()
st.subheader("⚠️ Produtos para Revisão Manual")

if "precisa_revisao" in df.columns:
    revisao_df = df[df["precisa_revisao"] == True].copy()
else:
    revisao_df = pd.DataFrame()

if revisao_df.empty:
    st.success("✅ Nenhum produto aguardando revisão!")
else:
    st.warning(f"{len(revisao_df)} foto(s) aguardando revisão.")
    show_cols = [c for c in ["sku", "nome_produto", "categoria", "qualidade_foto", "arquivo_novo"] if c in revisao_df.columns]
    st.dataframe(revisao_df[show_cols].rename(columns={
        "sku": "SKU", "nome_produto": "Nome", "categoria": "Categoria",
        "qualidade_foto": "Qualidade", "arquivo_novo": "Arquivo",
    }), use_container_width=True, hide_index=True)

    csv = revisao_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Exportar lista de revisão (CSV)", csv, "lbg-revisao.csv", "text/csv")

# ─── Top SKUs com mais fotos ─────────────────────────────────────────────────

st.divider()
st.subheader("Top 10 SKUs com mais fotos")
if "sku" in df.columns:
    top_skus = df["sku"].value_counts().head(10).rename_axis("SKU").reset_index(name="Fotos")
    st.bar_chart(top_skus.set_index("SKU"))
