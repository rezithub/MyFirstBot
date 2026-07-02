import telebot
import json
from telebot import types

TOKEN = "YOUR TOKEN"
bot = telebot.TeleBot(TOKEN)

user_data = {}
support_message_mapping = {}
admins = [7740644517]
users_connections = {}


def load_data():
    global user_data, users_connections
    try:
        with open("users_database.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}

    try:
        with open("connections.json", "r", encoding="utf-8") as f:
            users_connections = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users_connections = {}


def save_user_data():
    with open("users_database.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=4, ensure_ascii=False)


def save_connections():
    with open("connections.json", "w", encoding="utf-8") as f:
        json.dump(users_connections, f, indent=4, ensure_ascii=False)


load_data()

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
register_btn = types.KeyboardButton("Register")
support_btn = types.KeyboardButton("Support")
friend_btn = types.KeyboardButton("Find Friend")
main_markup.row(register_btn, support_btn)
main_markup.row(friend_btn)


@bot.message_handler(commands=["start"])
def first_page(message):
    bot.send_message(
        message.chat.id,
        f"Hi {message.from_user.first_name}, welcome to the Bot!\nPlease choose an option below:",
        reply_markup=main_markup,
    )


@bot.message_handler(
    func=lambda message: message.text in ["Register", "Support", "Find Friend"]
)
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
        back_btn = types.InlineKeyboardButton("back", callback_data="support_back_btn")
        markup.row(back_btn)
        msg = bot.send_message(
            message.chat.id,
            "You are now talking to support. Please type your message:",
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, send_to_support)

    elif message.text == "Find Friend":
        chat_id = str(message.chat.id)
        if (
            users_connections.get(chat_id) != None
            and users_connections.get(chat_id).get("status") == "waiting"
        ):
            markup = types.InlineKeyboardMarkup()
            cancel_find_btn = types.InlineKeyboardButton(
                "Cancel", callback_data="cancel_find_btn"
            )
            markup.row(cancel_find_btn)
            bot.send_message(
                message.chat.id,
                "You are already in the queue , please wait or click cancel:",
                reply_markup=markup,
            )
            return
        if not (chat_id in user_data and "age" in user_data[chat_id]):
            bot.send_message(
                message.chat.id, "Please Register First :)", reply_markup=main_markup
            )
            return
        if (
            chat_id in users_connections
            and users_connections[chat_id].get("status") == "connected"
        ):
            bot.send_message(
                chat_id,
                "You are already in a chat. Please disconnect first.",
                reply_markup=main_markup,
            )
            return

        gender_markup = types.InlineKeyboardMarkup()
        man_btn = types.InlineKeyboardButton("Man", callback_data="man_friend")
        woman_btn = types.InlineKeyboardButton("Woman", callback_data="woman_friend")
        unknown_btn = types.InlineKeyboardButton(
            "Not Important", callback_data="dontcare_friend"
        )
        back_btn = types.InlineKeyboardButton("Back", callback_data="support_back_btn")
        gender_markup.add(man_btn, woman_btn)
        gender_markup.add(unknown_btn)
        gender_markup.add(back_btn)
        bot.send_message(
            message.chat.id,
            "What gender do you want to chat with?",
            reply_markup=gender_markup,
        )


@bot.callback_query_handler(func=lambda call: call.data.endswith("cancel_find_btn"))
def cancel_friend_finding(call):
    chat_id = str(call.message.chat.id)
    if chat_id not in user_data:
        bot.send_message(chat_id, "Session expired")
        return
    users_connections.pop(chat_id)
    bot.answer_callback_query(call.id, text="Cancelling ...", show_alert=False)
    bot.edit_message_text(
        "Process Canceled !", chat_id=chat_id, message_id=call.message.message_id
    )
    bot.send_message(chat_id, "Please choose an option:", reply_markup=main_markup)


@bot.callback_query_handler(func=lambda call: call.data.endswith("_friend"))
def friend_gender_callback(call):
    chat_id = str(call.message.chat.id)
    if chat_id not in user_data:
        bot.send_message(chat_id, "Session expired.")
        return
    bot.answer_callback_query(call.id, text="choosing gender ...", show_alert=False)
    preference = call.data.split("_")[0]
    bot.edit_message_text(
        f"Friends Gender selected: {preference.capitalize()}",
        chat_id=chat_id,
        message_id=call.message.message_id,
    )
    bot.answer_callback_query(call.id)

    users_connections[chat_id] = {"status": "waiting", "preference": preference}
    save_connections()
    bot.send_message(chat_id, "Finding friend, please wait...")

    partner_id = None
    for uid, data in list(users_connections.items()):
        if uid == chat_id:
            continue
        if data.get("status") != "waiting":
            continue

        chooser_gender = user_data[chat_id].get("gender", "unknown")
        chooser_pref = preference
        candidate_gender = user_data[uid].get("gender", "unknown")
        candidate_pref = data.get("preference", "dontcare")

        chooser_accepts = (chooser_pref == "dontcare") or (
            candidate_gender == chooser_pref
        )
        candidate_accepts = (candidate_pref == "dontcare") or (
            chooser_gender == candidate_pref
        )

        if chooser_accepts and candidate_accepts:
            partner_id = uid
            break

    if partner_id is None:
        bot.send_message(
            chat_id, "No one is available right now. You are added to the waiting list."
        )
        return

    users_connections[chat_id] = {"status": "connected", "partner": partner_id}
    users_connections[partner_id] = {"status": "connected", "partner": chat_id}
    save_connections()

    disconnect_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    disconnect_btn = types.KeyboardButton("Disconnect")
    disconnect_markup.row(disconnect_btn)
    bot.send_message(
        chat_id,
        f"Friend Found! Say HI to your friend :)\nFriends Detail:\nname:{user_data[str(partner_id)]["name"]}\nage:{user_data[str(partner_id)]["age"]}\ngender:{user_data[str(partner_id)]["gender"]}",
        reply_markup=disconnect_markup,
    )
    bot.send_message(
        partner_id,
        f"Friend found! Say HI to your friend :)\nFriends Detail:\nname:{user_data[str(chat_id)]["name"]}\nage:{user_data[str(chat_id)]["age"]}\ngender:{user_data[str(chat_id)]["gender"]}",
        reply_markup=disconnect_markup,
    )


@bot.message_handler(func=lambda message: message.text == "Disconnect")
def disconnect(message):
    chat_id = str(message.chat.id)
    if chat_id not in users_connections:
        bot.send_message(chat_id, "You are not in a chat.", reply_markup=main_markup)
        return

    conn = users_connections[chat_id]
    if conn.get("status") != "connected":
        bot.send_message(
            chat_id, "You are not currently connected.", reply_markup=main_markup
        )
        users_connections.pop(chat_id, None)
        save_connections()
        return

    partner_id = conn.get("partner")
    if partner_id and partner_id in users_connections:
        bot.send_message(
            int(partner_id),
            "The chat has been stopped by the other side. Choose from the buttons:",
            reply_markup=main_markup,
        )
        users_connections.pop(partner_id, None)

    users_connections.pop(chat_id, None)
    save_connections()

    bot.send_message(
        chat_id,
        "You stopped the chat. Choose from the buttons:",
        reply_markup=main_markup,
    )


def send_to_support(message):
    user_chat_id = str(message.chat.id)
    for admin_id in admins:
        sent_msg = bot.send_message(
            admin_id,
            f"📩 New support message from user {user_chat_id}:\n\n{message.text}",
        )
        support_message_mapping[sent_msg.message_id] = user_chat_id
    bot.send_message(
        message.chat.id, f"✅ Your message has been sent to support:\n\n{message.text}"
    )


@bot.message_handler(
    func=lambda message: message.chat.id in admins
    and message.reply_to_message is not None
)
def handle_admin_reply(message):
    original_msg = message.reply_to_message
    original_msg_id = original_msg.message_id
    user_chat_id = support_message_mapping.get(original_msg_id)

    if user_chat_id:
        bot.send_message(user_chat_id, f"💬 Support reply:\n\n{message.text}")
        bot.send_message(
            message.chat.id, f"✅ Your reply has been sent to user {user_chat_id}."
        )
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ This message is not from a support request or the user is no longer in the system.",
        )


@bot.callback_query_handler(func=lambda call: call.data == "support_back_btn")
def handle_support_back(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, text="Returning to main menu", show_alert=False)
    bot.edit_message_text(
        "You are back to the main menu.",
        chat_id=chat_id,
        message_id=call.message.message_id,
    )
    bot.send_message(chat_id, "Please choose an option:", reply_markup=main_markup)
    bot.clear_step_handler_by_chat_id(chat_id)


def name_gender_process(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]["name"] = message.text

    gender_markup = types.InlineKeyboardMarkup()
    man_btn = types.InlineKeyboardButton("Man", callback_data="gender_man")
    woman_btn = types.InlineKeyboardButton("Woman", callback_data="gender_woman")
    unknown_btn = types.InlineKeyboardButton(
        "Prefer Not To Say", callback_data="gender_unknown"
    )
    gender_markup.add(man_btn, woman_btn)
    gender_markup.add(unknown_btn)

    bot.send_message(message.chat.id, "Choose your gender:", reply_markup=gender_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender_query(call):
    chat_id = str(call.message.chat.id)
    if chat_id not in user_data:
        bot.send_message(chat_id, "Session expired. Please click 'Register' again.")
        return
    bot.answer_callback_query(call.id, text="choosing gender ...", show_alert=False)
    gender = call.data.split("_")[1]
    user_data[chat_id]["gender"] = gender
    bot.edit_message_text(
        f"Gender selected: {gender.capitalize()}",
        chat_id=chat_id,
        message_id=call.message.message_id,
    )
    bot.answer_callback_query(call.id)

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
    user_data[chat_id]["status"] = "disconnected"
    save_user_data()
    bot.send_message(chat_id, "Registration successful!")


@bot.message_handler(
    func=lambda message: message.text
    not in ["Register", "Support", "Find Friend", "Disconnect"]
)
def users_messages_handler(message):
    chat_id = str(message.chat.id)
    disconnect_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    disconnect_btn = types.KeyboardButton("Disconnect")
    disconnect_markup.row(disconnect_btn)
    if (
        chat_id in users_connections
        and users_connections[chat_id].get("status") == "connected"
    ):
        partner_id = users_connections[chat_id]["partner"]
        bot.send_message(
            partner_id,
            f"Your Friend Sent A message :\n\n{message.text}",
            reply_markup=disconnect_markup,
        )
        bot.send_message(
            message.chat.id, f"Message Sent!", reply_markup=disconnect_markup
        )
    else:
        bot.send_message(message.chat.id, message.text)


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
