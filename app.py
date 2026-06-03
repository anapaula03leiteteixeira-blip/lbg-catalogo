"""
La Bella Griffe — Catálogo de Produtos
Página principal: busca, filtros e visualização do catálogo.

Dependências externas:
  - Supabase  → banco de dados (substitui catalog.json)
  - Cloudinary → hospedagem de imagens (substitui GitHub)
  - Anthropic  → classificação automática com IA (Claude Vision)

Variáveis necessárias em .streamlit/secrets.toml:
  SUPABASE_URL       = "https://xxxx.supabase.co"
  SUPABASE_KEY       = "eyJ..."          # anon/public key
  CLOUDINARY_CLOUD   = "meu-cloud"
  CLOUDINARY_API_KEY = "123456"
  CLOUDINARY_SECRET  = "abc..."
  ANTHROPIC_API_KEY  = "sk-ant-..."
"""

import streamlit as st
import pandas as pd
from supabase import create_client

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="La Bella Griffe | Catálogo",
    page_icon="🛁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos visuais ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Fundo da sidebar */
  [data-testid="stSidebar"] { background: #f4f6f9; }

  /* Cards de produto na grade */
  .product-card {
      border: 1px solid #e8ecf0;
      border-radius: 12px;
      padding: 12px;
      margin-bottom: 8px;
      background: white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      transition: box-shadow 0.2s;
  }
  .product-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }

  /* Badges de qualidade */
  .badge {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
  }
  .badge-excelente { background:#d4edda; color:#155724; }
  .badge-boa       { background:#cce5ff; color:#004085; }
  .badge-regular   { background:#fff3cd; color:#856404; }
  .badge-ruim      { background:#f8d7da; color:#721c24; }

  /* Aviso de revisão */
  .revisao-tag {
      background: #fff3cd;
      color: #856404;
      border-radius: 6px;
      padding: 2px 8px;
      font-size: 11px;
  }

  /* Métricas mais destacadas */
  [data-testid="metric-container"] {
      background: white;
      border: 1px solid #e8ecf0;
      border-radius: 10px;
      padding: 12px 16px;
  }
</style>
""", unsafe_allow_html=True)

# ── Conexão Supabase ──────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=60, show_spinner="Carregando catálogo...")
def load_catalog() -> pd.DataFrame:
    """Busca todos os produtos do Supabase."""
    sb = get_supabase()
    # Busca em lotes de 1000 para não exceder o limite do Supabase
    all_rows = []
    offset = 0
    batch = 1000
    while True:
        resp = sb.table("produtos").select("*").range(offset, offset + batch - 1).execute()
        rows = resp.data or []
        all_rows.extend(rows)
        if len(rows) < batch:
            break
        offset += batch
    if not all_rows:
        return pd.DataFrame()
    return pd.DataFrame(all_rows)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("# 🛁")
with col_title:
    st.title("La Bella Griffe — Catálogo de Produtos")

df = load_catalog()

if not df.empty:
    n_fotos = len(df)
    n_skus  = df["sku"].nunique() if "sku" in df.columns else 0
    st.caption(f"📸 {n_fotos} fotos catalogadas · 📦 {n_skus} produtos únicos")

st.divider()

# ── Sidebar: filtros ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filtrar produtos")
    st.markdown("Use os campos abaixo para encontrar o que precisa.")

    search = st.text_input(
        "Buscar por nome, SKU ou tag",
        placeholder="ex: cuba branca, LBG100...",
    )

    categorias = (
        sorted(df["categoria"].dropna().unique())
        if "categoria" in df.columns else []
    )
    cat_sel = st.multiselect("Categoria", categorias)

    qualidades_disponiveis = [
        q for q in ["excelente", "boa", "regular", "ruim"]
        if "qualidade_foto" in df.columns and q in df["qualidade_foto"].unique()
    ]
    qual_sel = st.multiselect("Qualidade da foto", qualidades_disponiveis)

    st.divider()
    revisao_only = st.checkbox("⚠️ Mostrar só os que precisam de revisão")

    st.divider()
    n_revisao = int(df["precisa_revisao"].sum()) if "precisa_revisao" in df.columns else 0
    st.caption(f"📦 {len(df)} fotos  |  {df['sku'].nunique() if 'sku' in df.columns else '—'} SKUs")
    if n_revisao:
        st.warning(f"⚠️ {n_revisao} produto(s) aguardando revisão")

# ── Aviso se catálogo vazio ───────────────────────────────────────────────────
if df.empty:
    st.info(
        "**Catálogo vazio.**\n\n"
        "Acesse a página **📦 Novo Produto** para começar a cadastrar."
    )
    st.stop()

# ── Aplicar filtros ───────────────────────────────────────────────────────────
filtered = df.copy()

if search:
    s = search.lower()
    cols_busca = [c for c in ["sku", "nome_produto", "tags", "descricao_marketing", "subcategoria", "cor_dominante"] if c in filtered.columns]
    mask = pd.Series(False, index=filtered.index)
    for c in cols_busca:
        mask |= filtered[c].astype(str).str.lower().str.contains(s, na=False)
    filtered = filtered[mask]

if cat_sel:
    filtered = filtered[filtered["categoria"].isin(cat_sel)]
if qual_sel:
    filtered = filtered[filtered["qualidade_foto"].isin(qual_sel)]
if revisao_only and "precisa_revisao" in filtered.columns:
    filtered = filtered[filtered["precisa_revisao"] == True]

# Por produto: mostra a melhor foto de cada SKU
QUAL_ORDER = {"excelente": 0, "boa": 1, "regular": 2, "ruim": 3}
if "sku" in filtered.columns and "qualidade_foto" in filtered.columns:
    unique_products = (
        filtered
        .sort_values("qualidade_foto", key=lambda s: s.map(QUAL_ORDER).fillna(9))
        .groupby("sku", as_index=False)
        .first()
    )
else:
    unique_products = filtered.copy()

# ── Métricas rápidas ──────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Produtos encontrados",  len(unique_products))
m2.metric("Fotos no filtro",       len(filtered))
m3.metric("Categorias",            filtered["categoria"].nunique() if "categoria" in filtered.columns else "—")
m4.metric("Para revisão",          int(filtered["precisa_revisao"].sum()) if "precisa_revisao" in filtered.columns else "—")

st.divider()

if unique_products.empty:
    st.info("Nenhum produto encontrado com esses filtros. Tente outros termos.")
    st.stop()

# ── Seletor de visualização ───────────────────────────────────────────────────
view = st.radio(
    "Como deseja visualizar?",
    ["🖼️  Grade (fotos)", "📋 Lista (tabela)"],
    horizontal=True,
    label_visibility="collapsed",
)

QUAL_ICON = {"excelente": "🟢", "boa": "🔵", "regular": "🟡", "ruim": "🔴"}

# ── Visualização em Grade ─────────────────────────────────────────────────────
if "Grade" in view:
    n_cols = 3
    for i in range(0, len(unique_products), n_cols):
        batch = unique_products.iloc[i : i + n_cols]
        cols  = st.columns(n_cols)
        for col, (_, p) in zip(cols, batch.iterrows()):
            with col:
                sku     = str(p.get("sku", "—"))
                nome    = str(p.get("nome_produto", "—"))
                cat     = str(p.get("categoria", "—"))
                qual    = str(p.get("qualidade_foto", "boa"))
                revisao = bool(p.get("precisa_revisao", False))
                img_url = str(p.get("image_url", "") or "")
                n_fotos_sku = len(filtered[filtered["sku"] == sku]) if "sku" in filtered.columns else 1

                # Imagem do produto
                if img_url and img_url.startswith("http"):
                    # Cloudinary: insere transformação automática (400px, qualidade auto)
                    if "cloudinary.com" in img_url and "/upload/" in img_url:
                        img_display = img_url.replace("/upload/", "/upload/w_400,q_auto,f_auto/")
                    else:
                        img_display = img_url
                    st.image(img_display, use_container_width=True)
                else:
                    # Placeholder SVG interno (sem dependência externa)
                    st.markdown(
                        f"""<div style="background:#f0f4f8;border-radius:8px;
                        height:160px;display:flex;align-items:center;
                        justify-content:center;color:#94a3b8;font-size:13px;">
                        📷 Sem imagem</div>""",
                        unsafe_allow_html=True,
                    )

                # Informações do produto
                icon = QUAL_ICON.get(qual, "⚪")
                st.markdown(f"**{sku}**")
                st.caption(f"{nome[:55]}{'…' if len(nome) > 55 else ''}")
                st.caption(f"{cat} · {icon} {qual} · 📸 {n_fotos_sku} foto(s)")
                if revisao:
                    st.markdown('<span class="revisao-tag">⚠️ Precisa revisão</span>', unsafe_allow_html=True)

                with st.expander("Ver detalhes completos"):
                    for label_txt, key in [
                        ("Subcategoria",   "subcategoria"),
                        ("Cor dominante",  "cor_dominante"),
                        ("Ângulo",         "angulo"),
                        ("Fundo",          "fundo"),
                        ("Material",       "material_aparente"),
                    ]:
                        val = p.get(key, "")
                        if val and str(val) not in ("", "None", "nan"):
                            st.write(f"**{label_txt}:** {val}")

                    tags = p.get("tags", [])
                    if isinstance(tags, list) and tags:
                        st.write("**Tags:** " + ", ".join(str(t) for t in tags[:8]))

                    desc = p.get("descricao_marketing", "")
                    if desc and str(desc) not in ("", "None", "nan"):
                        st.divider()
                        st.write(f"*{desc}*")

                    # Botão de edição rápida (abre página de edição com SKU pré-preenchido)
                    st.page_link(
                        "pages/1_📦_Novo_Produto.py",
                        label="✏️ Editar este produto",
                        icon="✏️",
                    )

# ── Visualização em Lista ─────────────────────────────────────────────────────
else:
    show_cols = [c for c in [
        "sku", "nome_produto", "categoria", "subcategoria",
        "cor_dominante", "qualidade_foto", "precisa_revisao", "angulo"
    ] if c in unique_products.columns]

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

# ── Exportar dados ────────────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📥 Exportar dados")
csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "📥 Baixar lista filtrada (CSV)",
    csv_bytes,
    "lbg-catalogo.csv",
    "text/csv",
    help="Baixa todos os produtos visíveis com os filtros aplicados",
)
