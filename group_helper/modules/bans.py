import html
import logging
from typing import Optional

from telegram import Message, Chat, Update, User, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters
from telegram.ext.callbackcontext import CallbackContext
from telegram.utils.helpers import mention_html
from group_helper import CONFIG
from group_helper.modules.disable import DisableAbleCommandHandler
from group_helper.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat
from group_helper.modules.helper_funcs.extraction import extract_user_and_text
from group_helper.modules.helper_funcs.string_handling import extract_time
from group_helper.modules.log_channel import loggable

from group_helper.modules.database import antispam_mongo as sql

from group_helper.modules.tr_engine.strings import tld


@bot_admin
@can_restrict
@user_admin
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "common_err_no_user"))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found.":
            message.reply_text(tld(chat.id, "bans_err_usr_not_found"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "bans_err_usr_is_bot"))
        return ""

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "bans_err_usr_is_admin"))
        return ""

    log = tld(chat.id, "bans_logger").format(
        html.escape(chat.title), mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name), user_id)

    reply = tld(chat.id, "bans_banned_success").format(
        mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name),
        html.escape(chat.title))

    if reason:
        log += tld(chat.id, "bans_logger_reason").format(reason)
        reply += tld(chat.id, "bans_logger_reason").format(reason)

    try:
        chat.kick_member(user_id)
        message.reply_text(reply, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(reply, quote=False, parse_mode=ParseMode.HTML)
            return log
        else:
            logging.warning(update)
            logging.error("ERROR banning user %s in chat %s (%s) due to %s",
                          user_id, chat.title, chat.id, excp.message)
            message.reply_text(
                tld(chat.id, "bans_err_unknown").format("banning"))

    return ""






@bot_admin
@can_restrict
@user_admin
@loggable
def gban(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "common_err_no_user"))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found.":
            message.reply_text(tld(chat.id, "bans_err_usr_not_found"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "bans_err_usr_is_bot"))
        return ""

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "bans_err_usr_is_admin"))
        return ""

    log = tld(chat.id, "bans_logger").format(
        html.escape(chat.title), mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name), user_id)

    reply = tld(chat.id, "bans_banned_success").format(
        mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name),
        html.escape(chat.title))

    if reason:
        log += tld(chat.id, "bans_logger_reason").format(reason)
        reply += tld(chat.id, "bans_logger_reason").format(reason)

    try:
        user_chats = sql.get_user_joined_chats(int(user_id))
        for chat in user_chats:
            context.bot.ban_chat_member(int(chat), user_id)
            context.bot.send_message(int(chat), reply, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(reply, quote=False, parse_mode=ParseMode.HTML)
            return log
        else:
            logging.warning(update)
            logging.error("ERROR banning user %s in chat %s (%s) due to %s",
                          user_id, chat.title, chat.id, excp.message)
            message.reply_text(
                tld(chat.id, "bans_err_unknown").format("banning"))

    return ""



@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "common_err_no_user"))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found.":
            message.reply_text(tld(chat.id, "bans_err_usr_not_found"))
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "bans_err_usr_is_admin"))
        return ""

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "bans_err_usr_is_bot"))
        return ""

    if not reason:
        message.reply_text(tld(chat.id, "bans_err_tban_no_arg"))
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = tld(chat.id, "bans_tban_logger").format(
        html.escape(chat.title), mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name), member.user.id,
        time_val)
    if reason:
        log += tld(chat.id, "bans_logger_reason").format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        reply = tld(chat.id, "bans_tbanned_success").format(
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            html.escape(chat.title), time_val)
        reply += tld(chat.id, "bans_logger_reason").format(reason)
        message.reply_text(reply, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(tld(chat.id, "bans_tbanned_success").format(
                mention_html(user.id, user.first_name),
                mention_html(member.user.id, member.user.first_name),
                html.escape(chat.title), time_val),
                               quote=False)
            return log
        else:
            logging.warning(update)
            logging.error("ERROR banning user %s in chat %s (%s) due to %s",
                          user_id, chat.title, chat.id, excp.message)
            message.reply_text(
                tld(chat.id, "bans_err_unknown").format("tbanning"))

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
def kick(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "common_err_no_user"))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found.":
            message.reply_text(tld(chat.id, "bans_err_usr_not_found"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "bans_kick_is_bot"))
        return ""

    if is_user_ban_protected(chat, user_id):
        message.reply_text(tld(chat.id, "bans_kick_is_admin"))
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        reply = tld(chat.id, "bans_kick_success").format(
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            html.escape(chat.title))
        if reason:
            reply += tld(chat.id, "bans_logger_reason").format(reason)

        message.reply_text(reply, parse_mode=ParseMode.HTML)

        log = tld(chat.id, "bans_kick_logger").format(
            html.escape(chat.title), mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id)
        if reason:
            log += tld(chat.id, "bans_logger_reason").format(reason)

        return log

    else:
        message.reply_text(tld(chat.id, "bans_err_unknown").format("kicking"))

    return ""


@bot_admin
@can_restrict
def kickme(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]

    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(tld(chat.id, "bans_kick_is_admin"))
        return

    res = update.effective_chat.unban_member(
        user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text(tld(chat.id,
                                                "bans_kickme_success"))
    else:
        update.effective_message.reply_text(tld(chat.id, "bans_kickme_failed"))


@bot_admin
@can_restrict
@loggable
def banme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            tld(chat.id, "bans_err_usr_is_admin"))
        return

    res = update.effective_chat.kick_member(user_id)
    if res:
        update.effective_message.reply_text(tld(chat.id,
                                                "bans_kickme_success"))

    else:
        update.effective_message.reply_text(tld(chat.id, "bans_kickme_failed"))


@bot_admin
@can_restrict
@user_admin
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    args = context.args
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "common_err_no_user"))
            return ""
        else:
            raise

    if is_user_in_chat(chat, user_id):
        message.reply_text(tld(chat.id, "bans_unban_user_in_chat"))
        return ""

    chat.unban_member(user_id)
    message.reply_text(tld(chat.id, "bans_unban_success"))

    log = tld(chat.id, "bans_unban_logger").format(
        html.escape(chat.title), mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name), member.user.id)
    if reason:
        log += tld(chat.id, "bans_logger_reason").format(reason)

    return log


@bot_admin
@can_restrict
@user_admin
@loggable
def sban(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        return ""

    if user_id == context.bot.id:
        return ""

    log = tld(chat.id, "bans_sban_logger").format(
        html.escape(chat.title), mention_html(user.id, user.first_name),
        mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += tld(chat.id, "bans_logger_reason").format(reason)

    try:
        chat.kick_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            return log
        else:
            logging.warning(update)
            logging.exception(
                "ERROR banning user %s in chat %s (%s) due to %s", user_id,
                chat.title, chat.id, excp.message)
    return ""


__help__ = True

BAN_HANDLER = DisableAbleCommandHandler("ban",
                                        ban,
                                        pass_args=True,
                                        run_async=True,
                                        filters=Filters.chat_type.groups,
                                        admin_ok=True)
GBAN_HANDLER = DisableAbleCommandHandler("gban",
                                        gban,
                                        pass_args=True,
                                        run_async=True,
                                        filters=Filters.chat_type.groups,
                                        admin_ok=True)
TEMPBAN_HANDLER = DisableAbleCommandHandler(["tban", "tempban"],
                                            temp_ban,
                                            pass_args=True,
                                            run_async=True,
                                            filters=Filters.chat_type.groups,
                                            admin_ok=True)
KICK_HANDLER = DisableAbleCommandHandler("kick",
                                         kick,
                                         pass_args=True,
                                         run_async=True,
                                         filters=Filters.chat_type.groups,
                                         admin_ok=True)
UNBAN_HANDLER = DisableAbleCommandHandler("unban",
                                          unban,
                                          pass_args=True,
                                          run_async=True,
                                          filters=Filters.chat_type.groups,
                                          admin_ok=True)
KICKME_HANDLER = DisableAbleCommandHandler("kickme",
                                           kickme,
                                           filters=Filters.chat_type.groups)
SBAN_HANDLER = DisableAbleCommandHandler("sban",
                                         sban,
                                         pass_args=True,
                                         run_async=True,
                                         filters=Filters.chat_type.groups,
                                         admin_ok=True)
BANME_HANDLER = DisableAbleCommandHandler("banme",
                                          banme,
                                          run_async=True,
                                          filters=Filters.chat_type.groups)

CONFIG.dispatcher.add_handler(BAN_HANDLER)
CONFIG.dispatcher.add_handler(GBAN_HANDLER)
CONFIG.dispatcher.add_handler(TEMPBAN_HANDLER)
CONFIG.dispatcher.add_handler(KICK_HANDLER)
CONFIG.dispatcher.add_handler(UNBAN_HANDLER)
CONFIG.dispatcher.add_handler(KICKME_HANDLER)
CONFIG.dispatcher.add_handler(BANME_HANDLER)
CONFIG.dispatcher.add_handler(SBAN_HANDLER)
