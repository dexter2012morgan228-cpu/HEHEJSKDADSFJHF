from __future__ import annotations

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from sublate.commands import setup_cog
from sublate.config import ConfigStore, EnvConfig
from sublate.context import BotContext
from sublate.health import start_health_server
from sublate.security import env_is_committed_warning, is_token_format_ok, mask_token
from sublate.views import DecisionView, WithdrawView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("sublate")


def _redact_in_logs(token: str) -> None:
    masked = mask_token(token)

    class _Redact(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if isinstance(record.msg, str) and token and token in record.msg:
                record.msg = record.msg.replace(token, masked)
            if record.args:
                try:
                    record.args = tuple(
                        a.replace(token, masked) if isinstance(a, str) and token in a else a
                        for a in record.args
                    )
                except Exception:
                    pass
            return True

    logging.getLogger().addFilter(_Redact())


async def main() -> None:
    load_dotenv()

    try:
        env = EnvConfig.from_env()
    except RuntimeError as exc:
        log.error("Configuration error: %s", exc)
        sys.exit(1)

    if not is_token_format_ok(env.token):
        log.error("DISCORD_TOKEN does not look like a valid bot token. Aborting.")
        sys.exit(1)

    _redact_in_logs(env.token)

    warn = env_is_committed_warning()
    if warn:
        log.warning("Security: %s", warn)

    cfg = ConfigStore(env)

    intents = discord.Intents.default()

    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
    context = BotContext(bot, cfg)

    bot.add_view(DecisionView(owner_id=env.owner_id, context=context))
    bot.add_view(WithdrawView(context=context))

    @bot.event
    async def on_ready():
        log.info(
            "Logged in as %s (ID: %s) — %d guild(s)",
            bot.user, bot.user.id if bot.user else "?", len(bot.guilds),
        )
        await cfg.load_from_discord(bot)

        try:
            synced = await bot.tree.sync()
            log.info("Synced %d application command(s).", len(synced))
        except Exception as exc:
            log.exception("Slash command sync failed: %s", exc)

        try:
            await bot.change_presence(
                status=discord.Status.dnd,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="Sublate · /sendinv",
                ),
            )
        except Exception:
            pass

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error):
        log.exception("App command error: %s", error)
        try:
            payload = {
                "embed": discord.Embed(
                    title="Something went wrong",
                    description=f"```{type(error).__name__}: {error}```",
                    color=0x0A0E14,
                ),
                "ephemeral": True,
            }
            if interaction.response.is_done():
                await interaction.followup.send(**payload)
            else:
                await interaction.response.send_message(**payload)
        except Exception:
            pass

    await setup_cog(bot, context)

    runner = await start_health_server(bot, env.health_port)

    try:
        await bot.start(env.token)
    finally:
        if runner is not None:
            await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
