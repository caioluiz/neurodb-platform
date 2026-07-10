"""
Passo 2 do pipeline: carregar no Postgres os metadados de UM arquivo EEG
(dataset -> subject -> session -> recording -> channels -> events).

Idempotente: se esse mesmo file_path já foi carregado antes, o script não
insere de novo, só avisa.

Uso:
    python 02_load_metadata.py caminho/para/S001R01.edf
    python 02_load_metadata.py caminho/para/S001R01.edf --dataset-name "Meu Dataset"
"""

import argparse
import sys
from pathlib import Path

from db_utils import load_file

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

    status, recording_id = load_file(
        args.file_path, args.dataset_name, args.source_url, args.license
    )

    if status == "loaded":
        print(f"✅ Carregado: recording_id={recording_id}")
    else:
        print(f"⏭️  Esse arquivo já estava carregado (recording_id={recording_id}) — nada foi alterado.")
