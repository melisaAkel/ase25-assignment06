# auth.py
import hashlib
import os
import time
import sqlite3
from datetime import datetime, timezone

ALLOWED_DOMAIN = "@uni-bayreuth.de"
CODE_TTL_SECONDS = 60  # cooldown for resend/register


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_allowed_email(email: str) -> bool:
    return isinstance(email, str) and email.endswith(ALLOWED_DOMAIN)


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _make_password_hash(password: str) -> str:
    salt = os.urandom(8).hex()
    digest = _hash_password(password, salt)
    return f"{salt}${digest}"


def _check_password(stored: str, password: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except Exception:
        return False
    return _hash_password(password, salt) == digest


def _generate_code() -> str:
    # 6 digits
    return str(int.from_bytes(os.urandom(3), "big") % 1000000).zfill(6)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _cooldown_seconds(row_last_sent_at: str) -> int:
    try:
        t = datetime.fromisoformat(row_last_sent_at.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - t).total_seconds()
        left = int(max(0, CODE_TTL_SECONDS - elapsed))
        return left
    except Exception:
        return 0


def start_registration(db: sqlite3.Connection, email: str, password: str):
    # user exists?
    u = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    if u:
        raise ValueError("USER_ALREADY_EXISTS")

    # check cooldown if pending exists
    pending = db.execute(
        "SELECT last_sent_at FROM email_verifications WHERE email = ?",
        (email,),
    ).fetchone()
    if pending:
        retry_in = _cooldown_seconds(pending["last_sent_at"])
        if retry_in > 0:
            return "", retry_in

    code = _generate_code()
    code_hash = _hash_code(code)
    password_hash = _make_password_hash(password)
    now = _now_iso()

    db.execute(
        """
        INSERT INTO email_verifications (email, code_hash, code_plain, password_hash, created_at, last_sent_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
          code_hash=excluded.code_hash,
          code_plain=excluded.code_plain,
          password_hash=excluded.password_hash,
          created_at=excluded.created_at,
          last_sent_at=excluded.last_sent_at
        """,
        (email, code_hash, code, password_hash, now, now),
    )
    db.commit()
    return code, CODE_TTL_SECONDS


def resend_code(db: sqlite3.Connection, email: str):
    # user exists?
    u = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    if u:
        raise ValueError("USER_ALREADY_EXISTS")

    pending = db.execute(
        "SELECT last_sent_at FROM email_verifications WHERE email = ?",
        (email,),
    ).fetchone()
    if not pending:
        raise ValueError("NO_PENDING_REGISTRATION")

    retry_in = _cooldown_seconds(pending["last_sent_at"])
    if retry_in > 0:
        return "", retry_in

    code = _generate_code()
    code_hash = _hash_code(code)
    now = _now_iso()

    db.execute(
        """
        UPDATE email_verifications
        SET code_hash = ?, code_plain = ?, last_sent_at = ?
        WHERE email = ?
        """,
        (code_hash, code, now, email),
    )
    db.commit()
    return code, CODE_TTL_SECONDS


def verify_code_and_create_user(db: sqlite3.Connection, email: str, code: str) -> bool:
    row = db.execute(
        "SELECT email, code_hash, password_hash FROM email_verifications WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        return False

    if _hash_code(code) != row["code_hash"]:
        return False

    now = _now_iso()
    db.execute(
        """
        INSERT INTO users (email, password_hash, role, created_at)
        VALUES (?, ?, 'student', ?)
        """,
        (email, row["password_hash"], now),
    )
    db.execute("DELETE FROM email_verifications WHERE email = ?", (email,))
    db.commit()
    return True

def hash_password(password: str) -> str:
    """
    Public helper to create a stored password hash in the same format as login() expects.
    Returns: "salt$digest"
    """
    return _make_password_hash(password)


def login(db: sqlite3.Connection, email: str, password: str):
    row = db.execute(
        "SELECT password_hash, role FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if not row:
        return False, ""

    if not _check_password(row["password_hash"], password):
        return False, ""

    return True, row["role"]
