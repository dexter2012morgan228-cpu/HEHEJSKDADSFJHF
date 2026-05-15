from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from .config import (
    BRAND_NAME,
    COLOR_ACCEPT,
    COLOR_DECLINE,
    COLOR_INFO,
    COLOR_PENDING,
)
from .embeds import (
    build_applicant_ack,
    build_invite_embed,
    error_embed,
    info_embed,
    warn_embed,
)
from .localization import pick_lang, t
from .security import (
    count_links,
    detect_blacklist,
    short_id,
)
from .views import DecisionView, InviteModal, WithdrawView

log = logging.getLogger("sublate.commands")


async def handle_submission(
    *,
    interaction: discord.Interaction,
    context: "BotContext",
    reason: str,
    contact: Optional[str],
    locale: str,
) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)

    user = interaction.user
    runtime = context.cfg.runtime
    state = context.state

    cooldown_until = state.get_cooldown(user.id)
    if cooldown_until:
        when = discord.utils.format_dt(
            datetime.fromtimestamp(cooldown_until, tz=timezone.utc),
            style="R",
        )
        state.stats.blocked_cooldown += 1
        await interaction.followup.send(
            embed=warn_embed(
                t("guard_cooldown_title", locale),
                t("guard_cooldown_desc", locale, when=when),
            ),
            ephemeral=True,
        )
        return

    min_age = max(int(runtime.min_account_age_days or 0), 0)
    if min_age > 0:
        age = datetime.now(timezone.utc) - user.created_at
        if age < timedelta(days=min_age):
            state.stats.blocked_age += 1
            await interaction.followup.send(
                embed=warn_embed(
                    t("guard_age_title", locale),
                    t("guard_age_desc", locale, days=min_age),
                ),
                ephemeral=True,
            )
            return

    bad = detect_blacklist(reason) or (detect_blacklist(contact) if contact else None)
    if bad:
        state.stats.blocked_blacklist += 1
        await interaction.followup.send(
            embed=error_embed(
                t("guard_blacklist_title", locale),
                t("guard_blacklist_desc", locale),
            ),
            ephemeral=True,
        )
        await context.log_event(
            title="Blocked submission",
            description=f"<@{user.id}> blocked — matched `{bad}`",
            color=COLOR_DECLINE,
        )
        return

    if user.id in state.pending_applicants:
        await interaction.followup.send(
            embed=warn_embed(
                t("guard_pending_title", locale),
                t("guard_pending_desc", locale),
            ),
            ephemeral=True,
        )
        return

    owner = await context.resolve_owner()
    if owner is None:
        await interaction.followup.send(
            embed=error_embed(
                t("fail_owner_title", locale),
                t("fail_owner_desc", locale),
            ),
            ephemeral=True,
        )
        return

    request_id = short_id()

    invite_embed = build_invite_embed(
        applicant=user,
        reason=reason,
        contact=contact,
        guild=interaction.guild,
        request_id=request_id,
        status="PENDING",
        locale=pick_lang(None),
    )

    decision_view = DecisionView(owner_id=owner.id, context=context)

    try:
        await owner.send(embed=invite_embed, view=decision_view)
    except discord.Forbidden:
        await interaction.followup.send(
            embed=error_embed(
                t("fail_dm_closed_title", locale),
                t("fail_dm_closed_desc", locale),
            ),
            ephemeral=True,
        )
        return
    except discord.HTTPException as exc:
        log.exception("Failed to deliver invite to owner: %s", exc)
        await interaction.followup.send(
            embed=error_embed(
                t("fail_generic_title", locale),
                t("fail_generic_desc", locale),
            ),
            ephemeral=True,
        )
        return

    state.set_cooldown(user.id, runtime.cooldown_hours)
    state.mark_pending(user.id)
    state.stats.submitted += 1

    try:
        applicant_dm_embed = build_invite_embed(
            applicant=user,
            reason=reason,
            contact=contact,
            guild=interaction.guild,
            request_id=request_id,
            status="PENDING",
            locale=locale,
        )
        await user.send(embed=applicant_dm_embed, view=WithdrawView(context))
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass

    await context.log_event(
        title="New request",
        description=f"`{request_id}` — <@{user.id}> submitted a request",
        color=COLOR_PENDING,
        fields=[
            ("Links in reason", str(count_links(reason)), True),
            ("Account age", discord.utils.format_dt(user.created_at, style="R"), True),
        ],
    )

    await interaction.followup.send(
        embed=build_applicant_ack(
            request_id=request_id,
            eta=runtime.avg_response_time,
            locale=locale,
        ),
        ephemeral=True,
    )


class SublateCog(commands.Cog):
    def __init__(self, bot: commands.Bot, context: "BotContext"):
        self.bot = bot
        self.context = context

    @app_commands.command(name="sendinv", description="Submit an access request for Sublate.")
    async def sendinv(self, interaction: discord.Interaction):
        locale = pick_lang(interaction.locale)
        await interaction.response.send_modal(InviteModal(self.context, locale))

    @app_commands.command(name="whoami", description="Check your current Sublate request status.")
    async def whoami(self, interaction: discord.Interaction):
        locale = pick_lang(interaction.locale)
        if interaction.user.id in self.context.state.pending_applicants:
            embed = info_embed(
                t("whoami_title", locale),
                t("whoami_pending", locale, when="recently"),
            )
        else:
            embed = info_embed(
                t("whoami_title", locale),
                t("whoami_none", locale),
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="invstats", description="Owner-only: session statistics.")
    @app_commands.default_permissions(administrator=True)
    async def invstats(self, interaction: discord.Interaction):
        if not await self._owner_check(interaction):
            return
        s = self.context.state.stats
        uptime = time.time() - s.started_at
        hours = uptime / 3600
        embed = info_embed(
            t("stats_title", pick_lang(interaction.locale)),
            t("stats_desc", pick_lang(interaction.locale)),
        )
        embed.add_field(name="Submitted", value=str(s.submitted), inline=True)
        embed.add_field(name="Accepted", value=str(s.accepted), inline=True)
        embed.add_field(name="Declined", value=str(s.declined), inline=True)
        embed.add_field(name="Withdrawn", value=str(s.withdrawn), inline=True)
        embed.add_field(name="Blocked (age)", value=str(s.blocked_age), inline=True)
        embed.add_field(name="Blocked (blacklist)", value=str(s.blocked_blacklist), inline=True)
        embed.add_field(name="Blocked (cooldown)", value=str(s.blocked_cooldown), inline=True)
        embed.add_field(name="Uptime", value=f"{hours:.2f} h", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="invreopen", description="Owner-only: reattach decision buttons to an old request.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(message_id="ID of the invite message in your DMs.")
    async def invreopen(self, interaction: discord.Interaction, message_id: str):
        if not await self._owner_check(interaction):
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            mid = int(message_id)
        except ValueError:
            await interaction.followup.send(
                embed=error_embed("Invalid", "message_id must be a numeric ID."),
                ephemeral=True,
            )
            return

        dm = interaction.user.dm_channel or await interaction.user.create_dm()
        try:
            msg = await dm.fetch_message(mid)
        except discord.NotFound:
            await interaction.followup.send(
                embed=error_embed("Not found", "Message not found in your DMs."),
                ephemeral=True,
            )
            return

        view = DecisionView(owner_id=interaction.user.id, context=self.context)
        try:
            await msg.edit(view=view)
        except discord.HTTPException as exc:
            await interaction.followup.send(
                embed=error_embed("Failed", f"```{exc}```"),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            embed=info_embed("Reopened", f"Buttons reattached to message `{mid}`.", color=COLOR_ACCEPT),
            ephemeral=True,
        )

    invconfig = app_commands.Group(
        name="invconfig",
        description="Owner-only: configure the Sublate Key bot.",
        default_permissions=discord.Permissions(administrator=True),
    )

    @invconfig.command(name="show", description="Show current configuration.")
    async def cfg_show(self, interaction: discord.Interaction):
        if not await self._owner_check(interaction):
            return
        rt = self.context.cfg.runtime
        embed = info_embed(
            t("config_view_title", pick_lang(interaction.locale)),
            "Current runtime configuration.",
        )
        embed.add_field(name="Log channel", value=f"<#{rt.log_channel_id}>" if rt.log_channel_id else "—", inline=True)
        embed.add_field(name="Role on accept", value=f"<@&{rt.role_on_accept_id}>" if rt.role_on_accept_id else "—", inline=True)
        embed.add_field(name="Cooldown (h)", value=str(rt.cooldown_hours), inline=True)
        embed.add_field(name="Min account age (d)", value=str(rt.min_account_age_days), inline=True)
        embed.add_field(name="Avg response", value=rt.avg_response_time, inline=True)
        embed.add_field(name="Config channel", value=f"<#{rt.config_channel_id}>" if rt.config_channel_id else "—", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @invconfig.command(name="set", description="Update a configuration field.")
    @app_commands.describe(
        log_channel="Channel for log events.",
        role_on_accept="Role granted to accepted applicants.",
        cooldown_hours="Cooldown between submissions per user.",
        min_account_age_days="Reject accounts younger than this.",
        avg_response_time="ETA shown to applicants.",
    )
    async def cfg_set(
        self,
        interaction: discord.Interaction,
        log_channel: Optional[discord.TextChannel] = None,
        role_on_accept: Optional[discord.Role] = None,
        cooldown_hours: Optional[float] = None,
        min_account_age_days: Optional[int] = None,
        avg_response_time: Optional[str] = None,
    ):
        if not await self._owner_check(interaction):
            return
        rt = self.context.cfg.runtime
        if log_channel is not None:
            rt.log_channel_id = log_channel.id
        if role_on_accept is not None:
            rt.role_on_accept_id = role_on_accept.id
        if cooldown_hours is not None:
            rt.cooldown_hours = max(cooldown_hours, 0)
        if min_account_age_days is not None:
            rt.min_account_age_days = max(min_account_age_days, 0)
        if avg_response_time is not None:
            rt.avg_response_time = avg_response_time[:80]

        await self.context.cfg.persist(self.bot)

        await interaction.response.send_message(
            embed=info_embed(
                t("config_view_title", pick_lang(interaction.locale)),
                t("config_updated", pick_lang(interaction.locale)),
                color=COLOR_ACCEPT,
            ),
            ephemeral=True,
        )

    async def _owner_check(self, interaction: discord.Interaction) -> bool:
        owner = await self.context.resolve_owner()
        if owner is None or interaction.user.id != owner.id:
            await interaction.response.send_message(
                embed=error_embed("⛔", t("guard_owner_only", interaction.locale)),
                ephemeral=True,
            )
            return False
        return True


async def setup_cog(bot: commands.Bot, context: "BotContext") -> None:
    await bot.add_cog(SublateCog(bot, context))
