"""Invite-only waitlist: let people request access, and grant codes from
the admin console. Nothing here touches the console's own login: it simply
decides who is allowed past the gate.

Storage: <data_root>/waitlist.json — a small, file-backed registry.
"""

import json
import os
import secrets
import string
import threading
import time

import web

from common.log import logger
from config import get_data_root

# ─── constants ────────────────────────────────────────────────────────

WAITLIST_FILE = "waitlist.json"
CODE_PREFIX = "NOVA-"
CODE_LENGTH = 6  # length of the random part: NOVA-ABCDEF

_lock = threading.Lock()

STATUSES = {"waitlisted", "invited", "active"}


def _path() -> str:
    return os.path.join(get_data_root(), WAITLIST_FILE)


def _load() -> dict:
    path = _path()
    if not os.path.exists(path):
        return {"entries": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "entries" not in data:
            return {"entries": {}}
        return data
    except Exception as e:
        logger.warning(f"[Waitlist] unreadable store, starting fresh: {e}")
        return {"entries": {}}


def _save(data: dict) -> None:
    path = _path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _generate_code(entries: dict) -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = CODE_PREFIX + "".join(secrets.choice(alphabet) for _ in range(CODE_LENGTH))
        if not any(e.get("code") == code for e in entries.values()):
            return code


# ─── core actions ─────────────────────────────────────────────────────

def join_waitlist(email: str) -> tuple[str, str]:
    """Register an email on the waitlist.

    Returns (status, message). ``status`` is "ok" or "error".
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email or "." not in email.split("@", 1)[-1]:
        return "error", "อีเมลไม่ถูกต้อง"

    with _lock:
        data = _load()
        entries = data.setdefault("entries", {})
        if email in entries:
            entry = entries[email]
            if entry.get("status") == "invited":
                return "ok", f"คุณมี invite code แล้ว: {entry['code']} (ตรวจสอบอีเมลของคุณ)"
            if entry.get("status") == "active":
                return "ok", "บัญชีของคุณเปิดใช้งานแล้ว"
            return "ok", "คุณลงทะเบียนรอคิวไว้แล้ว — เราจะติดต่อกลับเมื่อมีที่ว่าง"
        entries[email] = {
            "email": email,
            "status": "waitlisted",
            "code": None,
            "created_at": _now(),
            "invited_at": None,
            "activated_at": None,
        }
        _save(data)
    logger.info(f"[Waitlist] new registration: {email}")
    return "ok", "ขอบคุณที่ลงทะเบียน! สลี่จะติดต่อกลับเมื่อพร้อม"


def get_entry(email: str) -> dict | None:
    email = (email or "").strip().lower()
    if not email:
        return None
    data = _load()
    return data.get("entries", {}).get(email)


def redeem_code(code: str, email: str) -> tuple[str, str]:
    """Validate and consume an invite code.

    On success, marks the entry "active" and returns ("ok", code_canonical).
    On failure, returns ("error", message).
    """
    canonical = (code or "").strip().upper()
    email = (email or "").strip().lower()

    if not canonical or not email:
        return "error", "กรุณากรอกอีเมลและ invite code"

    with _lock:
        data = _load()
        entries = data.setdefault("entries", {})
        entry = entries.get(email)

        # First: accept any valid code even before the email registers.
        match_email = None
        for addr, candidate in entries.items():
            if candidate.get("code") == canonical:
                match_email = addr
                break

        if match_email is None:
            return "error", "Invite code ไม่ถูกต้อง หรือหมดอายุแล้ว"

        candidate = entries[match_email]
        if candidate.get("status") not in ("invited", "waitlisted", "active"):
            return "error", "Invite code นี้ไม่สามารถใช้งานได้"

        if candidate.get("status") == "active":
            if match_email != email:
                return "error", "Invite code นี้ถูกใช้กับบัญชีอื่นไปแล้ว"
            return "ok", canonical

        # Activate.
        candidate["status"] = "active"
        candidate["activated_at"] = _now()
        if match_email != email and email not in entries:
            entries[email] = {
                "email": email,
                "status": "active",
                "code": canonical,
                "created_at": _now(),
                "invited_at": _now(),
                "activated_at": _now(),
            }
        _save(data)

    logger.info(f"[Waitlist] code redeemed: {canonical} -> {email}")
    return "ok", canonical


def list_entries() -> list:
    data = _load()
    rows = sorted(
        data.get("entries", {}).values(),
        key=lambda e: (e.get("activated_at") or e.get("invited_at") or e.get("created_at") or ""),
        reverse=True,
    )
    out = []
    for e in rows:
        out.append({
            "email": e.get("email", ""),
            "status": e.get("status", "unknown"),
            "code": e.get("code"),
            "created_at": e.get("created_at"),
            "invited_at": e.get("invited_at"),
            "activated_at": e.get("activated_at"),
        })
    return out


def grant_invite(email: str) -> tuple[str, str]:
    """Mark an email as invited and assign a fresh code (admin only)."""
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return "error", "อีเมลไม่ถูกต้อง"

    with _lock:
        data = _load()
        entries = data.setdefault("entries", {})
        entry = entries.get(email)
        if not entry:
            entries[email] = {
                "email": email,
                "status": "waitlisted",
                "code": None,
                "created_at": _now(),
                "invited_at": None,
                "activated_at": None,
            }
            entry = entries[email]
        if entry.get("status") == "active":
            return "ok", entry.get("code") or "บัญชีเปิดใช้งานอยู่แล้ว"
        if not entry.get("code"):
            entry["code"] = _generate_code(entries)
        entry["status"] = "invited"
        entry["invited_at"] = _now()
        _save(data)

    logger.info(f"[Waitlist] invite granted: {email} -> {entry['code']}")
    return "ok", entry["code"]


def revoke_access(email: str) -> tuple[str, str]:
    """Reset an entry back to waitlisted (removes active status, keeps the record)."""
    email = (email or "").strip().lower()
    if not email:
        return "error", "อีเมลไม่ถูกต้อง"

    with _lock:
        data = _load()
        entries = data.get("entries", {})
        entry = entries.get(email)
        if not entry:
            return "error", "ไม่พบอีเมลนี้ในรายการ"
        if entry.get("status") != "active":
            return "error", "บัญชียังไม่เปิดใช้งาน"
        entry["status"] = "invited"  # keep the code, just deactivate
        entry["activated_at"] = None
        _save(data)
    logger.info(f"[Waitlist] access revoked: {email}")
    return "ok", "เพิกถอนการเข้าถึงแล้ว"


# ─── HTTP handlers ────────────────────────────────────────────────────

class WaitlistJoinHandler:
    def POST(self):
        web.header("Content-Type", "application/json; charset=utf-8")
        try:
            data = json.loads(web.data())
        except Exception:
            return json.dumps({"status": "error", "message": "Invalid request"})
        status, message = join_waitlist(data.get("email"))
        return json.dumps({"status": status, "message": message})


class WaitlistRedeemHandler:
    def POST(self):
        web.header("Content-Type", "application/json; charset=utf-8")
        try:
            data = json.loads(web.data())
        except Exception:
            return json.dumps({"status": "error", "message": "Invalid request"})
        status, payload = redeem_code(data.get("code"), data.get("email"))
        if status == "ok":
            return json.dumps({"status": "ok", "code": payload})
        return json.dumps({"status": "error", "message": payload})


class WaitlistStatusHandler:
    def POST(self):
        web.header("Content-Type", "application/json; charset=utf-8")
        try:
            data = json.loads(web.data())
        except Exception:
            return json.dumps({"status": "error", "message": "Invalid request"})
        email = (data.get("email") or "").strip().lower()
        entry = get_entry(email)
        if not entry:
            return json.dumps({"status": "success", "registered": False})
        return json.dumps({
            "status": "success",
            "registered": True,
            "email": entry.get("email"),
            "status_value": entry.get("status"),
            "has_code": bool(entry.get("code")),
        })


class WaitlistAdminHandler:
    def GET(self):
        from channel.web.core._common import _require_auth
        _require_auth()
        web.header("Content-Type", "application/json; charset=utf-8")
        return json.dumps({"status": "success", "entries": list_entries()})

    def POST(self):
        from channel.web.core._common import _require_auth
        _require_auth()
        web.header("Content-Type", "application/json; charset=utf-8")
        try:
            data = json.loads(web.data())
        except Exception:
            return json.dumps({"status": "error", "message": "Invalid request"})
        action = (data.get("action") or "").strip()
        email = data.get("email")

        if action == "grant":
            status, payload = grant_invite(email)
        elif action == "revoke":
            status, payload = revoke_access(email)
        elif action == "delete":
            with _lock:
                d = _load()
                entries = d.setdefault("entries", {})
                if email in entries:
                    del entries[email]
                    _save(d)
                    logger.info(f"[Waitlist] entry deleted: {email}")
                    return json.dumps({"status": "ok", "message": "ลบรายการแล้ว"})
                return json.dumps({"status": "error", "message": "ไม่พบอีเมลนี้"})
        else:
            return json.dumps({"status": "error", "message": "Unknown action"})

        if status == "ok":
            return json.dumps({"status": "ok", "message": payload})
        return json.dumps({"status": "error", "message": payload})
