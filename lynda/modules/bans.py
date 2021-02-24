import html
from typing import List

from telegram import Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, run_async, CallbackContext
from telegram.utils.helpers import mention_html

from lynda import dispatcher, LOGGER, DEV_USERS, SUDO_USERS, SARDEGNA_USERS, BAN_STICKER
from lynda.modules.disable import DisableAbleCommandHandler
from lynda.modules.helper_funcs.chat_status import (
    bot_admin,
    user_admin,
    is_user_ban_protected,
    can_restrict,
    is_user_admin,
    is_user_in_chat,
    connection_status)
from lynda.modules.helper_funcs.extraction import extract_user_and_text
from lynda.modules.helper_funcs.string_handling import extract_time
from lynda.modules.log_channel import loggable, gloggable


@run_async
def banme(update: Update, context: CallbackContext):
    message = update.effective_message
    if is_user_admin(update.effective_chat, update.effective_message.from_user.id):
        update.effective_message.reply_text("Ya lu gabisa ban admin bego.")
        return
    try:
        context.bot.kick_chat_member(update.effective_chat.id, update.effective_message.from_user.id)
        context.bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        response_message = "Kebanyakan di ban cok"
    except Exception as e:
        print(e)
        response_message = "Ohno! something is not right please contact @LyndaEagleSupport"
    message.reply_text(response_message)


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    user_id, reason = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text("Gw ngira dia user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User ngak ada":
            message.reply_text("Gk bisa diliat ni user.")
            return log_message
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("Tolo malah ban diri sendiri")
        return log_message

    # dev users to bypass whitelist protection incase of abuse
    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        message.reply_text("Dia immortal cok gabisa diban")
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#Yahahahha hayuk kena ban ya\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Pengguma:</b> {mention_html(member.user.id, member.user.first_name)}")
    if reason:
        log += "\n<b>Alasan nya:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            "Banned user {}.".format(
                mention_html(
                    member.user.id,
                    member.user.first_name)),
            parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Balas pesan lagi error":
            # Do not reply
            message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR pas ban orang %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message)
            message.reply_text("Gak bisa cok...")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Gw ngira dia user")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Nggk bisa cari user nya")
            return log_message
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("Tolo mana bisa gw ban diri gw sendiri")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Gw gasuka itu ya tod")
        return log_message

    if not reason:
        message.reply_text(
            "Lu gk spesifik nge ban")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#Ciee kena ban, ngk bisa masuk dulu sementara\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Pengguna:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Waktu:</b> {time_val}")
    if reason:
        log += "\n<b>Alasan nya:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            f"Acieee kena banned {mention_html(member.user.id, member.user.first_name)} "
            f"Kena ban sampe {time_val}.",
            parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Pesan gak ada":
            # Do not reply
            message.reply_text(
                f"Kena ban sampe {time_val}.",
                quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR gk bisa ban %s in chat %s (%s) due to %s",
                            user_id, chat.title, chat.id, excp.message)
            message.reply_text("Gk bisa diban bjir.")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return log_message
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("Yeahhh I'm not gonna do that.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text(
            "I really wish I could put the ban tag on this user....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            f"Gunned Out! {mention_html(member.user.id, member.user.first_name)}.",
            parse_mode=ParseMode.HTML)
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        message.reply_text("Well damn, I can't shoot that user.")

    return log_message


@run_async
@bot_admin
@can_restrict
def kickme(update: Update, _):
    message = update.effective_message
    user_id = message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        message.reply_text(
            "I wish I could... but you're an admin.")
        return

    res = update.effective_chat.unban_member(
        user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("No problem.")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return log_message
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("How would I unban myself if I wasn't here...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("Isn't this person already here??")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("Yep, this user can join!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    return log


@run_async
@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if user.id not in SUDO_USERS or user.id not in SARDEGNA_USERS:
        return

    try:
        chat_id = int(args[0])
    except Exception as e:
        print(e)
        message.reply_text("Give a valid chat ID.")
        return

    chat = context.bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("Aren't you already in the chat??")
        return

    chat.unban_member(user.id)
    message.reply_text("Yep, I have unbanned you.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")

    return log


__help__ = """
-> `/kickme`: kicks the user who issued the command

──「 *Admin only:* 」──
-> `/ban` <userhandle>
bans a user. (via handle, or reply)
-> `/tban` <userhandle> x(m/h/d)
bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
-> `/unban` <userhandle>
unbans a user. (via handle, or reply)
-> `/kick` <userhandle>
kickes a user out of the group, (via handle, or reply)
"""

BANME_HANDLER = DisableAbleCommandHandler(
    "banme", banme, filters=Filters.group)
BAN_HANDLER = CommandHandler("ban", ban, pass_args=True)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True)
ROAR_HANDLER = CommandHandler("roar", selfunban, pass_args=True)
KICKME_HANDLER = DisableAbleCommandHandler(
    "kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)

__mod_name__ = "Bans"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    KICK_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    KICKME_HANDLER,
    BANME_HANDLER]
