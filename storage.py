import json
import os
from pathlib import Path
from typing import Dict, List, Optional

def get_base_dir() -> Path:
    base_dir = Path.home() / ".preventivatore"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def get_customers_file() -> Path:
    return get_base_dir() / "customers.json"

def get_quotes_dir() -> Path:
    quotes_dir = get_base_dir() / "quotes"
    quotes_dir.mkdir(parents=True, exist_ok=True)
    return quotes_dir

def load_customers() -> Dict[str, Dict[str, str]]:
    """Carica l'anagrafica clienti dal file JSON."""
    file_path = get_customers_file()
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def save_customers_db(db: Dict[str, Dict[str, str]]) -> None:
    """Salva l'intero dizionario nel JSON."""
    with open(get_customers_file(), "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def save_customer(name: str, address: str, contact: str) -> None:
    """Aggiunge o aggiorna un cliente."""
    if not name or not name.strip():
        return
    name = name.strip()
    db = load_customers()

    # Se il cliente esiste già ma i nuovi dati sono vuoti, non sovrascrivere
    if name in db:
        if not address.strip(): address = db[name].get("address", "")
        if not contact.strip(): contact = db[name].get("contact", "")

    db[name] = {
        "address": address.strip(),
        "contact": contact.strip()
    }
    save_customers_db(db)

def get_customer(name: str) -> Optional[Dict[str, str]]:
    """Restituisce i dati di un cliente se esiste."""
    db = load_customers()
    return db.get(name.strip())

def save_local_quote(payload: dict, quote_number: str, customer_name: str) -> str:
    """Salva il preventivo nell'archivio locale. Restituisce il path."""
    import datetime
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = customer_name.replace(" ", "_").replace("/", "-")
    if not safe_name:
        safe_name = "SenzaNome"

    filename = f"{quote_number}_{safe_name}_{date_str}.pquote"
    filepath = get_quotes_dir() / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return str(filepath)

def list_local_quotes() -> List[Dict[str, str]]:
    """Lista i preventivi locali, ordinati dal più recente."""
    quotes_dir = get_quotes_dir()
    quotes = []

    for p in quotes_dir.glob("*.pquote"):
        try:
            stat = p.stat()
            quotes.append({
                "filename": p.name,
                "filepath": str(p),
                "mtime": stat.st_mtime,
                "size": stat.st_size
            })
        except OSError:
            pass

    # Ordina dal più recente
    quotes.sort(key=lambda x: x["mtime"], reverse=True)
    return quotes

def load_local_quote(filepath: str) -> Optional[dict]:
    """Carica un preventivo specifico."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
