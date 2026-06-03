"""
La Bella Griffe — Catálogo de Produtos
Página principal: navegação e busca no catálogo.
"""

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

# ─── Config ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="La Bella Griffe | Catálogo",
    page_icon="🛁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #f8f9fa; }
    .metric-card { background: #fff; border: 1px solid #e9ecef; border-radius: 8px; padding: 12px; text-align: center; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
    .badge-excelente { background: #d4edda; color: #155724; }
    .badge-boa       { background: #cce5ff; color: #004085; }
    .badge-regular   { background: #fff3cd; color: #856404; }
    .badge-ruim      { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# ─── Carrega catálogo ─────────────────────────────────────────────────────────

CATALOG_FILE = Path(__file__).parent / "catalog.json"

@st.cache_data(ttl=120)
def load_catalog() -> pd.DataFrame:
    if not CATALOG_FILE.exists():
        return pd.DataFrame()
    with open(CATALOG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data.get("produtos", []))
    # Normaliza barras para rodar em qualquer OS
    if "arquivo_novo" in df.columns:
        df["arquivo_novo"] = df["arquivo_novo"].str.replace("\\", "/", regex=False)
    return df


df = load_catalog()

# ─── Cabeçalho ────────────────────────────────────────────────────────────────

col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("# 🛁")
with col_title:
    st.title("La Bella Griffe — Catálogo de Produtos")
    if not df.empty:
        st.caption(f"{len(df)} fotos catalogadas · {df['sku'].nunique() if 'sku' in df.columns else 0} produtos únicos")

st.divider()

if df.empty:
    st.warning(
        "**catalog.json não encontrado.**\n\n"
        "Copie o arquivo `catalog.json` gerado pelo `organizer.py` para a raiz deste repositório."
    )
    st.stop()

# ─── Sidebar — Filtros ────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔍 Filtros")

    search = st.text_input("Buscar", placeholder="SKU, nome, cor, tags...")

    categorias = sorted(df["categoria"].dropna().unique()) if "categoria" in df.columns else []
    cat_sel = st.multiselect("Categoria", categorias)

    qualidades_disponiveis = [q for q in ["excelente", "boa", "regular", "ruim"]
                               if q in (df["qualidade_foto"].unique() if "qualidade_foto" in df.columns else [])]
    qual_sel = st.multiselect("Qualidade da foto", qualidades_disponiveis)

    st.divider()
    revisao_only = st.checkbox("⚠️  Somente para revisão")

    st.divider()
    st.caption(f"📦 {len(df)} fotos | {df['sku'].nunique() if 'sku' in df.columns else '—'} SKUs")
    revisao_count = int(df["precisa_revisao"].sum()) if "precisa_revisao" in df.columns else 0
    st.caption(f"⚠️  {revisao_count} aguardando revisão")

# ─── Aplica filtros ───────────────────────────────────────────────────────────

filtered = df.copy()

if search:
    s = search.lower()
    cols_to_search = [c for c in ["sku", "nome_produto", "tags", "descricao_marketing", "subcategoria"] if c in filtered.columns]
    mask = pd.Series([False] * len(filtered), index=filtered.index)
    for c in cols_to_search:
        mask |= filtered[c].astype(str).str.lower().str.contains(s, na=False)
    filtered = filtered[mask]

if cat_sel:
    filtered = filtered[filtered["categoria"].isin(cat_sel)]

if qual_sel:
    filtered = filtered[filtered["qualidade_foto"].isin(qual_sel)]

if revisao_only and "precisa_revisao" in filtered.columns:
    filtered = filtered[filtered["precisa_revisao"] == True]

# Um produto por SKU (primeira foto encontrada)
if "sku" in filtered.columns:
    unique_products = filtered.sort_values("qualidade_foto", key=lambda s: s.map(
        {"excelente": 0, "boa": 1, "regular": 2, "ruim": 3}
    )).groupby("sku", as_index=False).first()
else:
    unique_products = filtered.copy()

# ─── Métricas rápidas ─────────────────────────────────────────────────────────

m1, m2, m3, m4 = st.columns(4)
m1.metric("Produtos encontrados", len(unique_products))
m2.metric("Fotos no filtro", len(filtered))
m3.metric("Categorias", filtered["categoria"].nunique() if "categoria" in filtered.columns else "—")
m4.metric("Para revisão", int(filtered["precisa_revisao"].sum()) if "precisa_revisao" in filtered.columns else "—")

st.divider()

if unique_products.empty:
    st.info("Nenhum produto encontrado com os filtros selecionados.")
    st.stop()

# ─── Seletor de visualização ──────────────────────────────────────────────────

view = st.radio("Visualizar como:", ["🖼️  Grade", "📋 Lista"], horizontal=True, label_visibility="collapsed")

QUAL_BADGE = {
    "excelente": ("🟢", "badge-excelente"),
    "boa":       ("🔵", "badge-boa"),
    "regular":   ("🟡", "badge-regular"),
    "ruim":      ("🔴", "badge-ruim"),
}

CAT_COLOR = {
    "cuba":      "1a6985", "sanitario": "4a4a8a",
    "rejunte":   "8a6a1a", "acessorio":  "1a8a4a",
    "flexivel":  "6a1a8a", "outro":      "6a6a6a",
}

# ─── Grade ────────────────────────────────────────────────────────────────────

if "Grade" in view:
    n_cols = 3
    for i in range(0, len(unique_products), n_cols):
        batch = unique_products.iloc[i:i + n_cols]
        cols = st.columns(n_cols)

        for col, (_, p) in zip(cols, batch.iterrows()):
            with col:
                sku        = str(p.get("sku", "—"))
                nome       = str(p.get("nome_produto", "—"))
                cat        = str(p.get("categoria", "outro"))
                qual       = str(p.get("qualidade_foto", "boa"))
                revisao    = bool(p.get("precisa_revisao", False))
                img_url    = str(p.get("image_url", "") or "")
                n_fotos    = int(len(filtered[filtered["sku"] == sku])) if "sku" in filtered.columns else 1

                # Imagem
                if img_url and img_url.startswith("http"):
                    st.image(img_url, use_container_width=True)
                else:
                    color   = CAT_COLOR.get(cat, "888888")
                    label   = re.sub(r"[^a-zA-Z0-9 ]", "", sku)[:15]
                    st.image(
                        f"https://via.placeholder.com/300x200/{color}/ffffff?text={label}",
                        use_container_width=True,
                    )

                qual_icon = QUAL_BADGE.get(qual, ("⚪", ""))[0]

                st.markdown(f"**{sku}**")
                st.caption(f"{nome[:60]}{'…' if len(nome) > 60 else ''}")
                st.caption(f"{cat} · {qual_icon} {qual} · 📸 {n_fotos}")
                if revisao:
                    st.caption("⚠️ Para revisão")

                with st.expander("Ver detalhes"):
                    for label, key in [
                        ("Subcategoria",  "subcategoria"),
                        ("Cor dominante", "cor_dominante"),
                        ("Ângulo",        "angulo"),
                        ("Fundo",         "fundo"),
                        ("Material",      "material_aparente"),
                    ]:
                        val = p.get(key, "—")
                        if val and val != "—":
                            st.write(f"**{label}:** {val}")

                    tags = p.get("tags", [])
                    if isinstance(tags, list) and tags:
                        st.write("**Tags:** " + ", ".join(str(t) for t in tags[:6]))

                    desc = p.get("descricao_marketing", "")
                    if desc:
                        st.divider()
                        st.write(f"*{desc}*")

# ─── Lista ────────────────────────────────────────────────────────────────────

else:
    show_cols = [c for c in
                 ["sku", "nome_produto", "categoria", "subcategoria", "cor_dominante",
                  "qualidade_foto", "precisa_revisao", "angulo"]
                 if c in unique_products.columns]
    col_labels = {
        "sku": "SKU", "nome_produto": "Nome", "categoria": "Categoria",
        "subcategoria": "Subcategoria", "cor_dominante": "Cor",
        "qualidade_foto": "Qualidade", "precisa_revisao": "Revisão", "angulo": "Ângulo",
    }
    st.dataframe(
        unique_products[show_cols].rename(columns=col_labels),
        use_container_width=True,
        hide_index=True,
    )

# ─── Exportar ─────────────────────────────────────────────────────────────────

st.divider()
c1, c2 = st.columns(2)
with c1:
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Exportar CSV filtrado", csv_bytes, "lbg-filtrado.csv", "text/csv")
with c2:
    if CATALOG_FILE.exists():
        st.download_button(
            "📥 Baixar catalog.json completo",
            CATALOG_FILE.read_bytes(),
            "catalog.json",
            "application/json",
        )
