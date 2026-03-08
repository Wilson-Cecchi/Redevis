# history.py — Redevis
# Gerencia o histórico de scans anteriores.

import json
import os

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "data", "history.json")
MAX_HISTORY  = 10  # máximo de scans salvos


def load_history() -> list:
    """Carrega o histórico de scans."""
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_scan(scan: dict) -> None:
    """Salva um novo scan no histórico."""
    history = load_history()
    history.append(scan)

    # Mantém apenas os últimos MAX_HISTORY scans
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def get_last_scan() -> dict | None:
    """Retorna o scan mais recente do histórico."""
    history = load_history()
    if len(history) < 2:
        return None
    return history[-2]  # penúltimo (o último é o atual)


def compare_scans(current: dict, previous: dict) -> dict:
    """Compara dois scans e retorna dispositivos novos e removidos."""
    current_ips  = {d["ip"] for d in current["devices"]}
    previous_ips = {d["ip"] for d in previous["devices"]}

    new_devices     = [d for d in current["devices"]  if d["ip"] not in previous_ips]
    removed_devices = [d for d in previous["devices"] if d["ip"] not in current_ips]

    return {
        "new":     new_devices,
        "removed": removed_devices,
    }