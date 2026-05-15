from __future__ import annotations

LOCALES = {
    "en": {
        "modal_title": "Sublate Key — Access Request",
        "modal_reason_label": "Why should you get access to Sublate?",
        "modal_reason_placeholder": "Tell us about yourself, your use case and why we should grant access…",
        "modal_contact_label": "Preferred contact (Telegram, email, etc.)",
        "modal_contact_placeholder": "@username / email — optional",

        "preview_title": "Sublate Key — Review your request",
        "preview_desc": "Here is how your request will look. Confirm to send it to the Sublate team.",
        "preview_btn_send": "Send",
        "preview_btn_edit": "Edit",
        "preview_btn_cancel": "Cancel",

        "ack_sent_title": "Sublate Key — Request Sent",
        "ack_sent_desc": "Your access request has been delivered to the Sublate team.\nYou will receive a direct message once a decision is made.",
        "ack_sent_id": "Tracking ID",
        "ack_sent_eta": "Estimated response",

        "ack_cancelled_title": "Cancelled",
        "ack_cancelled_desc": "Your draft has been discarded.",

        "fail_owner_title": "Submission failed",
        "fail_owner_desc": "Could not resolve the Sublate owner. Please try again later or contact `@jadexov` directly.",
        "fail_dm_closed_title": "Submission failed",
        "fail_dm_closed_desc": "The owner has DMs closed and cannot receive your request right now. Please contact `@jadexov` on Discord or `@skeetdontupdate` on Telegram.",
        "fail_generic_title": "Submission failed",
        "fail_generic_desc": "An unexpected error occurred while sending your request.",

        "guard_cooldown_title": "Slow down",
        "guard_cooldown_desc": "You can submit a new request **{when}**.",
        "guard_age_title": "Account too new",
        "guard_age_desc": "Your Discord account must be at least **{days} days** old to apply.",
        "guard_blacklist_title": "Request rejected",
        "guard_blacklist_desc": "Your request contains content that is not allowed.",
        "guard_pending_title": "Request already pending",
        "guard_pending_desc": "You already have a request awaiting review. You can withdraw it from your DMs.",

        "decision_accepted_title": "Sublate Key — Access Granted",
        "decision_accepted_desc": "Your request has been **accepted**.\nWelcome to **Sublate**.",
        "decision_declined_title": "Sublate Key — Access Declined",
        "decision_declined_desc": "Your request has been **declined**.\nThank you for your interest in **Sublate**.",
        "decision_reviewer": "Reviewed by",
        "decision_note": "Note from the team",
        "decision_key": "Your access key",
        "decision_key_warn": "Keep this key private. It is your personal credential.",

        "applicant_label": "Applicant",
        "account_age_label": "Account Created",
        "origin_label": "Origin",
        "origin_dm": "Direct Message",
        "contact_label": "Preferred Contact",
        "reason_label": "Reason for Access",
        "tracking_label": "Tracking ID",
        "decision_label": "Decision",
        "status_pending": "PENDING",
        "status_accepted": "ACCEPTED",
        "status_declined": "DECLINED",
        "status_withdrawn": "WITHDRAWN",

        "btn_accept": "Accept",
        "btn_accept_note": "Accept w/ note",
        "btn_decline": "Decline",
        "btn_decline_reason": "Decline w/ reason",
        "btn_withdraw": "Withdraw",

        "withdraw_confirm_title": "Request withdrawn",
        "withdraw_confirm_desc": "You have withdrawn your access request.",

        "whoami_title": "Sublate Key — Status",
        "whoami_none": "You have no active request.",
        "whoami_pending": "You have a pending request submitted {when}.",

        "guard_owner_only": "Only the Sublate owner can use this control.",
        "guard_applicant_only": "Only the applicant can withdraw this request.",

        "config_updated": "Configuration updated.",
        "config_view_title": "Sublate Key — Configuration",
        "stats_title": "Sublate Key — Session Stats",
        "stats_desc": "Statistics since the bot was last started.",

        "modal_note_title": "Add a note for the applicant",
        "modal_note_label": "Message to applicant",
        "modal_note_placeholder": "Optional note that will be delivered to the applicant.",

        "modal_reason_decline_title": "Reason for decline",
        "modal_reason_decline_label": "Reason",
        "modal_reason_decline_placeholder": "Optional reason that will be delivered to the applicant.",
    },

    "ru": {
        "modal_title": "Sublate Key — Заявка на доступ",
        "modal_reason_label": "Почему вы должны получить доступ к Sublate?",
        "modal_reason_placeholder": "Расскажите о себе, для чего вам Sublate и почему стоит выдать доступ…",
        "modal_contact_label": "Контакт (Telegram, email и т.п.)",
        "modal_contact_placeholder": "@username / email — необязательно",

        "preview_title": "Sublate Key — Проверьте заявку",
        "preview_desc": "Так будет выглядеть ваша заявка. Подтвердите отправку команде Sublate.",
        "preview_btn_send": "Отправить",
        "preview_btn_edit": "Изменить",
        "preview_btn_cancel": "Отмена",

        "ack_sent_title": "Sublate Key — Заявка отправлена",
        "ack_sent_desc": "Ваша заявка доставлена команде Sublate.\nВы получите личное сообщение после принятия решения.",
        "ack_sent_id": "Идентификатор заявки",
        "ack_sent_eta": "Ожидаемый ответ",

        "ack_cancelled_title": "Отменено",
        "ack_cancelled_desc": "Черновик удалён.",

        "fail_owner_title": "Ошибка отправки",
        "fail_owner_desc": "Не удалось определить владельца Sublate. Попробуйте позже или напишите `@jadexov`.",
        "fail_dm_closed_title": "Ошибка отправки",
        "fail_dm_closed_desc": "У владельца закрыты ЛС, заявка не может быть доставлена. Напишите `@jadexov` в Discord или `@skeetdontupdate` в Telegram.",
        "fail_generic_title": "Ошибка отправки",
        "fail_generic_desc": "Произошла непредвиденная ошибка при отправке заявки.",

        "guard_cooldown_title": "Слишком часто",
        "guard_cooldown_desc": "Вы сможете отправить новую заявку **{when}**.",
        "guard_age_title": "Аккаунт слишком новый",
        "guard_age_desc": "Вашему аккаунту Discord должно быть не менее **{days} дн.** для подачи заявки.",
        "guard_blacklist_title": "Заявка отклонена",
        "guard_blacklist_desc": "Ваша заявка содержит запрещённый контент.",
        "guard_pending_title": "У вас уже есть активная заявка",
        "guard_pending_desc": "У вас есть заявка, ожидающая рассмотрения. Её можно отозвать в ваших ЛС.",

        "decision_accepted_title": "Sublate Key — Доступ выдан",
        "decision_accepted_desc": "Ваша заявка **принята**.\nДобро пожаловать в **Sublate**.",
        "decision_declined_title": "Sublate Key — Доступ отклонён",
        "decision_declined_desc": "Ваша заявка **отклонена**.\nСпасибо за интерес к **Sublate**.",
        "decision_reviewer": "Рассмотрел",
        "decision_note": "Сообщение от команды",
        "decision_key": "Ваш ключ доступа",
        "decision_key_warn": "Храните ключ в тайне. Это ваш личный креденшл.",

        "applicant_label": "Заявитель",
        "account_age_label": "Аккаунт создан",
        "origin_label": "Источник",
        "origin_dm": "Личные сообщения",
        "contact_label": "Контакт",
        "reason_label": "Причина запроса",
        "tracking_label": "Идентификатор заявки",
        "decision_label": "Решение",
        "status_pending": "ОЖИДАНИЕ",
        "status_accepted": "ПРИНЯТО",
        "status_declined": "ОТКЛОНЕНО",
        "status_withdrawn": "ОТОЗВАНО",

        "btn_accept": "Принять",
        "btn_accept_note": "Принять с заметкой",
        "btn_decline": "Отклонить",
        "btn_decline_reason": "Отклонить с причиной",
        "btn_withdraw": "Отозвать",

        "withdraw_confirm_title": "Заявка отозвана",
        "withdraw_confirm_desc": "Вы отозвали свою заявку на доступ.",

        "whoami_title": "Sublate Key — Статус",
        "whoami_none": "У вас нет активных заявок.",
        "whoami_pending": "У вас есть заявка, поданная {when}.",

        "guard_owner_only": "Только владелец Sublate может использовать этот элемент.",
        "guard_applicant_only": "Только автор заявки может её отозвать.",

        "config_updated": "Конфигурация обновлена.",
        "config_view_title": "Sublate Key — Конфигурация",
        "stats_title": "Sublate Key — Статистика сессии",
        "stats_desc": "Статистика с момента последнего запуска бота.",

        "modal_note_title": "Сообщение заявителю",
        "modal_note_label": "Текст для заявителя",
        "modal_note_placeholder": "Необязательная заметка, которая будет доставлена заявителю.",

        "modal_reason_decline_title": "Причина отказа",
        "modal_reason_decline_label": "Причина",
        "modal_reason_decline_placeholder": "Необязательная причина, которая будет доставлена заявителю.",
    },
}


def pick_lang(locale: str | None) -> str:
    if not locale:
        return "en"
    code = str(locale).lower()
    if code.startswith("ru") or code.startswith("uk") or code.startswith("be"):
        return "ru"
    return "en"


def t(key: str, locale: str | None = None, **kwargs) -> str:
    lang = pick_lang(locale)
    value = LOCALES.get(lang, LOCALES["en"]).get(key) or LOCALES["en"].get(key, key)
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value
    return value
