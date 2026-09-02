# neurodb-platform

Plataforma de dados para Neurociência (EEG): modelagem relacional + grafo, ETL e aplicação de LLMs sobre dados científicos reais.

# 🧠 Plataforma de Dados para Neurociência (EEG) — Roadmap do Projeto

**Objetivo do portfólio:** demonstrar domínio de modelagem de dados (relacional + grafo), engenharia de pipelines (ETL), e aplicação prática de LLMs sobre dados científicos reais.

**Formato:** projeto contínuo, dividido em 3 fases independentes. Cada fase já entrega algo funcional e apresentável sozinha — você não precisa esperar terminar tudo para ter algo bom no portfólio.

---

## Visão Geral das 3 Fases

| Fase | Nome | O que entrega | Foco técnico |
|---|---|---|---|
| 1 | Data Warehouse de EEG | Base de dados unificada com múltiplos datasets públicos de EEG | Modelagem relacional, séries temporais, ETL |
| 2 | Knowledge Graph de Neurociência | Grafo conectando biomarcadores, regiões cerebrais e condições, populado via LLM | Modelagem em grafo, extração de conhecimento com IA |
| 3 | Consulta em Linguagem Natural | Interface onde você pergunta em português/inglês e o sistema gera a query certa | LLM + Text-to-SQL/Cypher, RAG estruturado |

---

## Fase 1 — Data Warehouse de Sinais EEG (a fundação)

### Objetivo
Agregar datasets públicos de EEG (que vêm em formatos e estruturas diferentes) em um schema relacional único e consistente, seguindo como referência o padrão **EEG-BIDS** (o padrão que a comunidade científica usa para organizar dados de neuroimagem).

### Fontes de dados recomendadas (gratuitas e abertas)
- **PhysioNet** — datasets de EEG clínico e motor imagery, bem documentados
- **OpenNeuro** — repositório enorme já em formato BIDS, ótimo ponto de partida
- **TUH EEG Corpus** (Temple University) — o maior corpus clínico de EEG do mundo, bom para epilepsia

### Schema Relacional (proposta inicial)

```sql
-- Dataset de origem (proveniência dos dados)
CREATE TABLE datasets (
    dataset_id      SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    source_url      TEXT,
    license         VARCHAR(100),
    description     TEXT,
    imported_at     TIMESTAMP DEFAULT now()
);

-- Sujeitos de pesquisa
CREATE TABLE subjects (
    subject_id      SERIAL PRIMARY KEY,
    dataset_id      INTEGER REFERENCES datasets(dataset_id),
    external_code   VARCHAR(100),   -- ID original no dataset
    age             INTEGER,
    sex             VARCHAR(20),
    handedness      VARCHAR(20),
    notes           TEXT
);

-- Sessões de coleta
CREATE TABLE sessions (
    session_id      SERIAL PRIMARY KEY,
    subject_id      INTEGER REFERENCES subjects(subject_id),
    session_date    DATE,
    task            VARCHAR(255),   -- ex: 'motor_imagery', 'resting_state'
    condition       VARCHAR(255)
);

-- Gravações (um arquivo EEG bruto)
CREATE TABLE recordings (
    recording_id    SERIAL PRIMARY KEY,
    session_id      INTEGER REFERENCES sessions(session_id),
    file_path       TEXT NOT NULL,
    format          VARCHAR(20),    -- edf, bdf, set...
    sampling_rate   NUMERIC,
    duration_seconds NUMERIC,
    num_channels    INTEGER
);

-- Canais de eletrodo
CREATE TABLE channels (
    channel_id      SERIAL PRIMARY KEY,
    recording_id    INTEGER REFERENCES recordings(recording_id),
    label           VARCHAR(20),    -- ex: 'Fz', 'Cz', 'O1'
    position_x      NUMERIC,
    position_y      NUMERIC,
    position_z      NUMERIC,
    unit            VARCHAR(20)
);

-- Eventos/anotações dentro de uma gravação
CREATE TABLE events (
    event_id        SERIAL PRIMARY KEY,
    recording_id    INTEGER REFERENCES recordings(recording_id),
    onset_seconds   NUMERIC,
    duration_seconds NUMERIC,
    label           VARCHAR(255),
    description     TEXT
);

-- Features derivadas (calculadas depois, não o sinal bruto)
CREATE TABLE features (
    feature_id      SERIAL PRIMARY KEY,
    recording_id    INTEGER REFERENCES recordings(recording_id),
    channel_id      INTEGER REFERENCES channels(channel_id),
    feature_name    VARCHAR(100),   -- ex: 'alpha_power', 'spectral_entropy'
    frequency_band  VARCHAR(50),    -- ex: 'alpha (8-12Hz)'
    value           NUMERIC,
    computed_at     TIMESTAMP DEFAULT now()
);
```

> **Nota de design:** o sinal bruto (potencialmente gigabytes por gravação) fica em arquivo, não no banco — a tabela `recordings` só guarda o `file_path` e metadados. O banco é o "índice inteligente" sobre os arquivos, não um repositório de sinal bruto. Isso é uma decisão de arquitetura que vale a pena explicar no seu portfólio.

### Pipeline de ETL

1. **Extract:** baixar os arquivos EDF/BDF dos datasets escolhidos
2. **Parse:** usar **MNE-Python** (biblioteca padrão da neurociência computacional) para ler os arquivos e extrair metadados + estrutura de canais
3. **Transform:** normalizar nomenclatura de canais, unidades e labels de eventos entre datasets diferentes (aqui é onde um LLM pode ajudar — ver seção de IA abaixo)
4. **Load:** popular as tabelas acima via Python (psycopg2/SQLAlchemy)
5. **Feature engineering:** calcular métricas básicas (potência por banda de frequência, entropia espectral) e salvar em `features`

### Stack sugerida
| Componente | Ferramenta |
|---|---|
| Banco relacional | PostgreSQL + extensão TimescaleDB (opcional, se guardar séries temporais no banco depois) |
| Parsing de EEG | MNE-Python |
| Orquestração do ETL | Airflow ou Dagster (Dagster é mais simples pra projeto solo) |
| Transformações SQL | dbt (bom pra mostrar boas práticas de engenharia de dados) |

---

## Fase 2 — Knowledge Graph de Neurociência

### Objetivo
Construir um grafo de conhecimento conectando **biomarcadores de EEG**, **regiões cerebrais**, **condições clínicas** e **estudos científicos** — populado automaticamente via LLM lendo abstracts do PubMed.

### Schema do Grafo (Neo4j)

**Nós:**
- `(:BrainRegion {name, description})`
- `(:Biomarker {name, description})` — ex: "atividade alfa reduzida"
- `(:Condition {name, icd_code})` — ex: epilepsia, TDAH, Alzheimer
- `(:Study {pmid, title, year, doi})`
- `(:Author {name})`

**Relações:**
```cypher
(:Study)-[:MENTIONS]->(:Biomarker)
(:Biomarker)-[:LOCATED_IN]->(:BrainRegion)
(:Biomarker)-[:ASSOCIATED_WITH]->(:Condition)
(:Study)-[:STUDIES]->(:Condition)
(:Study)-[:AUTHORED_BY]->(:Author)
```

### Pipeline de extração com LLM
1. Buscar abstracts relevantes via **API do PubMed** (E-utilities, gratuita)
2. Para cada abstract, chamar a API da Claude com um prompt estruturado pedindo para extrair entidades e relações em JSON (biomarcadores, regiões, condições mencionadas e como se relacionam)
3. Validar/normalizar as entidades extraídas (evitar duplicatas tipo "hipocampo" vs "hippocampus")
4. Popular o grafo via driver do Neo4j em Python

Esse pipeline sozinho já é um baita projeto de portfólio: mostra extração de conhecimento estruturado a partir de texto não estruturado usando IA — uma habilidade muito procurada hoje.

### Ponte entre Fase 1 e Fase 2
A ligação natural: os `subjects` da Fase 1 podem ter uma `condition` que referencia o mesmo nó `(:Condition)` do grafo. Isso permite perguntas do tipo *"quais biomarcadores a literatura associa à condição que este sujeito tem?"* — cruzando dado experimental (Fase 1) com conhecimento da literatura (Fase 2).

---

## Fase 3 — Consulta em Linguagem Natural (RAG estruturado)

### Objetivo
Uma camada onde você (ou qualquer pesquisador) faz uma pergunta em linguagem natural, tipo:

> *"Mostre sujeitos entre 20 e 30 anos com atividade alfa dominante na tarefa de motor imagery"*

...e o sistema traduz isso automaticamente em uma query SQL real contra o seu banco da Fase 1, ou uma query Cypher contra o grafo da Fase 2, dependendo da pergunta.

### Arquitetura
1. Expor o **schema** do banco (não os dados) para o LLM via prompt/tool definition
2. LLM decide: a pergunta é sobre dados experimentais (→ SQL) ou sobre conhecimento científico (→ Cypher)?
3. LLM gera a query
4. Backend executa a query (com validação de segurança — nunca executar query gerada por LLM sem sanitização/allowlist)
5. Resultado volta formatado, opcionalmente com o LLM explicando o resultado em linguagem natural

### Stack
- Backend: **FastAPI**
- LLM: API da Claude com **tool use** (function calling) — você define as "ferramentas" como `query_sql` e `query_graph`
- Frontend simples de demonstração: **Streamlit** (rápido de montar, ótimo pra gravar um vídeo de demo pro portfólio)

```
---

## Recursos Úteis

- MNE-Python (documentação): https://mne.tools/
- Especificação EEG-BIDS: https://bids-specification.readthedocs.io/
- PhysioNet: https://physionet.org/
- OpenNeuro: https://openneuro.org/
- TUH EEG Corpus: https://isip.piconepress.com/projects/tuh_eeg/
