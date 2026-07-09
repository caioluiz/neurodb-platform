"""
Gera um arquivo EEG sintético (.fif) para você testar o pipeline
localmente ANTES de baixar dados reais do PhysioNet/OpenNeuro.

Isso existe porque, no ambiente onde eu (Claude) rodei e testei este
código, não há acesso à internet para baixar dados reais. No SEU
computador, com internet liberada, o passo natural depois de validar
o pipeline com este dado sintético é trocar por um arquivo .edf real
baixado do PhysioNet (veja o passo 6 nas instruções que te enviei).

Uso:
    python generate_sample_data.py
"""

import numpy as np
import mne
from pathlib import Path
from datetime import date

OUTPUT_DIR = Path(__file__).parent.parent / "sample_data"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_synthetic_eeg():
    # Canais seguindo o padrão internacional 10-20 (o mesmo usado em dados reais)
    ch_names = ["Fz", "Cz", "Pz", "C3", "C4", "P3", "P4", "O1", "O2", "F3"]
    ch_types = ["eeg"] * len(ch_names)
    sfreq = 256.0  # Hz — taxa de amostragem comum em EEG clínico
    duration_seconds = 60

    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    info.set_montage("standard_1020", on_missing="warn")

    # Sinal sintético: soma de ondas em faixas de frequência típicas do EEG
    # (delta, theta, alpha, beta) + ruído — só para termos algo plausível
    n_samples = int(duration_seconds * sfreq)
    t = np.arange(n_samples) / sfreq
    rng = np.random.default_rng(42)

    data = np.zeros((len(ch_names), n_samples))
    for i in range(len(ch_names)):
        alpha = 20e-6 * np.sin(2 * np.pi * 10 * t + rng.uniform(0, 2 * np.pi))
        beta = 8e-6 * np.sin(2 * np.pi * 20 * t + rng.uniform(0, 2 * np.pi))
        noise = rng.normal(0, 5e-6, n_samples)
        data[i] = alpha + beta + noise

    raw = mne.io.RawArray(data, info)

    # Metadados do "sujeito" (equivalente ao que viria no header de um EDF real)
    raw.info["subject_info"] = {
        "id": 1,
        "his_id": "sample_subject_001",
        "sex": 1,  # 1 = masculino, 2 = feminino, no padrão MNE
        "birthday": date(1995, 5, 20),
    }

    # Eventos simulados (ex: marcações de estímulo/tarefa)
    onsets = [5.0, 20.0, 35.0, 50.0]
    durations = [1.0, 1.0, 1.0, 1.0]
    descriptions = ["eyes_open", "eyes_closed", "eyes_open", "eyes_closed"]
    annotations = mne.Annotations(onset=onsets, duration=durations, description=descriptions)
    raw.set_annotations(annotations)

    out_path = OUTPUT_DIR / "sample_eeg_raw.fif"
    raw.save(out_path, overwrite=True)
    print(f"✅ Arquivo sintético gerado em: {out_path}")
    return out_path


if __name__ == "__main__":
    generate_synthetic_eeg()
