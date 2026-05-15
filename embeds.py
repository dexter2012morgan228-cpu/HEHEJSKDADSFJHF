from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import discord

from .config import (
    BRAND_FOOTER,
    BRAND_ICON,
    BRAND_NAME,
    COLOR_ACCEPT,
    COLOR_DECLINE,
    COLOR_INFO,
    COLOR_PENDING,
    COLOR_PRIMARY,
    COLOR_WARN,
)
from .localization import t
from .security import sanitize_text

DIVIDER = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
SOFT_DIVIDER = "──────────────────────────"


def _base(title: str, description: str | None, color: int) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=BRAND_FOOTER, icon_url=BRAND_ICON)
    return embed


def info_embed(title: str, description: str, color: int = COLOR_INFO) -> discord.Embed:
    return _base(title, description, color)


def warn_embed(title: str, description: str) -> discord.Embed:
    return _base(title, description, COLOR_WARN)


def error_embed(title: str, description: str) -> discord.Embed:
    return _base(title, description, COLOR_DECLINE)


def success_embed(title: str, description: str) -> discord.Embed:
    return _base(title, description, COLOR_ACCEPT)


def _status_block(status_key: str, locale: str | None) -> tuple[str, int, str]:
    mapping = {
        "PENDING":   (COLOR_PENDING, "○"),
        "ACCEPTED":  (COLOR_ACCEPT,  "●"),
        "DECLINED":  (COLOR_DECLINE, "✕"),
        "WITHDRAWN": (COLOR_PENDING, "↺"),
    }
    color, dot = mapping.get(status_key, (COLOR_PRIMARY, "○"))
    label = t(f"status_{status_key.lower()}", locale)
    return label, color, dot


def build_invite_embed(
    *,
    applicant: discord.abc.User,
    reason: str,
    contact: Optional[str],
    guild: Optional[discord.Guild],
    request_id: str,
    status: str = "PENDING",
    locale: str | None = "en",
) -> discord.Embed:
    label, color, dot = _status_block(status, locale)

    embed = discord.Embed(
        title=f"{BRAND_NAME} — Access Request",
        description=(
            f"`{dot}` **{label}**\n"
            f"{SOFT_DIVIDER}\n"
            f"A new request to access **Sublate** has been submitted."
        ),
        color=color,
        timestamp=datetime.now(timezone.utc),
    )

    embed.set_author(
        name=f"{applicant} · ID {applicant.id}",
        icon_url=applicant.display_avatar.url,
    )
    embed.set_thumbnail(url=applicant.display_avatar.url)

    embed.add_field(
        name=t("applicant_label", locale),
        value=f"{applicant.mention}\n`@{applicant.name}`",
        inline=True,
    )
    embed.add_field(
        name=t("account_age_label", locale),
        value=discord.utils.format_dt(applicant.created_at, style="R"),
        inline=True,
    )
    embed.add_field(
        name=t("origin_label", locale),
        value=f"`{guild.name}`" if guild else f"`{t('origin_dm', locale)}`",
        inline=True,
    )

    if contact:
        embed.add_field(
            name=t("contact_label", locale),
            value=f"```{sanitize_text(contact)[:200]}```",
            inline=False,
        )

    reason_block = sanitize_text(reason)
    if len(reason_block) > 1000:
        reason_block = reason_block[:997] + "..."
    embed.add_field(
        name=t("reason_label", locale),
        value=f"```{reason_block}```",
        inline=False,
    )

    embed.add_field(
        name=t("tracking_label", locale),
        value=f"`{request_id}`",
        inline=False,
    )

    embed.set_footer(text=BRAND_FOOTER, icon_url=BRAND_ICON)
    return embed


def build_decision_dm(
    *,
    accepted: bool,
    reviewer: discord.abc.User,
    note: str | None,
    access_key: str | None,
    locale: str | None,
) -> discord.Embed:
    if accepted:
        embed = info_embed(
            t("decision_accepted_title", locale),
            t("decision_accepted_desc", locale),
            color=COLOR_ACCEPT,
        )
    else:
        embed = info_embed(
            t("decision_declined_title", locale),
            t("decision_declined_desc", locale),
            color=COLOR_DECLINE,
        )

    embed.add_field(
        name=t("decision_reviewer", locale),
        value=f"`@{reviewer.name}`",
        inline=False,
    )

    if note:
        embed.add_field(
            name=t("decision_note", locale),
            value=f"```{sanitize_text(note)[:900]}```",
            inline=False,
        )

    if accepted and access_key:
        embed.add_field(
            name=t("decision_key", locale),
            value=f"||`{access_key}`||\n_{t('decision_key_warn', locale)}_",
            inline=False,
        )
    return embed


def build_applicant_ack(
    *,
    request_id: str,
    eta: str,
    locale: str | None,
) -> discord.Embed:
    embed = success_embed(
        t("ack_sent_title", locale),
        t("ack_sent_desc", locale),
    )
    embed.add_field(name=t("ack_sent_id", locale), value=f"`{request_id}`", inline=True)
    embed.add_field(name=t("ack_sent_eta", locale), value=eta, inline=True)
    return embed


def build_log_embed(
    *,
    title: str,
    description: str,
    color: int,
    fields: list[tuple[str, str, bool]] | None = None,
) -> discord.Embed:
    embed = _base(title, description, color)
    for name, value, inline in (fields or []):
        embed.add_field(name=name, value=value, inline=inline)
    return embed
