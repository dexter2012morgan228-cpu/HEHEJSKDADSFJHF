from __future__ import annotations

import logging
from typing import Optional

import discord
from discord.ext import commands

from .config import (
    BRAND_FOOTER,
    BRAND_ICON,
    COLOR_ACCEPT,
    COLOR_DECLINE,
    COLOR_PENDING,
    ConfigStore,
)
from .embeds import build_log_embed, error_embed
from .state import State

log = logging.getLogger("sublate.context")


class BotContext:
    """Shared runtime context passed into views, modals and cogs."""

    def __init__(self, bot: commands.Bot, cfg: ConfigStore):
        self.bot = bot
        self.cfg = cfg
        self.state = State()

    async def resolve_owner(self) -> Optional[discord.User]:
        env = self.cfg.env
        bot = self.bot

        if env.owner_id:
            user = bot.get_user(env.owner_id)
            if user:
                return user
            try:
                return await bot.fetch_user(env.owner_id)
            except discord.NotFound:
                pass

        try:
            app_info = await bot.application_info()
            if app_info.team and app_info.team.owner:
                return app_info.team.owner
            if app_info.owner:
                return app_info.owner
        except Exception as exc:
            log.warning("application_info failed: %s", exc)

        if env.owner_username:
            for user in bot.users:
                if user.name.lower() == env.owner_username.lower():
                    return user
        return None

    async def log_event(
        self,
        *,
        title: str,
        description: str,
        color: int = COLOR_PENDING,
        fields: Optional[list[tuple[str, str, bool]]] = None,
    ) -> None:
        channel_id = self.cfg.runtime.log_channel_id
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden):
                return

        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        try:
            await channel.send(
                embed=build_log_embed(
                    title=title,
                    description=description,
                    color=color,
                    fields=fields,
                )
            )
        except discord.Forbidden:
            log.warning("Missing permission to post in log channel %s", channel_id)
        except discord.HTTPException as exc:
            log.warning("Log post failed: %s", exc)
