# La Bella Griffe — Catálogo de Produtos

Sistema online de catálogo e upload de fotos de produtos, construído com Streamlit.

## Funcionalidades

- **Catálogo**: grade ou lista com filtros por categoria, qualidade e busca livre
- **Novo Produto**: upload de foto → classificação automática por Claude Vision → salvar
- **Relatório**: métricas por categoria, qualidade, ângulo e lista de revisão

## Instalação local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configurar API Key

Crie o arquivo `.streamlit/secrets.toml` (já ignorado pelo .gitignore):

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

## Deploy no Streamlit Cloud

1. Crie um repositório público no GitHub e suba todos estes arquivos
2. Copie o `catalog.json` para a raiz do repositório
3. Acesse [share.streamlit.io](https://share.streamlit.io) → **New app**
4. Selecione o repositório e o arquivo `app.py`
5. Em **Advanced settings → Secrets**, adicione:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
6. Clique **Deploy**

## Como exibir fotos no catálogo online

As fotos ficam no seu Google Drive. Para exibi-las no sistema:

1. Abra a foto no Google Drive
2. Clique com botão direito → **Compartilhar** → **Qualquer pessoa com o link**
3. No campo "Acesso", selecione **Visualizador**
4. Copie o link. Exemplo: `https://drive.google.com/file/d/ABC123/view`
5. Extraia o ID: a parte `ABC123` entre `/d/` e `/view`
6. A URL pública fica: `https://drive.google.com/uc?id=ABC123`
7. Cole esta URL no campo **URL da imagem** ao cadastrar um novo produto

## Adicionar novos produtos

1. Acesse a página **📦 Novo Produto**
2. Faça upload da foto
3. Preencha o SKU e contexto (opcional — melhora a precisão da IA)
4. Clique **Classificar com IA**
5. Revise e edite os campos
6. Clique **Salvar no Catálogo**
7. Baixe o `catalog.json` atualizado e substitua no repositório GitHub
