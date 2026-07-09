"""
Passo 1 do pipeline: ler UM arquivo EEG e extrair seus metadados.

Suporta qualquer formato que o MNE reconheça (.fif, .edf, .bdf, .set, ...)
graças ao leitor genérico mne.io.read_raw(), que detecta o formato
automaticamente pela extensão do arquivo.

Uso:
    python 01_read_eeg_metadata.py caminho/para/arquivo.edf
    python 01_read_eeg_metadata.py                      # usa o sample_data por padrão
"""

import sys
from pathlib import Path

from eeg_utils import read_eeg_metadata

DEFAULT_FILE = Path(__file__).parent.parent / "sample_data" / "sample_eeg_raw.fif"


def print_metadata(metadata: dict) -> None:
    print("=" * 60)
    print("METADADOS DA GRAVAÇÃO EEG")
    print("=" * 60)
    print(f"Arquivo:            {metadata['file_path']}")
    print(f"Formato:            {metadata['format']}")
    print(f"Taxa de amostragem: {metadata['sampling_rate_hz']} Hz")
    print(f"Nº de canais:       {metadata['num_channels']}")
    print(f"Canais:             {', '.join(metadata['channel_names'])}")
    print(f"Duração:            {metadata['duration_seconds']} segundos")
    print(f"Nº de amostras:     {metadata['num_samples']}")
    print(f"Sujeito (ID):       {metadata['subject_id']}")
    print(f"Sujeito (sexo):     {metadata['subject_sex']}")
    print(f"Nº de eventos:      {metadata['num_events']}")
    print(f"Tipos de evento:    {', '.join(metadata['event_labels']) or '(nenhum)'}")
    print("=" * 60)
    print("\nPróximo passo no pipeline: usar esses metadados para popular")
    print("as tabelas 'datasets', 'subjects', 'sessions' e 'recordings'.")


if __name__ == "__main__":
    file_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE

    if not file_arg.exists():
        print(f"❌ Arquivo não encontrado: {file_arg}")
        print("   Rode primeiro: python generate_sample_data.py")
        sys.exit(1)

    metadata = read_eeg_metadata(file_arg)
    print_metadata(metadata)
