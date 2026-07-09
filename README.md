# neurodb-platform

Plataforma de dados para Neurociência (EEG): modelagem relacional + grafo, ETL e aplicação de LLMs sobre dados científicos reais.

Veja `roadmap-bd-neurociencia.md` para o plano completo do projeto (as 3 fases).

## Setup rápido (Fase 1)

```bash
# 1. Suba o Postgres + pgAdmin
docker compose up -d

# 2. Crie um ambiente virtual Python e instale as dependências
python3 -m venv venv
source venv/bin/activate        # no Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Gere um arquivo EEG sintético para testar o pipeline
cd phase1_warehouse/etl
python generate_sample_data.py

# 4. Leia os metadados desse arquivo
python 01_read_eeg_metadata.py
```

O schema SQL (`phase1_warehouse/schema/schema.sql`) já roda automaticamente na
primeira vez que o container do Postgres sobe, graças ao volume configurado
no `docker-compose.yml`.

## Acessando o banco

- Via terminal: `docker exec -it neurodb_postgres psql -U neurodb -d neurodb`
- Via navegador (pgAdmin): http://localhost:5050 (login: admin@neurodb.local / admin)

## Próximo passo real

Troque o dado sintético por um arquivo `.edf` real baixado do PhysioNet e
rode `01_read_eeg_metadata.py caminho/para/arquivo.edf` para confirmar que
funciona com dado de verdade.
