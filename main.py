import telebot
import json
from telebot import types

TOKEN = "THE TOKEN"
bot = telebot.TeleBot(TOKEN)

# Global data structures
user_data = {}                 # stores registered users
support_message_mapping = {}   # maps forwarded message IDs to original user chat IDs
admins = [7740644517]          # list of admin user IDs

# Load existing user data
try:
    with open('users_database.json', 'r') as file:
        user_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    user_data = {}

def save_data():
    with open('users_database.json', 'w') as file:
        json.dump(user_data, file, indent=4, ensure_ascii=False)

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
register_btn = types.KeyboardButton("Register")
support_btn = types.KeyboardButton("Support")
main_markup.row(register_btn, support_btn)

# ---------- START ----------
@bot.message_handler(commands=["start"])
def first_page(message):
    bot.send_message(
        message.chat.id,
        f"Hi {message.from_user.first_name}, welcome to the Bot!\nPlease choose an option below:",
        reply_markup=main_markup
    )

# ---------- MAIN MENU HANDLER ----------
@bot.message_handler(func=lambda message: message.text in ['Register', 'Support'])
def answer_request(message):
    if message.text == "Register":
        chat_id = str(message.chat.id)
        if chat_id in user_data and "age" in user_data[chat_id]:
            bot.send_message(message.chat.id, "You have already registered.")
            return
        user_data[chat_id] = {} 
        msg = bot.send_message(chat_id, "Enter your name:")
        bot.register_next_step_handler(msg, name_gender_process)

    elif message.text == "Support":
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("Back", callback_data="support_back_btn")
        markup.row(back_btn)
        msg = bot.send_message(
            message.chat.id,
            "You are now talking to support. Please type your message:",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, send_to_support)

# ---------- SUPPORT MESSAGE FORWARDING ----------
def send_to_support(message):
    user_chat_id = str(message.chat.id)
    for admin_id in admins:
        sent_msg = bot.send_message(
            admin_id,
            f"📩 New support message from user {user_chat_id}:\n\n{message.text}"
        )
        support_message_mapping[sent_msg.message_id] = user_chat_id
    bot.send_message(
        message.chat.id,
        f"✅ Your message has been sent to support:\n\n{message.text}"
    )

# ---------- ADMIN REPLY HANDLER (when admin replies to a forwarded message) ----------
@bot.message_handler(func=lambda message: message.chat.id in admins and message.reply_to_message is not None)
def handle_admin_reply(message):
    original_msg = message.reply_to_message
    original_msg_id = original_msg.message_id
    user_chat_id = support_message_mapping.get(original_msg_id)

    if user_chat_id:
        bot.send_message(
            user_chat_id,
            f"💬 Support reply :\n\n{message.text}"
        )
        bot.send_message(
            message.chat.id,
            f"✅ Your reply has been sent to user {user_chat_id}."
        )
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ This message is not from a support request or the user is no longer in the system."
        )

# ---------- BACK BUTTON CALLBACK ----------
@bot.callback_query_handler(func=lambda call: call.data == "support_back_btn")
def handle_support_back(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, text="Returning to main menu", show_alert=False)
    bot.edit_message_text(
        "You are back to the main menu.",
        chat_id=chat_id,
        message_id=call.message.message_id
    )
    bot.send_message(
        chat_id,
        "Please choose an option:",
        reply_markup=main_markup
    )
    bot.clear_step_handler_by_chat_id(chat_id)

# ---------- REGISTRATION FLOW ----------
def name_gender_process(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]["name"] = message.text

    gender_markup = types.InlineKeyboardMarkup()
    man_btn = types.InlineKeyboardButton("Man", callback_data="gender_man")
    woman_btn = types.InlineKeyboardButton("Woman", callback_data="gender_woman")
    unknown_btn = types.InlineKeyboardButton("Prefer Not To Say", callback_data="gender_unknown")
    gender_markup.add(man_btn, woman_btn)
    gender_markup.add(unknown_btn)

    bot.send_message(message.chat.id, "Choose your gender:", reply_markup=gender_markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender_query(call):
    chat_id = str(call.message.chat.id)
    if chat_id not in user_data:
        bot.send_message(chat_id, "Session expired. Please click 'Register' again.")
        return

    gender = call.data.split("_")[1]
    user_data[chat_id]["gender"] = gender

    bot.edit_message_text(
        f"Gender selected: {gender.capitalize()}",
        chat_id=chat_id,
        message_id=call.message.message_id
    )

    msg = bot.send_message(chat_id, "Enter your age:")
    bot.register_next_step_handler(msg, age_process)

def age_process(message):
    chat_id = str(message.chat.id)
    age = message.text
    if not age.isdigit():
        msg = bot.send_message(chat_id, "Invalid age! Please enter a number:")
        bot.register_next_step_handler(msg, age_process)
        return

    user_data[chat_id]["age"] = age
    save_data()
    bot.send_message(chat_id, "Registration successful!")

if __name__ == "__main__":
    bot.infinity_polling()
