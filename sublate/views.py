from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import discord

from .config import BRAND_NAME, COLOR_ACCEPT, COLOR_DECLINE, COLOR_PENDING
from .embeds import build_decision_dm, build_invite_embed, info_embed, error_embed, success_embed
from .localization import pick_lang, t
from .security import generate_access_key, sanitize_text

log = logging.getLogger("sublate.views")

CUSTOM_ID_ACCEPT = "sublate:accept"
CUSTOM_ID_ACCEPT_NOTE = "sublate:accept_note"
CUSTOM_ID_DECLINE = "sublate:decline"
CUSTOM_ID_DECLINE_REASON = "sublate:decline_reason"
CUSTOM_ID_WITHDRAW = "sublate:withdraw"
CUSTOM_ID_PREVIEW_SEND = "sublate:preview_send"
CUSTOM_ID_PREVIEW_EDIT = "sublate:preview_edit"
CUSTOM_ID_PREVIEW_CANCEL = "sublate:preview_cancel"

APPLICANT_RE = re.compile(r"ID\s+(\d+)")


def parse_invite_message(message: discord.Message) -> Optional[dict]:
    """Recover applicant_id, reason, contact, request_id from the embed."""
    if not message.embeds:
        return None
    embed = message.embeds[0]

    applicant_id: Optional[int] = None
    if embed.author and embed.author.name:
        m = APPLICANT_RE.search(embed.author.name)
        if m:
            applicant_id = int(m.group(1))

    reason = ""
    contact: Optional[str] = None
    request_id = ""

    for field in embed.fields:
        name = (field.name or "").lower()
        value = field.value or ""
        if "reason" in name or "причина" in name:
            reason = _strip_codeblock(value)
        elif "contact" in name or "контакт" in name:
            contact = _strip_codeblock(value)
        elif "tracking" in name or "идентификатор" in name:
            request_id = value.strip("` ").strip()

    if not applicant_id:
        return None

    return {
        "applicant_id": applicant_id,
        "reason": reason,
        "contact": contact,
        "request_id": request_id,
    }


def _strip_codeblock(value: str) -> str:
    raw = value.strip()
    if raw.startswith("```") and raw.endswith("```"):
        return raw.strip("`").strip()
    return raw


class _OwnerGuardMixin:
    def __init__(self, owner_id: Optional[int]):
        self.owner_id = owner_id

    async def _owner_only(self, interaction: discord.Interaction) -> bool:
        if self.owner_id and interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                embed=error_embed("⛔", t("guard_owner_only", interaction.locale)),
                ephemeral=True,
            )
            return False
        return True


class DecisionView(discord.ui.View, _OwnerGuardMixin):
    """Persistent view for owner-side decisions."""

    def __init__(self, owner_id: Optional[int], context: "BotContext"):
        discord.ui.View.__init__(self, timeout=None)
        _OwnerGuardMixin.__init__(self, owner_id)
        self.context = context

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self._owner_only(interaction)

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.success,
        emoji="\U00002705",
        custom_id=CUSTOM_ID_ACCEPT,
        row=0,
    )
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_decision(interaction, self.context, accepted=True, with_modal=False)

    @discord.ui.button(
        label="Accept w/ note",
        style=discord.ButtonStyle.secondary,
        emoji="\U0001F4DD",
        custom_id=CUSTOM_ID_ACCEPT_NOTE,
        row=0,
    )
    async def accept_note_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_decision(interaction, self.context, accepted=True, with_modal=True)

    @discord.ui.button(
        label="Decline",
        style=discord.ButtonStyle.danger,
        emoji="\U0000274C",
        custom_id=CUSTOM_ID_DECLINE,
        row=1,
    )
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_decision(interaction, self.context, accepted=False, with_modal=False)

    @discord.ui.button(
        label="Decline w/ reason",
        style=discord.ButtonStyle.secondary,
        emoji="\U0001F4DD",
        custom_id=CUSTOM_ID_DECLINE_REASON,
        row=1,
    )
    async def decline_reason_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_decision(interaction, self.context, accepted=False, with_modal=True)


class WithdrawView(discord.ui.View):
    """Persistent view in applicant DM with a single Withdraw button."""

    def __init__(self, context: "BotContext"):
        super().__init__(timeout=None)
        self.context = context

    @discord.ui.button(
        label="Withdraw",
        style=discord.ButtonStyle.secondary,
        emoji="\U0001F5D1\uFE0F",
        custom_id=CUSTOM_ID_WITHDRAW,
    )
    async def withdraw_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _resolve_withdraw(interaction, self.context)


class _NoteModal(discord.ui.Modal):
    note = discord.ui.TextInput(
        label="placeholder",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=900,
    )

    def __init__(self, *, accepted: bool, locale: str, parsed: dict, context: "BotContext"):
        title = t("modal_note_title" if accepted else "modal_reason_decline_title", locale)
        super().__init__(title=title[:45])
        self.accepted = accepted
        self.locale = locale
        self.parsed = parsed
        self.context = context

        self.note.label = t(
            "modal_note_label" if accepted else "modal_reason_decline_label",
            locale,
        )[:45]
        self.note.placeholder = t(
            "modal_note_placeholder" if accepted else "modal_reason_decline_placeholder",
            locale,
        )[:100]

    async def on_submit(self, interaction: discord.Interaction):
        await _finalize_decision(
            interaction=interaction,
            context=self.context,
            accepted=self.accepted,
            note=str(self.note.value) if self.note.value else None,
            parsed=self.parsed,
        )


async def _resolve_decision(
    interaction: discord.Interaction,
    context: "BotContext",
    accepted: bool,
    with_modal: bool,
) -> None:
    parsed = parse_invite_message(interaction.message) if interaction.message else None
    if not parsed:
        await interaction.response.send_message(
            embed=error_embed("⚠️", "Could not recover request data."),
            ephemeral=True,
        )
        return

    if with_modal:
        await interaction.response.send_modal(
            _NoteModal(
                accepted=accepted,
                locale=pick_lang(interaction.locale),
                parsed=parsed,
                context=context,
            )
        )
        return

    await _finalize_decision(
        interaction=interaction,
        context=context,
        accepted=accepted,
        note=None,
        parsed=parsed,
    )


async def _finalize_decision(
    *,
    interaction: discord.Interaction,
    context: "BotContext",
    accepted: bool,
    note: Optional[str],
    parsed: dict,
) -> None:
    applicant_id: int = parsed["applicant_id"]
    reason: str = parsed["reason"]
    contact: Optional[str] = parsed["contact"]
    request_id: str = parsed["request_id"] or "SBL-UNKNOWN"

    bot = context.bot

    applicant = bot.get_user(applicant_id)
    if applicant is None:
        try:
            applicant = await bot.fetch_user(applicant_id)
        except discord.NotFound:
            applicant = None

    status = "ACCEPTED" if accepted else "DECLINED"
    locale_owner = pick_lang(interaction.locale)

    if applicant is not None:
        updated_embed = build_invite_embed(
            applicant=applicant,
            reason=reason,
            contact=contact,
            guild=None,
            request_id=request_id,
            status=status,
            locale=locale_owner,
        )
    else:
        from .embeds import info_embed as _info
        updated_embed = _info(
            f"{BRAND_NAME} — Access {status.title()}",
            f"Applicant <@{applicant_id}> · Decision by {interaction.user.mention}",
            color=COLOR_ACCEPT if accepted else COLOR_DECLINE,
        )

    updated_embed.add_field(
        name=t("decision_label", locale_owner),
        value=(
            f"**{t(f'status_{status.lower()}', locale_owner)}** by `@{interaction.user.name}`\n"
            f"{discord.utils.format_dt(datetime.now(timezone.utc), style='F')}"
            + (f"\n```{sanitize_text(note)[:400]}```" if note else "")
        ),
        inline=False,
    )

    disabled_view = discord.ui.View(timeout=None)
    accept_btn = discord.ui.Button(
        label="Accepted" if accepted else "Accept",
        style=discord.ButtonStyle.success,
        emoji="\U00002705",
        disabled=True,
    )
    decline_btn = discord.ui.Button(
        label="Declined" if not accepted else "Decline",
        style=discord.ButtonStyle.danger,
        emoji="\U0000274C",
        disabled=True,
    )
    disabled_view.add_item(accept_btn)
    disabled_view.add_item(decline_btn)

    if interaction.response.is_done():
        await interaction.message.edit(embed=updated_embed, view=disabled_view)
    else:
        await interaction.response.edit_message(embed=updated_embed, view=disabled_view)

    access_key = None

    delivered = False
    if applicant is not None:
        locale_applicant = "en"
        try:
            dm_embed = build_decision_dm(
                accepted=accepted,
                reviewer=interaction.user,
                note=note,
                access_key=access_key,
                locale=locale_applicant,
            )
            dm_embed.add_field(name="Tracking ID", value=f"`{request_id}`", inline=False)
            await applicant.send(embed=dm_embed)
            delivered = True
        except discord.Forbidden:
            delivered = False
        except discord.HTTPException as exc:
            log.warning("Failed to DM applicant %s: %s", applicant_id, exc)

    context.state.clear_pending(applicant_id)

    if accepted:
        context.state.stats.accepted += 1
        await _maybe_assign_role(context, applicant_id, applicant, interaction)
    else:
        context.state.stats.declined += 1

    if not delivered and applicant is not None:
        try:
            await interaction.followup.send(
                embed=info_embed(
                    "Notice",
                    "Could not deliver the decision DM to the applicant.",
                    color=COLOR_PENDING,
                ),
                ephemeral=False,
            )
        except discord.HTTPException:
            pass

    await context.log_event(
        title=f"Decision · {status}",
        description=f"`{request_id}` — <@{applicant_id}> reviewed by {interaction.user.mention}",
        color=COLOR_ACCEPT if accepted else COLOR_DECLINE,
        fields=[
            ("Reason snippet", f"```{(reason or '')[:200]}```", False),
        ] + ([("Note", f"```{sanitize_text(note)[:200]}```", False)] if note else []),
    )


async def _maybe_assign_role(
    context: "BotContext",
    applicant_id: int,
    applicant: Optional[discord.User],
    interaction: discord.Interaction,
) -> None:
    role_id = context.cfg.runtime.role_on_accept_id
    if not role_id:
        return

    bot = context.bot
    assigned_anywhere = False
    for guild in bot.guilds:
        role = guild.get_role(role_id)
        if role is None:
            continue
        member = guild.get_member(applicant_id)
        if member is None:
            try:
                member = await guild.fetch_member(applicant_id)
            except (discord.NotFound, discord.Forbidden):
                continue
        try:
            await member.add_roles(role, reason=f"Sublate access granted by {interaction.user}")
            assigned_anywhere = True
        except discord.Forbidden:
            log.warning("Missing permission to assign role %s in guild %s", role_id, guild.id)
        except discord.HTTPException as exc:
            log.warning("Role assignment failed: %s", exc)

    if not assigned_anywhere:
        log.info("Role %s could not be assigned to %s anywhere.", role_id, applicant_id)


async def _resolve_withdraw(interaction: discord.Interaction, context: "BotContext") -> None:
    parsed = parse_invite_message(interaction.message) if interaction.message else None
    if not parsed:
        await interaction.response.send_message(
            embed=error_embed("⚠️", "Could not recover request data."),
            ephemeral=True,
        )
        return

    if interaction.user.id != parsed["applicant_id"]:
        await interaction.response.send_message(
            embed=error_embed("⛔", t("guard_applicant_only", interaction.locale)),
            ephemeral=True,
        )
        return

    locale = pick_lang(interaction.locale)
    request_id = parsed["request_id"] or "SBL-UNKNOWN"

    new_embed = build_invite_embed(
        applicant=interaction.user,
        reason=parsed["reason"],
        contact=parsed["contact"],
        guild=None,
        request_id=request_id,
        status="WITHDRAWN",
        locale=locale,
    )
    new_embed.add_field(
        name=t("decision_label", locale),
        value=f"**{t('status_withdrawn', locale)}** by `@{interaction.user.name}`",
        inline=False,
    )

    disabled_view = discord.ui.View(timeout=None)
    btn = discord.ui.Button(label="Withdrawn", style=discord.ButtonStyle.secondary, disabled=True)
    disabled_view.add_item(btn)

    await interaction.response.edit_message(embed=new_embed, view=disabled_view)

    context.state.clear_pending(interaction.user.id)
    context.state.stats.withdrawn += 1

    owner = await context.resolve_owner()
    if owner is not None:
        try:
            await owner.send(
                embed=info_embed(
                    f"{BRAND_NAME} — Request withdrawn",
                    f"`{request_id}` was withdrawn by <@{interaction.user.id}>.",
                    color=COLOR_PENDING,
                )
            )
        except discord.HTTPException:
            pass

    await context.log_event(
        title="Request withdrawn",
        description=f"`{request_id}` — <@{interaction.user.id}>",
        color=COLOR_PENDING,
    )

    await interaction.followup.send(
        embed=success_embed(
            t("withdraw_confirm_title", locale),
            t("withdraw_confirm_desc", locale),
        ),
        ephemeral=True,
    )


class InviteModal(discord.ui.Modal):
    reason = discord.ui.TextInput(
        label="placeholder",
        style=discord.TextStyle.paragraph,
        required=True,
        min_length=20,
        max_length=1500,
    )
    contact = discord.ui.TextInput(
        label="placeholder",
        style=discord.TextStyle.short,
        required=False,
        max_length=120,
    )

    def __init__(self, context: "BotContext", locale: str):
        super().__init__(title=t("modal_title", locale)[:45])
        self.context = context
        self.locale = locale
        self.reason.label = t("modal_reason_label", locale)[:45]
        self.reason.placeholder = t("modal_reason_placeholder", locale)[:100]
        self.contact.label = t("modal_contact_label", locale)[:45]
        self.contact.placeholder = t("modal_contact_placeholder", locale)[:100]

    async def on_submit(self, interaction: discord.Interaction):
        from .commands import handle_submission
        await handle_submission(
            interaction=interaction,
            context=self.context,
            reason=str(self.reason.value),
            contact=str(self.contact.value) if self.contact.value else None,
            locale=self.locale,
        )
