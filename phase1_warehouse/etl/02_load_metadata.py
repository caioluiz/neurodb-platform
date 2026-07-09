"""
Passo 2 do pipeline: carregar no Postgres os metadados extraídos de um
arquivo EEG (dataset -> subject -> session -> recording -> channels -> events).

O script é idempotente para dataset e subject: rodar duas vezes com o
mesmo dataset/sujeito não cria duplicatas dessas duas tabelas (usa
get_or_create). Session/recording/channels/events são sempre criados
novos, porque cada arquivo processado é uma gravação nova.

Uso:
    python 02_load_metadata.py caminho/para/S001R01.edf
    python 02_load_metadata.py caminho/para/S001R01.edf --dataset-name "Meu Dataset"
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

from eeg_utils import (
    read_eeg_metadata,
    normalize_channel_name,
    parse_subject_and_run,
    PHYSIONET_MMI_RUN_TASKS,
)

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "dbname": os.getenv("POSTGRES_DB", "neurodb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "root"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_or_create_dataset(cur, name, source_url, license_):
    cur.execute("SELECT dataset_id FROM datasets WHERE name = %s", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO datasets (name, source_url, license) VALUES (%s, %s, %s) RETURNING dataset_id",
        (name, source_url, license_),
    )
    return cur.fetchone()[0]


def get_or_create_subject(cur, dataset_id, external_code):
    cur.execute(
        "SELECT subject_id FROM subjects WHERE dataset_id = %s AND external_code = %s",
        (dataset_id, external_code),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO subjects (dataset_id, external_code) VALUES (%s, %s) RETURNING subject_id",
        (dataset_id, external_code),
    )
    return cur.fetchone()[0]


def create_session(cur, subject_id, task):
    cur.execute(
        "INSERT INTO sessions (subject_id, task) VALUES (%s, %s) RETURNING session_id",
        (subject_id, task),
    )
    return cur.fetchone()[0]


def create_recording(cur, session_id, metadata):
    cur.execute(
        """
        INSERT INTO recordings (session_id, file_path, format, sampling_rate, duration_seconds, num_channels)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING recording_id
        """,
        (
            session_id,
            metadata["file_path"],
            metadata["format"],
            metadata["sampling_rate_hz"],
            metadata["duration_seconds"],
            metadata["num_channels"],
        ),
    )
    return cur.fetchone()[0]


def create_channels(cur, recording_id, channel_names):
    for raw_name in channel_names:
        clean_name = normalize_channel_name(raw_name)
        cur.execute(
            "INSERT INTO channels (recording_id, label) VALUES (%s, %s)",
            (recording_id, clean_name),
        )


def create_events(cur, recording_id, annotations):
    for onset, duration, description in zip(
        annotations.onset, annotations.duration, annotations.description
    ):
        cur.execute(
            "INSERT INTO events (recording_id, onset_seconds, duration_seconds, label) VALUES (%s, %s, %s, %s)",
            (recording_id, float(onset), float(duration), description),
        )


def load_file(file_path: Path, dataset_name: str, source_url: str, license_: str) -> int:
    metadata, raw = read_eeg_metadata(file_path, return_raw=True)
    subject_code, run_code = parse_subject_and_run(file_path)
    task = PHYSIONET_MMI_RUN_TASKS.get(run_code, run_code)

    conn = get_connection()
    try:
        with conn:  # commit automático se não der erro, rollback se der
            with conn.cursor() as cur:
                dataset_id = get_or_create_dataset(cur, dataset_name, source_url, license_)
                subject_id = get_or_create_subject(cur, dataset_id, subject_code)
                session_id = create_session(cur, subject_id, task)
                recording_id = create_recording(cur, session_id, metadata)
                create_channels(cur, recording_id, metadata["channel_names"])
                create_events(cur, recording_id, raw.annotations)

        print(
            f"✅ Carregado: dataset_id={dataset_id}, subject={subject_code} "
            f"(subject_id={subject_id}), task={task}, recording_id={recording_id}"
        )
        return recording_id
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carrega metadados de um arquivo EEG no Postgres")
    parser.add_argument("file_path", type=Path)
    parser.add_argument("--dataset-name", default="PhysioNet EEG Motor Movement/Imagery")
    parser.add_argument("--source-url", default="https://physionet.org/content/eegmmidb/1.0.0/")
    parser.add_argument("--license", default="ODC-BY 1.0")
    args = parser.parse_args()

    if not args.file_path.exists():
        print(f"❌ Arquivo não encontrado: {args.file_path}")
        sys.exit(1)

    load_file(args.file_path, args.dataset_name, args.source_url, args.license)
