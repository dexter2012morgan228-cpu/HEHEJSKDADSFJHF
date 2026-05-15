from __future__ import annotations

import base64
import hmac
import hashlib
import os
import re
import secrets
import time
from typing import Iterable

INVITE_RE = re.compile(r"(discord\.gg|discord(?:app)?\.com/invite)/[\w-]+", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
MENTION_RE = re.compile(r"@(everyone|here)", re.IGNORECASE)

DEFAULT_BLACKLIST = (
    "nigger", "kike", "faggot",
    "cp ", "child porn", "loli",
    "free nitro", "nitro generator",
    "cheap rdp", "selling stolen",
)


def sanitize_text(value: str) -> str:
    if not value:
        return ""
    cleaned = MENTION_RE.sub(lambda m: f"@\u200b{m.group(1)}", value)
    cleaned = cleaned.replace("```", "''' ")
    return cleaned.strip()


def detect_blacklist(value: str, extra: Iterable[str] = ()) -> str | None:
    if not value:
        return None
    haystack = value.lower()
    for term in (*DEFAULT_BLACKLIST, *extra):
        if term and term.lower() in haystack:
            return term
    if INVITE_RE.search(value):
        return "external invite link"
    return None


def count_links(value: str) -> int:
    return len(URL_RE.findall(value or ""))


def short_id() -> str:
    raw = secrets.token_bytes(4)
    code = base64.b32encode(raw).decode("ascii").rstrip("=")
    return f"SBL-{code[:6]}"


def generate_access_key(secret: str, applicant_id: int, request_id: str) -> str:
    salt = secrets.token_bytes(8)
    payload = f"{applicant_id}:{request_id}:{int(time.time())}".encode()
    sig = hmac.new(
        (secret or "sublate-default").encode(),
        salt + payload,
        hashlib.sha256,
    ).digest()
    body = base64.urlsafe_b64encode(salt + sig[:18]).decode("ascii").rstrip("=")
    grouped = "-".join(body[i:i + 5] for i in range(0, len(body), 5))
    return f"SBLT-{grouped.upper()}"


def is_token_format_ok(token: str) -> bool:
    if not token:
        return False
    parts = token.split(".")
    return len(parts) == 3 and all(parts) and len(token) > 50


def mask_token(token: str) -> str:
    if not token:
        return "<empty>"
    if len(token) <= 12:
        return "***"
    return f"{token[:6]}…{token[-4:]}"


def env_is_committed_warning() -> str | None:
    cwd = os.getcwd()
    gitignore = os.path.join(cwd, ".gitignore")
    env_path = os.path.join(cwd, ".env")
    if not os.path.exists(env_path):
        return None
    if not os.path.exists(gitignore):
        return ".env exists but .gitignore is missing — risk of leaking the token."
    with open(gitignore, "r", encoding="utf-8", errors="ignore") as f:
        if ".env" not in f.read():
            return ".env is not listed in .gitignore — add it before committing."
    return None
