"""Password-based per-draft encryption with AES-256-GCM and scrypt key derivation."""
import base64
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

DB_PATH = Path(os.environ.get("LEXIGUARD_DB", str(Path(__file__).resolve().parent.parent / "data" / "vault.db")))

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("""CREATE TABLE IF NOT EXISTS drafts
        (id TEXT PRIMARY KEY, payload BLOB NOT NULL, salt BLOB NOT NULL,
         nonce BLOB NOT NULL, created_at TEXT NOT NULL)""")
    return connection

def _key(passphrase: str, salt: bytes) -> bytes:
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(passphrase.encode("utf-8"))

def save(title: str, content: str, passphrase: str) -> dict:
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    draft_id = secrets.token_hex(12)
    payload = json.dumps({"title": title, "content": content}, ensure_ascii=False).encode("utf-8")
    ciphertext = AESGCM(_key(passphrase, salt)).encrypt(nonce, payload, draft_id.encode())
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        db.execute("INSERT INTO drafts VALUES (?, ?, ?, ?, ?)", (draft_id, ciphertext, salt, nonce, now))
    return {"id": draft_id, "created_at": now}

def list_drafts() -> list[dict]:
    with _connect() as db:
        rows = db.execute("SELECT id, created_at FROM drafts ORDER BY created_at DESC LIMIT 100").fetchall()
    return [{"id": row[0], "created_at": row[1]} for row in rows]

def load(draft_id: str, passphrase: str) -> dict | None:
    with _connect() as db:
        row = db.execute("SELECT payload,salt,nonce FROM drafts WHERE id=?", (draft_id,)).fetchone()
    if not row:
        return None
    try:
        raw = AESGCM(_key(passphrase, row[1])).decrypt(row[2], row[0], draft_id.encode())
    except (InvalidTag, ValueError) as exc:
        raise ValueError("Incorrect passphrase or damaged encrypted draft.") from exc
    return json.loads(raw.decode("utf-8"))

def remove(draft_id: str) -> bool:
    with _connect() as db:
        cursor = db.execute("DELETE FROM drafts WHERE id=?", (draft_id,))
    return cursor.rowcount > 0
