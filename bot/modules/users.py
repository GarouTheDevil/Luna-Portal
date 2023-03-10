from telegram import Update
from pymongo import MongoClient
from telegram.ext import CommandHandler

from bot import app, OWNER_ID, DATABASE_URL, dispatcher
from bot.helper.telegram_helper.filters import CustomFilters

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Set dc_info in bot_data
    dc_info = updater.bot.get_me().dc_info
    updater.bot_data['dc_info'] = dc_info
    
    dp.add_handler(CommandHandler("info", info))
    
    updater.start_polling()
    updater.idle()


def info(update, context):
    chat = update.effective_chat
    dc_info = context.bot_data['dc_info']
    
    if context.args:
        try:
            user_id = int(context.args[0])
            user = context.bot.get_chat(user_id)
        except ValueError:
            username = context.args[0].replace("@", "")
            user = context.bot.get_chat(username=username)
    else:
        if update.message.reply_to_message:
            user = update.message.reply_to_message.from_user
        else:
            user = chat
    
    if user.type == telegram.Chat.PRIVATE:
        profile_photo = context.bot.get_user_profile_photos(user.id).photos[-1][-1] if context.bot.get_user_profile_photos(user.id).photos else None
        profile_link = f"https://t.me/{user.username}" if user.username else None
        message = f"Your username is {user.username} and your ID is {user.id}. \n\n" if user == chat else ""
    else:
        profile_photo = None
        profile_link = None
        message = f"This is the {user.title} group and the group ID is {user.id}. \n\n" if user == chat else ""
    
    message += f"Current DC information: \n" \
              f"DC ID: {dc_info.id}\n" \
              f"DC IP Address: {dc_info.ip_address}\n" \
              f"DC Port: {dc_info.port}\n\n"
    
    if profile_photo:
        context.bot.send_photo(chat_id=chat.id, photo=profile_photo)

    if profile_link:
        message += f"Your permanent link is {profile_link}."
    
    update.message.send_message(message)


def dbusers(update, context):
    if not DATABASE_URL:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"DATABASE_URL not provided")
    else:
        client = MongoClient(DATABASE_URL)
        db = client["mltb"]
        count = db.users.count_documents({})
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Total users in database: {count}")


def get_id(update: Update, context):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == 'private':
        user_id = update.message.from_user.id
        context.bot.send_message(chat_id=user_id, text=f"Your user ID is: <code>{user_id}</code>")
    else:
        context.bot.send_message(chat_id=chat_id, text=f"This group's ID is: <code>{chat_id}</code>")

info_handler = CommandHandler("info", info, filters=CustomFilters.owner_filter | CustomFilters.sudo_user)
dbusers_handler = CommandHandler("dbusers", dbusers, filters=CustomFilters.owner_filter | CustomFilters.sudo_user)
id_handler = CommandHandler("id", get_id)

dispatcher.add_handler(dbusers_handler)
dispatcher.add_handler(id_handler)
dispatcher.add_handler(info_handler)
