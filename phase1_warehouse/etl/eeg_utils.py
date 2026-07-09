"""
Funções compartilhadas entre os scripts do pipeline ETL (fase 1).

Fica num módulo à parte (sem prefixo numérico) porque nomes de arquivo
começando com dígito não podem ser importados como módulo Python
(ex: "import 01_read_eeg_metadata" é inválido). Os scripts numerados
(01_, 02_, ...) importam funções daqui.
"""

import re
from pathlib import Path

import mne


def read_eeg_metadata(file_path: Path, return_raw: bool = False):
    """
    Lê um arquivo EEG (qualquer formato suportado pelo MNE) e retorna
    um dicionário com os metadados. Se return_raw=True, também retorna
    o objeto `raw` do MNE (útil quando o próximo passo precisa dos dados
    de anotações completos, não só os labels).
    """
    raw = mne.io.read_raw(file_path, preload=False, verbose="ERROR")
    info = raw.info
    subject_info = info.get("subject_info") or {}

    metadata = {
        "file_path": str(file_path),
        "format": file_path.suffix.replace(".", ""),
        "sampling_rate_hz": float(info["sfreq"]),
        "num_channels": len(info["ch_names"]),
        "channel_names": info["ch_names"],
        "duration_seconds": float(round(raw.n_times / info["sfreq"], 2)),
        "num_samples": int(raw.n_times),
        "subject_id": subject_info.get("his_id", "desconhecido"),
        "subject_sex": subject_info.get("sex", "não informado"),
        "num_events": len(raw.annotations),
        "event_labels": sorted(set(raw.annotations.description)) if len(raw.annotations) else [],
    }

    if return_raw:
        return metadata, raw
    return metadata


def normalize_channel_name(name: str) -> str:
    """
    Remove sufixos/pontuação que alguns formatos (ex: os .edf do PhysioNet)
    adicionam aos nomes de canais. Ex: 'Fc5.' -> 'FC5', 'Cz..' -> 'CZ'

    Isso é exatamente o tipo de normalização que mencionamos no roadmap
    como um bom caso de uso pra IA quando os datasets ficam mais heterogêneos
    (aqui resolvemos com regex porque o padrão é simples e previsível).
    """
    return re.sub(r"\.+$", "", name).upper()


def parse_subject_and_run(file_path: Path) -> tuple[str, str]:
    """
    Extrai subject_code e run_code de arquivos no padrão do PhysioNet
    EEG Motor Movement/Imagery Dataset, ex: 'S001R01.edf' -> ('S001', 'R01')
    Se o arquivo não seguir esse padrão, retorna o nome do arquivo como
    subject_code e 'unknown' como run_code.
    """
    match = re.match(r"(S\d+)(R\d+)", file_path.stem)
    if not match:
        return file_path.stem, "unknown"
    return match.group(1), match.group(2)


# Mapeamento dos runs do PhysioNet EEG Motor Movement/Imagery Dataset,
# baseado na documentação oficial (physionet.org/content/eegmmidb).
# Cada sujeito tem 14 runs; os dois primeiros são baseline, os outros
# alternam entre execução real e imaginação motora.
PHYSIONET_MMI_RUN_TASKS = {
    "R01": "baseline_eyes_open",
    "R02": "baseline_eyes_closed",
    "R03": "motor_execution_fist_left_right",
    "R04": "motor_imagery_fist_left_right",
    "R05": "motor_execution_fists_feet",
    "R06": "motor_imagery_fists_feet",
    "R07": "motor_execution_fist_left_right",
    "R08": "motor_imagery_fist_left_right",
    "R09": "motor_execution_fists_feet",
    "R10": "motor_imagery_fists_feet",
    "R11": "motor_execution_fist_left_right",
    "R12": "motor_imagery_fist_left_right",
    "R13": "motor_execution_fists_feet",
    "R14": "motor_imagery_fists_feet",
}
