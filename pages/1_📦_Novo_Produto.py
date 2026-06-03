"""
La Bella Griffe — Novo Produto
Upload de foto + classificação automática por Claude Vision.
"""

import base64
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Novo Produto | LBG",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Adicionar Novo Produto")
st.caption("Envie a foto e a IA classificará automaticamente. Revise e salve.")

# ─── API Key ──────────────────────────────────────────────────────────────────

api_key = ""
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except (KeyError, FileNotFoundError):
    pass

if not api_key:
    api_key = st.text_input(
        "🔑 Chave da API Anthropic",
        type="password",
        help="Configure em .streamlit/secrets.toml para não precisar digitar.",
    )
    if not api_key:
        st.warning("Insira a chave da API Anthropic para usar a classificação automática.")
        st.stop()

# ─── Upload da foto ───────────────────────────────────────────────────────────

st.subheader("1. Envie a foto do produto")

uploaded = st.file_uploader(
    "Selecione a foto",
    type=["jpg", "jpeg", "png", "webp"],
    help="JPG, PNG ou WebP. Máx. 50 MB.",
)

if not uploaded:
    st.info("Aguardando upload da foto do produto...")
    st.stop()

col_img, col_hint = st.columns([1, 2])
with col_img:
    st.image(uploaded, caption=uploaded.name, use_container_width=True)

with col_hint:
    st.subheader("2. Contexto opcional (melhora a precisão)")
    sku_hint   = st.text_input("SKU / Código", placeholder="ex: LBG100IPANEMA")
    cat_hint   = st.selectbox(
        "Categoria (se souber)",
        ["— automático —", "cuba", "sanitario", "flexivel", "rejunte", "acessorio", "outro"],
    )
    nome_hint  = st.text_input("Nome ou descrição", placeholder="ex: Cuba de Apoio Redonda Branca 35cm")
    image_url  = st.text_input(
        "URL pública da imagem (Google Drive / Cloudinary)",
        placeholder="https://drive.google.com/uc?id=...",
        help="Compartilhe a foto no Drive, obtenha o link direto e cole aqui para exibir no catálogo online.",
    )

# ─── Classificar ──────────────────────────────────────────────────────────────

st.subheader("3. Classificação automática")

if st.button("🤖 Classificar com IA", type="primary", use_container_width=True):
    with st.spinner("Claude Vision está analisando a foto..."):
        context_parts = []
        if sku_hint:
            context_parts.append(f"SKU informado: {sku_hint}")
        if cat_hint != "— automático —":
            context_parts.append(f"Categoria informada: {cat_hint}")
        if nome_hint:
            context_parts.append(f"Descrição informada: {nome_hint}")
        context = "\n".join(context_parts) if context_parts else "Nenhum contexto adicional."

        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        media_type = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp",
        }.get(ext, "image/jpeg")

        img_bytes = uploaded.getvalue()
        img_b64 = base64.standard_b64encode(img_bytes).decode()

        prompt = f"""Analise esta foto de produto hidráulico (cubas, sanitários, flexíveis, rejunte, acessórios).

CONTEXTO FORNECIDO:
{context}

Retorne APENAS um JSON válido (sem texto adicional):
{{
  "sku": "código do produto",
  "nome_produto": "nome completo padronizado",
  "categoria": "cuba|sanitario|flexivel|rejunte|acessorio|outro",
  "subcategoria": "subcategoria específica",
  "cores": ["lista", "de", "cores"],
  "cor_dominante": "cor principal",
  "angulo": "frontal|lateral|superior|perspectiva|detalhe|conjunto|embalagem",
  "fundo": "branco|colorido|ambiente|transparente|outro",
  "qualidade_foto": "excelente|boa|regular|ruim",
  "problemas_foto": [],
  "material_aparente": "louca|aco_inox|plastico|ceramica|metal|borracha|outro",
  "tags": ["lista", "de", "tags"],
  "descricao_marketing": "frase de 1-2 linhas para catálogo",
  "descricao_tecnica": "características técnicas visíveis",
  "precisa_revisao": false
}}

Se o SKU foi informado no contexto, use-o. Se não, tente identificar pela imagem."""

        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": img_b64},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
            text = resp.content[0].text.strip()
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text.strip())
            result = json.loads(text)

            # Aplica hints do usuário sobre o resultado da IA
            if sku_hint:
                result["sku"] = sku_hint
            if cat_hint != "— automático —":
                result["categoria"] = cat_hint

            st.session_state["classified"]  = result
            st.session_state["img_bytes"]   = img_bytes
            st.session_state["img_name"]    = uploaded.name
            st.session_state["image_url"]   = image_url

        except Exception as e:
            st.error(f"Erro na classificação: {e}")
            st.stop()

# ─── Formulário editável ──────────────────────────────────────────────────────

if "classified" not in st.session_state:
    st.stop()

r = st.session_state["classified"]
st.success("✅ Classificação concluída! Revise os campos abaixo e salve.")
st.divider()

st.subheader("4. Revise e edite")

CATEGORIAS    = ["cuba", "sanitario", "flexivel", "rejunte", "acessorio", "outro"]
QUALIDADES    = ["excelente", "boa", "regular", "ruim"]
ANGULOS       = ["frontal", "lateral", "superior", "perspectiva", "detalhe", "conjunto", "embalagem"]
FUNDOS        = ["branco", "colorido", "ambiente", "transparente", "outro"]
MATERIAIS     = ["louca", "aco_inox", "plastico", "ceramica", "metal", "borracha", "outro"]


def idx(lst, val, default=0):
    return lst.index(val) if val in lst else default


col1, col2 = st.columns(2)

with col1:
    sku        = st.text_input("SKU *", value=r.get("sku", ""))
    nome       = st.text_input("Nome do Produto *", value=r.get("nome_produto", ""))
    categoria  = st.selectbox("Categoria *", CATEGORIAS,      index=idx(CATEGORIAS, r.get("categoria", "outro"), 5))
    subcateg   = st.text_input("Subcategoria", value=r.get("subcategoria", ""))
    cor        = st.text_input("Cor Dominante", value=r.get("cor_dominante", ""))
    material   = st.selectbox("Material", MATERIAIS,          index=idx(MATERIAIS, r.get("material_aparente", "louca")))

with col2:
    angulo     = st.selectbox("Ângulo",    ANGULOS,           index=idx(ANGULOS, r.get("angulo", "frontal")))
    fundo      = st.selectbox("Fundo",     FUNDOS,            index=idx(FUNDOS, r.get("fundo", "branco")))
    qualidade  = st.selectbox("Qualidade da Foto", QUALIDADES, index=idx(QUALIDADES, r.get("qualidade_foto", "boa"), 1))
    url_final  = st.text_input("URL pública da imagem", value=st.session_state.get("image_url", ""))
    revisao    = st.checkbox("⚠️ Marcar para revisão manual", value=r.get("precisa_revisao", False))

tags_raw   = r.get("tags", [])
tags_str   = st.text_input(
    "Tags (separadas por vírgula)",
    value=", ".join(tags_raw) if isinstance(tags_raw, list) else str(tags_raw),
)
desc_mkt   = st.text_area("Descrição Marketing", value=r.get("descricao_marketing", ""), height=80)
desc_tec   = st.text_area("Descrição Técnica",   value=r.get("descricao_tecnica",   ""), height=80)

st.divider()

# ─── Salvar ───────────────────────────────────────────────────────────────────

if st.button("💾 Salvar no Catálogo", type="primary", use_container_width=True):
    if not sku.strip():
        st.error("O campo SKU é obrigatório.")
        st.stop()
    if not nome.strip():
        st.error("O campo Nome é obrigatório.")
        st.stop()

    img_bytes   = st.session_state.get("img_bytes", b"")
    img_name    = st.session_state.get("img_name", "produto.jpg")
    file_hash   = hashlib.sha256(img_bytes).hexdigest()
    ext_final   = img_name.rsplit(".", 1)[-1].lower()
    nome_pad    = f"{sku.strip()}-{categoria}-{angulo}.{ext_final}"
    tags_list   = [t.strip() for t in tags_str.split(",") if t.strip()]

    new_product = {
        "hash_sha256":       file_hash,
        "arquivo_original":  img_name,
        "arquivo_novo":      f"imagens/{categoria}/{nome_pad}",
        "nome_padronizado":  nome_pad,
        "precisa_revisao":   revisao,
        "processado_em":     datetime.now().isoformat(),
        "sku":               sku.strip(),
        "nome_produto":      nome.strip(),
        "categoria":         categoria,
        "subcategoria":      subcateg.strip(),
        "cores":             tags_list[:3],
        "cor_dominante":     cor.strip(),
        "angulo":            angulo,
        "fundo":             fundo,
        "qualidade_foto":    qualidade,
        "problemas_foto":    r.get("problemas_foto", []),
        "material_aparente": material,
        "tags":              tags_list,
        "descricao_marketing": desc_mkt.strip(),
        "descricao_tecnica":   desc_tec.strip(),
        "ref_encontrada":    False,
        "image_url":         url_final.strip(),
    }

    # Carrega catálogo existente
    catalog_path = Path(__file__).parent.parent / "catalog.json"
    if catalog_path.exists():
        with open(catalog_path, encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = {"versao": "1.0", "criado_em": datetime.now().isoformat(), "produtos": []}

    catalog["produtos"].append(new_product)
    catalog["total_produtos"] = len(catalog["produtos"])
    catalog["ultima_atualizacao"] = datetime.now().isoformat()

    updated_json = json.dumps(catalog, ensure_ascii=False, indent=2).encode("utf-8")

    st.success(f"✅ Produto **{sku}** ({nome}) adicionado ao catálogo!")

    st.download_button(
        "📥 Baixar catalog.json atualizado",
        updated_json,
        "catalog.json",
        "application/json",
        type="primary",
        use_container_width=True,
    )

    st.info(
        "**Como salvar permanentemente:**\n"
        "1. Baixe o `catalog.json` acima\n"
        "2. Substitua o arquivo no repositório GitHub\n"
        "3. O catálogo online atualiza automaticamente em até 2 minutos"
    )

    if not url_final:
        st.caption(
            "💡 **Dica:** Para exibir a foto no catálogo online, faça upload no Google Drive, "
            "compartilhe com 'Qualquer pessoa com o link' e cole a URL pública no campo 'URL da imagem'."
        )

    # Limpa estado
    for k in ["classified", "img_bytes", "img_name", "image_url"]:
        st.session_state.pop(k, None)
