from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

import discord

log = logging.getLogger("sublate.config")

PALETTE = {
    "deep_black":    0x030508,
    "rich_charcoal": 0x0A0E14,
    "midnight":      0x101722,
    "slate":         0x2A313C,
    "silver_mist":   0x5A6470,
    "faint_glow":    0xAEB7C2,
}

COLOR_PRIMARY = PALETTE["midnight"]
COLOR_PENDING = PALETTE["slate"]
COLOR_ACCEPT  = PALETTE["silver_mist"]
COLOR_DECLINE = PALETTE["rich_charcoal"]
COLOR_INFO    = PALETTE["midnight"]
COLOR_WARN    = PALETTE["slate"]

BRAND_NAME    = "Sublate Key"
BRAND_PRODUCT = "Sublate"
BRAND_FOOTER  = "Sublate • Access Management"
BRAND_ICON    = os.getenv("BRAND_ICON_URL", "https://cdn.discordapp.com/embed/avatars/0.png")

CONFIG_MARKER = "SUBLATE_CONFIG_V1"


@dataclass
class RuntimeConfig:
    log_channel_id: Optional[int] = None
    role_on_accept_id: Optional[int] = None
    cooldown_hours: float = 12.0
    min_account_age_days: int = 7
    avg_response_time: str = "within 24 hours"
    config_guild_id: Optional[int] = None
    config_channel_id: Optional[int] = None
    config_message_id: Optional[int] = None

    def to_json(self) -> str:
        data = asdict(self)
        return f"{CONFIG_MARKER}\n```json\n{json.dumps(data, indent=2)}\n```"

    @classmethod
    def from_message_content(cls, content: str) -> Optional["RuntimeConfig"]:
        if CONFIG_MARKER not in content:
            return None
        try:
            start = content.index("```json")
            end = content.index("```", start + 7)
            payload = content[start + 7:end].strip()
            data = json.loads(payload)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except (ValueError, json.JSONDecodeError) as exc:
            log.warning("Failed to parse runtime config: %s", exc)
            return None


@dataclass
class EnvConfig:
    token: str
    owner_id: Optional[int]
    owner_username: str
    config_channel_id: Optional[int]
    log_channel_id: Optional[int]
    role_on_accept_id: Optional[int]
    cooldown_hours: float
    min_account_age_days: int
    key_signing_secret: str
    health_port: int

    @classmethod
    def from_env(cls) -> "EnvConfig":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token or "." not in token:
            raise RuntimeError("DISCORD_TOKEN is missing or malformed in environment")

        def _int(name: str) -> Optional[int]:
            raw = os.getenv(name, "").strip()
            return int(raw) if raw.isdigit() else None

        return cls(
            token=token,
            owner_id=_int("OWNER_ID"),
            owner_username=os.getenv("OWNER_USERNAME", "jadexov").strip(),
            config_channel_id=_int("CONFIG_CHANNEL_ID"),
            log_channel_id=_int("LOG_CHANNEL_ID"),
            role_on_accept_id=_int("ROLE_ON_ACCEPT_ID"),
            cooldown_hours=float(os.getenv("COOLDOWN_HOURS", "12") or 12),
            min_account_age_days=int(os.getenv("MIN_ACCOUNT_AGE_DAYS", "7") or 7),
            key_signing_secret=os.getenv("KEY_SIGNING_SECRET", "sublate-default-secret-change-me"),
            health_port=int(os.getenv("PORT", "8080") or 8080),
        )


class ConfigStore:
    def __init__(self, env: EnvConfig):
        self.env = env
        self.runtime = RuntimeConfig(
            log_channel_id=env.log_channel_id,
            role_on_accept_id=env.role_on_accept_id,
            cooldown_hours=env.cooldown_hours,
            min_account_age_days=env.min_account_age_days,
            config_channel_id=env.config_channel_id,
        )

    async def load_from_discord(self, bot: discord.Client) -> None:
        if not self.env.config_channel_id:
            log.info("No CONFIG_CHANNEL_ID set, using env defaults only.")
            return

        channel = bot.get_channel(self.env.config_channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(self.env.config_channel_id)
            except (discord.NotFound, discord.Forbidden) as exc:
                log.warning("Config channel unreachable: %s", exc)
                return

        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            log.warning("Config channel is not a text channel.")
            return

        try:
            pins = await channel.pins()
        except discord.Forbidden:
            log.warning("No permission to read pins in config channel.")
            return

        for msg in pins:
            if msg.author.id == bot.user.id and CONFIG_MARKER in msg.content:
                cfg = RuntimeConfig.from_message_content(msg.content)
                if cfg:
                    cfg.config_channel_id = self.env.config_channel_id
                    cfg.config_guild_id = msg.guild.id if msg.guild else None
                    cfg.config_message_id = msg.id
                    self.runtime = cfg
                    log.info("Runtime config loaded from pinned message %s.", msg.id)
                    return

        await self.persist(bot)

    async def persist(self, bot: discord.Client) -> None:
        if not self.env.config_channel_id:
            return

        channel = bot.get_channel(self.env.config_channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(self.env.config_channel_id)
            except (discord.NotFound, discord.Forbidden):
                return

        content = self.runtime.to_json()

        if self.runtime.config_message_id:
            try:
                msg = await channel.fetch_message(self.runtime.config_message_id)
                await msg.edit(content=content)
                return
            except (discord.NotFound, discord.Forbidden):
                self.runtime.config_message_id = None

        try:
            msg = await channel.send(content)
            await msg.pin(reason="Sublate runtime config")
            self.runtime.config_message_id = msg.id
            self.runtime.config_guild_id = msg.guild.id if msg.guild else None
            log.info("Runtime config persisted as pinned message %s.", msg.id)
        except discord.Forbidden:
            log.warning("Cannot persist config: missing permissions in config channel.")

    def export_dict(self) -> dict:
        return asdict(self.runtime)
