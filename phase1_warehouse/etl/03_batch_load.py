"""
Passo 3 do pipeline: carregar TODOS os arquivos EEG de uma pasta (recursivo).

Percorre a pasta procurando arquivos com extensões conhecidas (.edf, .bdf,
.fif, .set, .vhdr), carrega cada um no Postgres, e no final imprime um
resumo. Arquivos já carregados antes (mesmo file_path na tabela recordings)
são pulados automaticamente — ou seja, é seguro rodar esse script de novo
sempre que você adicionar arquivos novos na pasta: ele não duplica o que já
foi processado. Se um arquivo específico der erro (corrompido, formato
inesperado, etc.), o script registra a falha e continua para o próximo —
não trava o lote inteiro por causa de um arquivo problemático.

Uso:
    python 03_batch_load.py caminho/para/pasta/com/arquivos
    python 03_batch_load.py caminho/para/pasta --dataset-name "Meu Dataset"
"""

import argparse
import sys
from pathlib import Path

from db_utils import load_file

EEG_EXTENSIONS = {".edf", ".bdf", ".fif", ".set", ".vhdr"}


def find_eeg_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in EEG_EXTENSIONS)


def batch_load(root: Path, dataset_name: str, source_url: str, license_: str) -> None:
    files = find_eeg_files(root)
    if not files:
        print(f"Nenhum arquivo EEG encontrado em {root}")
        print(f"(extensões aceitas: {', '.join(sorted(EEG_EXTENSIONS))})")
        return

    print(f"Encontrados {len(files)} arquivos. Iniciando carga...\n")

    loaded, skipped, failed = 0, 0, []

    for i, file_path in enumerate(files, start=1):
        print(f"[{i}/{len(files)}] {file_path.name} ... ", end="")
        try:
            status, recording_id = load_file(file_path, dataset_name, source_url, license_)
            if status == "loaded":
                print(f"✅ carregado (recording_id={recording_id})")
                loaded += 1
            else:
                print(f"⏭️  já existia (recording_id={recording_id})")
                skipped += 1
        except Exception as e:
            print(f"❌ falhou: {e}")
            failed.append((file_path.name, str(e)))

    print("\n" + "=" * 60)
    print("RESUMO DA CARGA EM LOTE")
    print("=" * 60)
    print(f"Carregados agora:      {loaded}")
    print(f"Já existiam (pulados): {skipped}")
    print(f"Falharam:              {len(failed)}")
    if failed:
        print("\nArquivos com erro:")
        for name, err in failed:
            print(f"  - {name}: {err}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carrega todos os arquivos EEG de uma pasta no Postgres")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--dataset-name", default="PhysioNet EEG Motor Movement/Imagery")
    parser.add_argument("--source-url", default="https://physionet.org/content/eegmmidb/1.0.0/")
    parser.add_argument("--license", default="ODC-BY 1.0")
    args = parser.parse_args()

    if not args.folder.exists() or not args.folder.is_dir():
        print(f"❌ Pasta não encontrada: {args.folder}")
        sys.exit(1)

    batch_load(args.folder, args.dataset_name, args.source_url, args.license)
