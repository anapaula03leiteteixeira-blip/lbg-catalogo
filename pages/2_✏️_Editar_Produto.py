"""
La Bella Griffe — Editar Produto
Página para editar ou excluir produtos já cadastrados.
"""

import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Editar Produto | LBG", page_icon="✏️", layout="wide")

st.markdown("""
<style>
  .step-box {
      background: #f8fafc;
      border-left: 4px solid #f59e0b;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      margin-bottom: 16px;
  }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data(ttl=30)
def load_catalog():
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

def idx(lst, val, default=0):
    try:
        return lst.index(val)
    except ValueError:
        return default

CATEGORIAS = ["cuba", "sanitario", "flexivel", "rejunte", "acessorio", "outro"]
QUALIDADES = ["excelente", "boa", "regular", "ruim"]
ANGULOS    = ["frontal", "lateral", "superior", "perspectiva", "detalhe", "conjunto", "embalagem"]
FUNDOS     = ["branco", "colorido", "ambiente", "transparente", "outro"]
MATERIAIS  = ["louca", "aco_inox", "plastico", "ceramica", "metal", "borracha", "outro"]

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.title("✏️ Editar Produto")
st.markdown("Encontre o produto pelo SKU ou nome e edite as informações.")
st.divider()

df = load_catalog()
if df.empty:
    st.warning("Catálogo vazio. Nenhum produto para editar.")
    st.stop()

# ── Busca do produto ──────────────────────────────────────────────────────────
st.markdown('<div class="step-box"><b>① Encontre o produto</b></div>', unsafe_allow_html=True)

search_term = st.text_input("Buscar por SKU ou nome do produto", placeholder="ex: LBG100 ou Cuba Redonda")

if not search_term:
    st.info("Digite o SKU ou nome do produto que deseja editar.")
    st.stop()

mask = (
    df["sku"].astype(str).str.lower().str.contains(search_term.lower(), na=False)
    | df["nome_produto"].astype(str).str.lower().str.contains(search_term.lower(), na=False)
)
results = df[mask]

if results.empty:
    st.warning(f"Nenhum produto encontrado com '{search_term}'.")
    st.stop()

# Seleção do produto
opcoes = {
    f"{row['sku']} — {row['nome_produto']} ({row['categoria']})": row
    for _, row in results.iterrows()
}
escolha = st.selectbox("Selecione o produto para editar:", list(opcoes.keys()))
p = opcoes[escolha]

st.divider()
st.markdown('<div class="step-box"><b>② Edite os dados abaixo</b></div>', unsafe_allow_html=True)

# Exibir imagem atual
img_url = str(p.get("image_url", "") or "")
if img_url.startswith("http"):
    col_img, col_edit = st.columns([1, 3])
    with col_img:
        st.image(img_url, use_container_width=True)
        st.caption("Imagem atual")
else:
    col_edit = st.container()

with col_edit:
    col1, col2 = st.columns(2)
    with col1:
        sku      = st.text_input("SKU *",            value=str(p.get("sku", "")))
        nome     = st.text_input("Nome *",            value=str(p.get("nome_produto", "")))
        categoria= st.selectbox("Categoria *",        CATEGORIAS, index=idx(CATEGORIAS, p.get("categoria", "outro"), 5))
        subcateg = st.text_input("Subcategoria",      value=str(p.get("subcategoria", "") or ""))
        cor      = st.text_input("Cor dominante",     value=str(p.get("cor_dominante", "") or ""))
        material = st.selectbox("Material",           MATERIAIS, index=idx(MATERIAIS, p.get("material_aparente", "louca")))
    with col2:
        angulo   = st.selectbox("Ângulo",             ANGULOS, index=idx(ANGULOS, p.get("angulo", "frontal")))
        fundo    = st.selectbox("Fundo",              FUNDOS, index=idx(FUNDOS, p.get("fundo", "branco")))
        qualidade= st.selectbox("Qualidade da foto",  QUALIDADES, index=idx(QUALIDADES, p.get("qualidade_foto", "boa"), 1))
        url_img  = st.text_input("URL da imagem",     value=img_url)
        revisao  = st.checkbox("⚠️ Marcar para revisão", value=bool(p.get("precisa_revisao", False)))

tags_raw = p.get("tags", [])
if isinstance(tags_raw, list):
    tags_str_val = ", ".join(str(t) for t in tags_raw)
else:
    tags_str_val = str(tags_raw) if tags_raw else ""

tags_str = st.text_input("Tags (separe por vírgula)", value=tags_str_val)
desc_mkt = st.text_area("Descrição para o catálogo", value=str(p.get("descricao_marketing", "") or ""), height=70)
desc_tec = st.text_area("Descrição técnica",          value=str(p.get("descricao_tecnica", "") or ""),  height=70)

st.divider()

col_save, col_del = st.columns([3, 1])

# ── Salvar edição ─────────────────────────────────────────────────────────────
with col_save:
    if st.button("💾 Salvar alterações", type="primary", use_container_width=True):
        if not sku.strip():
            st.error("SKU obrigatório.")
            st.stop()
        if not nome.strip():
            st.error("Nome obrigatório.")
            st.stop()

        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
        updates = {
            "sku":               sku.strip(),
            "nome_produto":      nome.strip(),
            "categoria":         categoria,
            "subcategoria":      subcateg.strip(),
            "cor_dominante":     cor.strip(),
            "angulo":            angulo,
            "fundo":             fundo,
            "qualidade_foto":    qualidade,
            "material_aparente": material,
            "tags":              tags_list,
            "descricao_marketing": desc_mkt.strip(),
            "descricao_tecnica": desc_tec.strip(),
            "precisa_revisao":   revisao,
            "image_url":         url_img.strip(),
        }

        try:
            sb = get_supabase()
            produto_id = p.get("id")
            sb.table("produtos").update(updates).eq("id", produto_id).execute()
            st.cache_data.clear()
            st.success(f"✅ Produto **{sku}** atualizado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {e}")

# ── Excluir produto ───────────────────────────────────────────────────────────
with col_del:
    with st.expander("🗑️ Excluir produto"):
        st.warning("Esta ação não pode ser desfeita.")
        confirma = st.text_input("Digite o SKU para confirmar a exclusão:", placeholder=str(p.get("sku", "")))
        if st.button("Excluir permanentemente", type="secondary", use_container_width=True):
            if confirma.strip() == str(p.get("sku", "")).strip():
                try:
                    sb = get_supabase()
                    sb.table("produtos").delete().eq("id", p.get("id")).execute()
                    st.cache_data.clear()
                    st.success("Produto excluído.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("SKU digitado não confere. Exclusão cancelada.")
