"""
La Bella Griffe — Adicionar Novo Produto
Upload de imagem → Cloudinary, classificação IA → Claude Vision, salva → Supabase.
"""

import base64
import hashlib
import json
import re
from datetime import datetime

import cloudinary
import cloudinary.uploader
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Novo Produto | LBG", page_icon="📦", layout="wide")

st.markdown("""
<style>
  .step-box {
      background: #f8fafc;
      border-left: 4px solid #3b82f6;
      padding: 12px 16px;
      border-radius: 0 8px 8px 0;
      margin-bottom: 16px;
  }
  .step-number { font-size: 22px; font-weight: 800; color: #3b82f6; }
  .success-box {
      background: #f0fdf4;
      border: 1px solid #86efac;
      border-radius: 10px;
      padding: 16px;
  }
</style>
""", unsafe_allow_html=True)

# ── Configurar Cloudinary ─────────────────────────────────────────────────────
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD"],
    api_key    = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_SECRET"],
    secure     = True,
)

# ── Conexão Supabase ──────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

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
st.title("📦 Cadastrar Novo Produto")
st.markdown(
    "Envie a foto, preencha as informações básicas e a **IA classifica automaticamente**. "
    "Você só precisa revisar e confirmar. Simples assim! 👇"
)
st.divider()

# ── PASSO 1: Upload ───────────────────────────────────────────────────────────
st.markdown('<div class="step-box"><span class="step-number">① </span> <b>Envie a foto do produto</b><br><small>Formatos aceitos: JPG, PNG, WEBP · Máximo 10MB por foto</small></div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Clique aqui ou arraste a foto para esta área",
    type=["jpg", "jpeg", "png", "webp"],
)

if not uploaded:
    st.info("👆 Aguardando a foto do produto para continuar...")
    st.stop()

img_bytes = uploaded.getvalue()
if len(img_bytes) > 10 * 1024 * 1024:
    st.error("⚠️ Arquivo muito grande. O limite é 10MB.")
    st.stop()

col_img, col_form = st.columns([1, 2])
with col_img:
    st.image(uploaded, caption=f"📷 {uploaded.name}", use_container_width=True)
    st.caption(f"Tamanho: {len(img_bytes)/1024:.0f} KB")

# ── PASSO 2: Contexto ─────────────────────────────────────────────────────────
with col_form:
    st.markdown('<div class="step-box"><span class="step-number">② </span> <b>Dê uma dica para a IA (opcional)</b><br><small>Quanto mais você informar, mais precisa será a classificação</small></div>', unsafe_allow_html=True)
    sku_hint  = st.text_input("Código / SKU do produto", placeholder="ex: LBG100IPANEMA")
    cat_hint  = st.selectbox("Categoria", ["— deixar a IA decidir —"] + CATEGORIAS)
    nome_hint = st.text_input("Nome ou descrição", placeholder="ex: Cuba de Apoio Redonda Branca")

# ── PASSO 3: Classificar ──────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="step-box"><span class="step-number">③ </span> <b>Classificar com Inteligência Artificial</b><br><small>A IA analisa a foto e preenche todos os campos automaticamente</small></div>', unsafe_allow_html=True)

if st.button("🤖  Analisar foto com IA", type="primary", use_container_width=True):
    with st.spinner("🔍 Claude Vision analisando a imagem..."):
        context_parts = []
        if sku_hint:  context_parts.append(f"SKU: {sku_hint}")
        if cat_hint != "— deixar a IA decidir —": context_parts.append(f"Categoria: {cat_hint}")
        if nome_hint: context_parts.append(f"Descrição: {nome_hint}")
        context = "\n".join(context_parts) or "Nenhum contexto adicional."

        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        img_b64 = base64.standard_b64encode(img_bytes).decode()

        prompt = f"""Você é especialista em produtos hidráulicos e de banheiro.
Analise a foto e retorne APENAS um JSON válido, sem texto adicional.

CONTEXTO DO USUÁRIO:
{context}

{{
  "sku": "código (use o fornecido, senão inferir ou deixar vazio)",
  "nome_produto": "nome comercial completo",
  "categoria": "cuba|sanitario|flexivel|rejunte|acessorio|outro",
  "subcategoria": "subcategoria específica",
  "cor_dominante": "cor principal",
  "angulo": "frontal|lateral|superior|perspectiva|detalhe|conjunto|embalagem",
  "fundo": "branco|colorido|ambiente|transparente|outro",
  "qualidade_foto": "excelente|boa|regular|ruim",
  "problemas_foto": ["problemas encontrados ou lista vazia"],
  "material_aparente": "louca|aco_inox|plastico|ceramica|metal|borracha|outro",
  "tags": ["palavras-chave para busca"],
  "descricao_marketing": "frase atrativa para catálogo (máx 120 chars)",
  "descricao_tecnica": "descrição técnica objetiva",
  "precisa_revisao": false
}}"""

        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                    {"type": "text", "text": prompt},
                ]}],
            )
            raw = re.sub(r"^```(?:json)?\s*", "", resp.content[0].text.strip())
            raw = re.sub(r"\s*```$", "", raw.strip())
            result = json.loads(raw)

            if sku_hint: result["sku"] = sku_hint
            if cat_hint != "— deixar a IA decidir —": result["categoria"] = cat_hint

            st.session_state["classified"] = result
            st.session_state["img_bytes"]  = img_bytes
            st.session_state["img_name"]   = uploaded.name
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro na classificação: {e}")
            st.stop()

if "classified" not in st.session_state:
    st.stop()

# ── PASSO 4: Revisar ──────────────────────────────────────────────────────────
r = st.session_state["classified"]
st.success("✅ A IA classificou o produto! Confira abaixo e corrija se necessário.")
st.divider()
st.markdown('<div class="step-box"><span class="step-number">④ </span> <b>Revise e corrija os dados</b><br><small>Campos com * são obrigatórios</small></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    sku      = st.text_input("SKU / Código *", value=r.get("sku", ""))
    nome     = st.text_input("Nome do produto *", value=r.get("nome_produto", ""))
    categoria= st.selectbox("Categoria *", CATEGORIAS, index=idx(CATEGORIAS, r.get("categoria", "outro"), 5))
    subcateg = st.text_input("Subcategoria", value=r.get("subcategoria", ""))
    cor      = st.text_input("Cor dominante", value=r.get("cor_dominante", ""))
    material = st.selectbox("Material", MATERIAIS, index=idx(MATERIAIS, r.get("material_aparente", "louca")))

with col2:
    angulo   = st.selectbox("Ângulo da foto", ANGULOS, index=idx(ANGULOS, r.get("angulo", "frontal")))
    fundo    = st.selectbox("Fundo da foto", FUNDOS, index=idx(FUNDOS, r.get("fundo", "branco")))
    qualidade= st.selectbox("Qualidade da foto", QUALIDADES, index=idx(QUALIDADES, r.get("qualidade_foto", "boa"), 1))
    revisao  = st.checkbox("⚠️ Marcar para revisão posterior", value=r.get("precisa_revisao", False))
    problemas = r.get("problemas_foto", [])
    if problemas:
        st.warning("**Problemas na foto:**\n" + "\n".join(f"- {p}" for p in problemas))

tags_raw = r.get("tags", [])
tags_str = st.text_input("Tags / palavras-chave (vírgula)", value=", ".join(tags_raw) if isinstance(tags_raw, list) else "")
desc_mkt = st.text_area("Descrição para o catálogo", value=r.get("descricao_marketing", ""), height=80)
desc_tec = st.text_area("Descrição técnica", value=r.get("descricao_tecnica", ""), height=80)

# ── PASSO 5: Salvar ───────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="step-box"><span class="step-number">⑤ </span> <b>Salvar no catálogo</b><br><small>A foto vai para a nuvem e os dados são salvos automaticamente</small></div>', unsafe_allow_html=True)

if st.button("💾  Salvar produto no catálogo", type="primary", use_container_width=True):
    if not sku.strip(): st.error("⚠️ SKU obrigatório."); st.stop()
    if not nome.strip(): st.error("⚠️ Nome obrigatório."); st.stop()

    # Upload para Cloudinary
    with st.spinner("📤 Enviando imagem para a nuvem..."):
        try:
            img_bytes_save = st.session_state.get("img_bytes", b"")
            img_name_save  = st.session_state.get("img_name", "produto.jpg")
            public_id = f"lbg/{categoria}/{sku.strip()}-{angulo}"
            upload_resp = cloudinary.uploader.upload(
                img_bytes_save,
                public_id=public_id, overwrite=True,
                resource_type="image", quality="auto", fetch_format="auto",
            )
            image_url = upload_resp["secure_url"]
            file_hash = hashlib.sha256(img_bytes_save).hexdigest()
        except Exception as e:
            st.error(f"❌ Erro ao enviar imagem: {e}")
            st.stop()

    # Salvar no Supabase
    with st.spinner("💾 Salvando no banco de dados..."):
        tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]
        new_product = {
            "sku": sku.strip(), "nome_produto": nome.strip(),
            "categoria": categoria, "subcategoria": subcateg.strip(),
            "cor_dominante": cor.strip(), "angulo": angulo, "fundo": fundo,
            "qualidade_foto": qualidade, "material_aparente": material,
            "tags": tags_list, "descricao_marketing": desc_mkt.strip(),
            "descricao_tecnica": desc_tec.strip(),
            "problemas_foto": r.get("problemas_foto", []),
            "precisa_revisao": revisao, "image_url": image_url,
            "hash_sha256": file_hash, "arquivo_original": img_name_save,
            "processado_em": datetime.now().isoformat(), "ref_encontrada": False,
        }
        try:
            get_supabase().table("produtos").insert(new_product).execute()
        except Exception as e:
            st.error(f"❌ Erro ao salvar: {e}"); st.stop()

    st.balloons()
    st.markdown(f"""<div class="success-box">
        <h3>✅ Produto salvo com sucesso!</h3>
        <b>SKU:</b> {sku.strip()}<br>
        <b>Nome:</b> {nome.strip()}<br>
        <b>Categoria:</b> {categoria}<br>
        <b>Imagem:</b> <a href="{image_url}" target="_blank">Ver na nuvem ↗</a>
    </div>""", unsafe_allow_html=True)

    for k in ["classified", "img_bytes", "img_name"]:
        st.session_state.pop(k, None)
    st.info("👆 Para cadastrar outro produto, faça o upload de uma nova foto acima.")
