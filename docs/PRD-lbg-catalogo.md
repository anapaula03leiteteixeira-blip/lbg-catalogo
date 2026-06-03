# PRD — La Bella Griffe: Sistema de Catálogo de Produtos

**Versão:** 2.0  
**Data:** 2026-06-03  
**Status:** Em produção  
**Owner:** Ana Paula Teixeira (anapaula03.leiteteixeira@gmail.com)

---

## 1. Visão Geral

Sistema web interno para **catalogar, consultar e gerenciar fotos de produtos hidráulicos** da La Bella Griffe (cubas, sanitários, flexíveis, rejunte, acessórios). Substitui o processo manual de organização de fotos em pastas e planilhas Excel.

---

## 2. Problema

- Fotos de produtos armazenadas em pastas locais desorganizadas (sem padrão de nomenclatura)
- Sem forma rápida de buscar um produto por SKU, cor ou categoria
- A Gabi (designer) e os funcionários não têm acesso centralizado às fotos
- Cadastro de novos produtos era manual, sem metadados estruturados
- Impossível saber a qualidade das fotos sem abrir uma a uma

---

## 3. Solução

Aplicativo web (Streamlit) com 3 páginas:

| Página | Funcionalidade |
|--------|---------------|
| 🛁 Catálogo | Galeria com filtros por categoria, qualidade, cor; busca por SKU/nome/tags |
| 📦 Novo Produto | Upload de foto → Claude Vision classifica → funcionário revisa → salva |
| ✏️ Editar Produto | Buscar produto existente, editar campos, excluir |
| 📊 Relatório | Métricas: total fotos, por categoria, por qualidade, lista de revisão |

---

## 4. Usuários

| Persona | Acesso | Uso principal |
|---------|--------|---------------|
| Gabi (designer) | Leitura | Buscar fotos por categoria/SKU para artes |
| Funcionários | Leitura + Upload | Cadastrar novos produtos quando chegam |
| Ana Paula (admin) | Full | Supervisão, revisão de produtos pendentes |

---

## 5. Stack Técnica

| Camada | Tecnologia | Plano | Custo |
|--------|-----------|-------|-------|
| Frontend/Backend | Streamlit | Community Cloud | Gratuito |
| Banco de dados | Supabase (PostgreSQL) | Free tier | Gratuito |
| Imagens (novas) | Cloudinary CDN | Free (25GB) | Gratuito |
| Imagens (existentes) | GitHub raw files | — | Gratuito |
| IA (classificação) | Claude Sonnet (Anthropic) | Pay-per-use | ~$0.02/foto |
| Repositório | GitHub | Public | Gratuito |

**URL do sistema:** (configurar após deploy no Streamlit Cloud)  
**Repositório:** https://github.com/anapaula03leiteteixeira-blip/lbg-catalogo

---

## 6. Arquitetura de Dados

### Tabela `produtos` (Supabase/PostgreSQL)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | BIGSERIAL PK | ID auto-incremento |
| sku | TEXT | Código do produto (ex: LBG100IPANEMA) |
| nome_produto | TEXT | Nome comercial padronizado |
| categoria | TEXT | cuba / sanitario / flexivel / rejunte / acessorio / outro |
| subcategoria | TEXT | Detalhe da categoria |
| cor_dominante | TEXT | Cor principal |
| angulo | TEXT | frontal / lateral / superior / perspectiva / detalhe / conjunto / embalagem |
| fundo | TEXT | branco / colorido / ambiente / transparente / outro |
| qualidade_foto | TEXT | excelente / boa / regular / ruim |
| material_aparente | TEXT | louca / aco_inox / plastico / ceramica / metal / outro |
| tags | TEXT[] | Array de palavras-chave para busca |
| problemas_foto | TEXT[] | Defeitos detectados pela IA |
| descricao_marketing | TEXT | Frase para catálogo (gerada por IA) |
| descricao_tecnica | TEXT | Especificações técnicas (gerada por IA) |
| precisa_revisao | BOOLEAN | Flag de revisão manual pendente |
| image_url | TEXT | URL pública da imagem (Cloudinary ou GitHub) |
| hash_sha256 | TEXT | Hash do arquivo para deduplicação |
| arquivo_original | TEXT | Nome original do arquivo |
| processado_em | TIMESTAMPTZ | Data/hora do processamento |
| criado_em | TIMESTAMPTZ | Data de inserção no banco |

### Segurança (RLS)
- Leitura: pública (qualquer pessoa com o link do app)
- Escrita: via anon key + RLS policies (permissão aberta para o app)

---

## 7. Fluxo de Cadastro de Novo Produto

```
Funcionário abre o app
  ↓
Faz upload da foto (JPG/PNG/WebP, máx 10MB)
  ↓
(Opcional) Informa SKU e categoria
  ↓
Clica "Classificar com IA"
  ↓
Claude Sonnet analisa a imagem via Vision API
  ↓
Campos preenchidos automaticamente:
  categoria, subcategoria, cor, ângulo, fundo,
  qualidade, material, tags, descrição marketing,
  descrição técnica
  ↓
Funcionário revisa e corrige se necessário
  ↓
Clica "Salvar"
  ↓
Imagem → Cloudinary (CDN, URL permanente)
Dados → Supabase (banco PostgreSQL)
  ↓
Produto aparece instantaneamente no catálogo
```

---

## 8. Catálogo Inicial

Processado em 03/06/2026 via script `organizer.py`:

| Métrica | Valor |
|---------|-------|
| Total de fotos catalogadas | 435 |
| SKUs únicos | ~85 |
| Com SKU identificado | 426 (98%) |
| Para revisão manual | 18 (4%) |
| Tamanho das imagens web | 13.4 MB |

**Categorias:** cuba, sanitario, rejunte, acessorio, outro, flexivel  
**Fonte:** `C:\Users\DELL\Pictures\Fotos_LBG\Fotos_Produtos_Organizadas\`

---

## 9. Ferramentas e Scripts

| Arquivo | Função |
|---------|--------|
| `organizer.py` | Classifica fotos em lote via Claude Vision, gera catalog.json |
| `compress_images.py` | Comprime fotos para web (173MB → 13MB) e atualiza URLs GitHub |
| `migrar_para_supabase.py` | Importa catalog.json para o Supabase (executado uma vez) |
| `supabase_schema.sql` | DDL da tabela produtos com índices e RLS |
| `app.py` | Streamlit: página principal do catálogo |
| `pages/1_📦_Novo_Produto.py` | Upload + IA + salvar no Supabase |
| `pages/2_✏️_Editar_Produto.py` | Editar e excluir produtos existentes |
| `pages/3_📊_Relatorio.py` | Métricas e relatório de revisão |

---

## 10. Configuração do Ambiente

### Variáveis de ambiente (Streamlit Secrets)

```toml
SUPABASE_URL       = "https://fjzcypjldbxkcumydyzp.supabase.co"
SUPABASE_KEY       = "eyJ..."   # anon public key
CLOUDINARY_CLOUD   = "dvlxblssx"
CLOUDINARY_API_KEY = "897626126694167"
CLOUDINARY_SECRET  = "***"      # não expor
ANTHROPIC_API_KEY  = "sk-ant-..." # renovar periodicamente
```

### IDs dos serviços
- Supabase Project ID: `fjzcypjldbxkcumydyzp`
- Cloudinary Cloud: `dvlxblssx`
- GitHub Repo: `anapaula03leiteteixeira-blip/lbg-catalogo`

---

## 11. Roadmap / Melhorias Futuras

| Prioridade | Feature | Esforço |
|-----------|---------|---------|
| Alta | Autenticação de usuários (login por email) | Médio |
| Alta | Upload de múltiplas fotos de uma vez | Baixo |
| Média | Associar todas as fotos de um SKU em uma página de detalhe | Médio |
| Média | Exportar seleção de fotos em ZIP | Médio |
| Baixa | App mobile (câmera direta para upload) | Alto |
| Baixa | Integração com planilha de referências (SKU oficial) | Médio |
| Baixa | Notificação por WhatsApp quando produto é cadastrado | Baixo |

---

## 12. Decisões Técnicas

| Decisão | Motivo |
|---------|--------|
| Streamlit em vez de React/Vue | Equipe sem dev frontend; Streamlit suficiente para uso interno |
| Supabase em vez de JSON file | Persistência real, edição de registros, escalabilidade |
| Cloudinary para novas fotos | CDN profissional, transformações automáticas (resize, WebP) |
| GitHub para fotos existentes | 435 fotos já estavam comprimidas e funcionando; migração desnecessária |
| Claude Sonnet (não Opus) | 5x mais barato com qualidade equivalente para classificação de imagens |
| Repo público no GitHub | Free tier Streamlit Cloud; dados não sensíveis |

---

*Documento gerado em 03/06/2026 — La Bella Griffe Catálogo v2.0*
