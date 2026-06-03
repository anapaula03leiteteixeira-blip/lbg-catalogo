-- ══════════════════════════════════════════════════════════════
-- La Bella Griffe — Script de criação da tabela no Supabase
-- Execute este SQL no Supabase: Dashboard → SQL Editor → New Query
-- ══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS produtos (
    id                  BIGSERIAL PRIMARY KEY,
    sku                 TEXT NOT NULL,
    nome_produto        TEXT NOT NULL,
    categoria           TEXT,
    subcategoria        TEXT,
    cor_dominante       TEXT,
    angulo              TEXT,
    fundo               TEXT,
    qualidade_foto      TEXT,
    material_aparente   TEXT,
    tags                TEXT[],          -- array de strings
    problemas_foto      TEXT[],          -- array de strings
    descricao_marketing TEXT,
    descricao_tecnica   TEXT,
    precisa_revisao     BOOLEAN DEFAULT FALSE,
    image_url           TEXT,
    hash_sha256         TEXT,
    arquivo_original    TEXT,
    ref_encontrada      BOOLEAN DEFAULT FALSE,
    processado_em       TIMESTAMPTZ DEFAULT NOW(),
    criado_em           TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_produtos_sku       ON produtos(sku);
CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria);
CREATE INDEX IF NOT EXISTS idx_produtos_qualidade ON produtos(qualidade_foto);
CREATE INDEX IF NOT EXISTS idx_produtos_revisao   ON produtos(precisa_revisao);

-- Busca por texto em múltiplos campos (full-text search)
CREATE INDEX IF NOT EXISTS idx_produtos_fts ON produtos
    USING GIN (to_tsvector('portuguese',
        coalesce(sku, '') || ' ' ||
        coalesce(nome_produto, '') || ' ' ||
        coalesce(subcategoria, '') || ' ' ||
        coalesce(cor_dominante, '')
    ));

-- Permissão de leitura/escrita para o app (anon key)
ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir leitura publica"
    ON produtos FOR SELECT USING (true);

CREATE POLICY "Permitir insercao autenticada"
    ON produtos FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir atualizacao autenticada"
    ON produtos FOR UPDATE USING (true);

CREATE POLICY "Permitir exclusao autenticada"
    ON produtos FOR DELETE USING (true);
