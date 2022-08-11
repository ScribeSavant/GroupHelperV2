
import html
import logging

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.ext.callbackcontext import CallbackContext

import tldextract
from group_helper import CONFIG
from group_helper.modules.disable import DisableAbleCommandHandler
from group_helper.modules.helper_funcs.chat_status import user_admin, user_not_admin
from group_helper.modules.database import urlbalcklist_mongo as sql
# from group_helper.modules.database import urlblacklist_sql as sql
from group_helper.modules.tr_engine.strings import tld
from group_helper.modules.connection import connected


@user_admin
def add_blacklist_url(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    urls = message.text.split(None, 1)
    if sql.is_delete_all(chat.id):
        return message.reply_text(tld(chat.id, "delete_all_enabled_err"), parse_mode=ParseMode.HTML)
    if len(urls) > 1:
        urls = urls[1]
        to_blacklist = list(
            set(uri.strip() for uri in urls.split("\n") if uri.strip()))
        blacklisted = []

        for uri in to_blacklist:
            extract_url = tldextract.extract(uri)
            if extract_url.domain and extract_url.suffix:
                blacklisted.append(extract_url.domain + "." +
                                   extract_url.suffix)
                sql.blacklist_url(
                    chat.id, extract_url.domain + "." + extract_url.suffix)

        if len(to_blacklist) == 1:
            extract_url = tldextract.extract(to_blacklist[0])
            if extract_url.domain and extract_url.suffix:
                message.reply_text(tld(
                    chat.id, "url_blacklist_success").format(
                        html.escape(extract_url.domain + "." +
                                    extract_url.suffix)),
                    parse_mode=ParseMode.HTML)
            else:
                message.reply_text(tld(chat.id, "url_blacklist_invalid"))
        else:
            message.reply_text(tld(chat.id, "url_blacklist_success_2").format(
                len(blacklisted)),
                parse_mode=ParseMode.HTML)
    else:
        message.reply_text(tld(chat.id, "url_blacklist_invalid_2"))


@user_admin
def blacklist_all_url(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args
    conn = connected(update, context, user.id)
    if conn:
        chat_id = conn
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id
    if len(args) >= 1:
        print(args)
        var = args[0]
        if (var == "no" or var == "off"):
            sql.disable_delete_all(chat_id)
            update.effective_message.reply_text(
                tld(chat_id, 'delete_all_disabled'))
        
        elif (var == "yes" or var == "on"):
            sql.enable_delete_all(chat_id)
            update.effective_message.reply_text(
                tld(chat_id, 'delete_all_enabled'))
    
       
        else:
            update.effective_message.reply_text(
                tld(chat_id, 'common_invalid_arg'),
                parse_mode=ParseMode.MARKDOWN)
    else:
        update.effective_message.reply_text(tld(chat_id,
                                                'common_invalid_arg'),
                                            parse_mode=ParseMode.MARKDOWN)


@user_admin
def rm_blacklist_url(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    urls = message.text.split(None, 1)

    if len(urls) > 1:
        urls = urls[1]
        to_unblacklist = list(
            set(uri.strip() for uri in urls.split("\n") if uri.strip()))
        unblacklisted = 0
        for uri in to_unblacklist:
            extract_url = tldextract.extract(uri)
            success = sql.rm_url_from_blacklist(
                chat.id, extract_url.domain + "." + extract_url.suffix)
            if success:
                unblacklisted += 1

        if len(to_unblacklist) == 1:
            if unblacklisted:
                message.reply_text(tld(chat.id,
                                       "url_blacklist_remove_success").format(
                                           html.escape(to_unblacklist[0])),
                                   parse_mode=ParseMode.HTML)
            else:
                message.reply_text(tld(chat.id,
                                       "url_blacklist_remove_invalid"))
        elif unblacklisted == len(to_unblacklist):
            message.reply_text(
                tld(chat.id,
                    "url_blacklist_remove_success_2").format(unblacklisted),
                parse_mode=ParseMode.HTML)
        elif not unblacklisted:
            message.reply_text(tld(chat.id, "url_blacklist_remove_invalid_2"),
                               parse_mode=ParseMode.HTML)
        else:
            message.reply_text(tld(chat.id,
                                   "url_blacklist_remove_success_3").format(
                                       unblacklisted,
                                       len(to_unblacklist) - unblacklisted),
                               parse_mode=ParseMode.HTML)
    else:
        message.reply_text(tld(chat.id, "url_blacklist_remove_invalid_3"))


@user_not_admin
def del_blacklist_url(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    parsed_entities = message.parse_entities(types=["url"])
    if sql.is_delete_all(chat.id):
            return message.delete()
    extracted_domains = []
    for obj, url in parsed_entities.items():
        extract_url = tldextract.extract(url)
        extracted_domains.append(extract_url.domain + "." + extract_url.suffix)
    for url in sql.get_blacklisted_urls(chat.id):
        if url in extracted_domains:
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    logging.error("Error while deleting blacklist message.")
            break


def get_blacklisted_urls(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message

    base_string = tld(chat.id, "url_blacklist_current")
    blacklisted = sql.get_blacklisted_urls(chat.id)

    if not blacklisted:
        message.reply_text(tld(chat.id, "url_blacklist_no_existed"))
        return
    for domain in blacklisted:
        base_string += "- <code>{}</code>\n".format(domain)

    message.reply_text(base_string, parse_mode=ParseMode.HTML)


URL_BLACKLIST_HANDLER = DisableAbleCommandHandler(
    "blacklist",
    add_blacklist_url,
    filters=Filters.chat_type.groups,
    pass_args=True,
    run_async=True,
    admin_ok=True)
ADD_URL_BLACKLIST_HANDLER = CommandHandler("addurl",
                                           add_blacklist_url,
                                           run_async=True,
                                           filters=Filters.chat_type.groups)

RM_BLACKLIST_URL_HANDLER = CommandHandler("delurl",
                                          rm_blacklist_url,
                                          run_async=True,
                                          filters=Filters.chat_type.groups)

GET_BLACKLISTED_URLS = CommandHandler("geturl",
                                      get_blacklisted_urls,
                                      run_async=True,
                                      filters=Filters.chat_type.groups)

BLACKLIST_ALL_URL = CommandHandler("blacklist_all_url",
                                      blacklist_all_url,
                                      run_async=True)

URL_DELETE_HANDLER = MessageHandler(Filters.entity("url"),
                                    del_blacklist_url,
                                    run_async=True)

__help__ = False

CONFIG.dispatcher.add_handler(URL_BLACKLIST_HANDLER)
CONFIG.dispatcher.add_handler(ADD_URL_BLACKLIST_HANDLER)
CONFIG.dispatcher.add_handler(RM_BLACKLIST_URL_HANDLER)
CONFIG.dispatcher.add_handler(GET_BLACKLISTED_URLS)
CONFIG.dispatcher.add_handler(URL_DELETE_HANDLER)
CONFIG.dispatcher.add_handler(BLACKLIST_ALL_URL)
