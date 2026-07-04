import os
import telebot
import json
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
if TOKEN is None:
    raise ValueError("BOT_TOKEN environment variable not set!")

bot = telebot.TeleBot(TOKEN)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "json"))

user_data = {}
support_message_mapping = {}
admins = []
users_connections = {}
owner_id = 7740644517


def load_data():
    global user_data, users_connections, admins
    try:
        with open(
            os.path.join(JSON_DIR, "users_database.json"), "r", encoding="utf-8"
        ) as f:
            user_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}

    try:
        with open(
            os.path.join(JSON_DIR, "connections.json"), "r", encoding="utf-8"
        ) as f:
            users_connections = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users_connections = {}

    try:
        with open(os.path.join(JSON_DIR, "admins.json"), "r", encoding="utf-8") as f:
            admins = json.load(f).get("admins")
    except (FileNotFoundError, json.JSONDecodeError):
        admins = []


def save_user_data():
    with open(
        os.path.join(JSON_DIR, "users_database.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(user_data, f, indent=4, ensure_ascii=False)


def save_connections():
    with open(os.path.join(JSON_DIR, "connections.json"), "w", encoding="utf-8") as f:
        json.dump(users_connections, f, indent=4, ensure_ascii=False)


def save_admins():
    the_dic = {"admins": admins}
    with open(os.path.join(JSON_DIR, "admins.json"), "w", encoding="utf-8") as f:
        json.dump(the_dic, f, indent=4, ensure_ascii=False)


load_data()

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=False)
register_btn = types.KeyboardButton("Register")
support_btn = types.KeyboardButton("Support")
friend_btn = types.KeyboardButton("Find Friend")
main_markup.row(register_btn, support_btn)
main_markup.row(friend_btn)

main_markup_admin = types.ReplyKeyboardMarkup(resize_keyboard=False)
main_markup_admin.row(register_btn, support_btn)
main_markup_admin.row(friend_btn)
main_markup_admin.row(types.KeyboardButton("Admin Panel"))


admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=False)
send_to_all_btn = types.KeyboardButton("Send To All")
num_of_users_btn = types.KeyboardButton("Number Of Users")
user_profile_btn = types.KeyboardButton("User Profile")
add_admin_btn = types.KeyboardButton("Add Admin")
main_menu_btn = types.KeyboardButton("Main Menu")
admin_markup.add(send_to_all_btn, user_profile_btn)
admin_markup.add(num_of_users_btn, add_admin_btn)
admin_markup.add(main_menu_btn)


@bot.message_handler(func=lambda message: message.text in ["Admin Panel", "/admin"])
def admin_page(message):
    if not message.chat.id in admins:
        bot.send_message(message.chat.id, "unfortunately You are not my admin 🥲")
        return
    bot.send_message(
        message.chat.id,
        f"Welcome To The Admin Panel Dear Admin {message.from_user.first_name} !\n\nID:{message.chat.id}\n\nChoose From The Buttons Below:",
        reply_markup=admin_markup,
    )


@bot.message_handler(
    func=lambda message: message.text
    in ["Send To All", "Number Of Users", "User Profile", "Main Menu", "Add Admin"]
)
def admin_commands(message):
    if message.text == "Send To All":
        msg = bot.send_message(message.chat.id, "Enter The message :")
        bot.register_next_step_handler(msg, send_to_all)
    elif message.text == "Number Of Users":
        num_of_reg = 0
        for userid in user_data:
            if user_data.get(userid) != {}:
                num_of_reg += 1
        bot.send_message(
            message.chat.id,
            f"Number Of Total Users: {len(user_data)}\nNumber Of Registred Users: {num_of_reg}\nNumber Of Unregistred Users: {len(user_data)-num_of_reg}",
        )
    elif message.text == "User Profile":
        profile_markup = types.InlineKeyboardMarkup()
        all_IDs_btn = types.InlineKeyboardButton(
            "ALL USERS", callback_data="all_ids_profile"
        )
        special_user_profile = types.InlineKeyboardButton(
            "SPECIAL USER", callback_data="special_user_profile"
        )
        back_user_profile = types.InlineKeyboardButton(
            "BACK", callback_data="back_profile"
        )
        profile_markup.row(all_IDs_btn, special_user_profile)
        profile_markup.row(back_user_profile)
        msg = bot.send_message(
            message.chat.id,
            "Choose One Of Them :\n\nDescription :\nALL USER : it will show all users ids\nSPECIAL USER:it will send all of the specified users detailes by id",
            reply_markup=profile_markup,
        )
    elif message.text == "Main Menu":
        if message.chat.id in admins:
            bot.send_message(
                message.chat.id,
                f"Hi Admin {message.from_user.first_name}, welcome to your Bot!\nPlease choose an option below:",
                reply_markup=main_markup_admin,
            )
            return
        bot.send_message(
            message.chat.id,
            "welcome back to the main menu".capitalize(),
            reply_markup=main_markup,
        )
    elif message.text == "Add Admin":
        if message.chat.id != owner_id:
            bot.send_message(
                message.chat.id,
                "you are not the owner:)".capitalize(),
                reply_markup=admin_markup,
            )
            return
        back_markup = types.InlineKeyboardMarkup()
        back_user_profile = types.InlineKeyboardButton(
            "BACK", callback_data="back_profile"
        )
        back_markup.row(back_user_profile)
        msg = bot.send_message(
            message.chat.id, "enter the id : ".capitalize(), reply_markup=back_markup
        )
        bot.register_next_step_handler(msg, add_admin)

    else:
        bot.send_message(message.chat.id, message.text)


def add_admin(message):
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "Please Enter A Number Like 800000000:")
        bot.register_next_step_handler(msg, show_user_profile)
        return
    if not str(message.text) in user_data:
        bot.send_message(
            message.chat.id,
            f"User {message.text} Is Not In The Bot",
            reply_markup=admin_markup,
        )
        return
    admins.append(int(message.text))
    bot.send_message(
        message.chat.id,
        f"Admin {message.text} Added Successfully !",
        reply_markup=admin_markup,
    )
    bot.send_message(
        int(message.text),
        "the owner promote you to admin !\n\nyou are now my admin:)\nuse admin buttons below:",
        reply_markup=admin_markup,
    )
    save_admins()


def send_to_all(message):
    for user_id in user_data:
        bot.send_message(
            user_id,
            f"This Is A Public Message From Admin{message.chat.id}:\n\n{message.text}",
        )
    bot.send_message(message.chat.id, f"Message Sent To All Users:)")


@bot.callback_query_handler(func=lambda call: call.data.endswith("_profile"))
def users_profile_handle(call):
    profile_type = call.data.split("_")[0]
    bot.answer_callback_query(call.id, text="Ok", show_alert=False)
    bot.edit_message_text(
        f"SELECTED : {call.data}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
    )
    if profile_type == "all":
        all_profile = "ALL USER IDS WITH NAMES :"
        registred_users = "\nRegistred Users:\n"
        unregistred_users = "\nUnregistred Users:\n"
        for userid in user_data:
            if user_data.get(userid) == {}:
                unregistred_users += str(userid) + "\n"
                continue
            registred_users += (
                str(userid) + " : " + user_data.get(userid).get("name") + "\n"
            )
        all_profile += registred_users + unregistred_users
        bot.send_message(call.message.chat.id, all_profile)
    elif profile_type == "special":
        msg = bot.send_message(call.message.chat.id, "Enter The ID:")
        bot.register_next_step_handler(msg, show_user_profile)
    elif profile_type == "back":
        bot.edit_message_text(
            "OK!", chat_id=call.message.chat.id, message_id=call.message.message_id
        )
        bot.send_message(
            call.message.chat.id,
            "Welcome Back To The Admin Menu :",
            reply_markup=admin_markup,
        )


def show_user_profile(message):
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "Please Enter A Number Like 800000000:")
        bot.register_next_step_handler(msg, show_user_profile)
        return
    if not str(message.text) in user_data:
        bot.send_message(
            message.chat.id,
            f"User {message.text} Is Not In The Bot",
            reply_markup=admin_markup,
        )
        return
    if user_data.get(str(message.text)) == None:
        bot.send_message(
            message.chat.id,
            f"User {message.text} Is Not Registred Yet",
            reply_markup=admin_markup,
        )
        return
    bot.send_message(
        message.chat.id,
        f"Requested User ID:{message.text}\n\nName:{user_data.get(str(message.text)).get('name')}\nAge:{user_data.get(str(message.text)).get('age')}\nGender:{user_data.get(str(message.text)).get('gender')}",
    )


@bot.message_handler(commands=["start"])
def first_page(message):
    chat_id = str(message.chat.id)
    if user_data.get(chat_id) == None:
        user_data[chat_id] = {}
    if int(chat_id) in admins:
        bot.send_message(
            message.chat.id,
            f"Hi Admin {message.from_user.first_name}, welcome to your Bot!\nPlease choose an option below:",
            reply_markup=main_markup_admin,
        )
        return
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
        if chat_id not in user_data:
            user_data[chat_id] = {}
        if "age" in user_data[chat_id]:
            bot.send_message(message.chat.id, "You have already registered.")
            return
        markup = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton(
            "Cancel", callback_data="support_back_btn"
        )
        markup.row(back_btn)
        msg = bot.send_message(chat_id, "Enter your name:", reply_markup=markup)
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
            if int(chat_id) in admins:
                bot.send_message(
                    int(chat_id),
                   "Please Register First :)",
                    reply_markup=main_markup_admin,
                )
                return
            bot.send_message(
                message.chat.id, "Please Register First :)", reply_markup=main_markup
            )
            return
        if (
            chat_id in users_connections
            and users_connections[chat_id].get("status") == "connected"
        ):
            if int(chat_id) in admins:
                bot.send_message(
                    int(chat_id),
                    "You are already in a chat. Please disconnect first.",
                    reply_markup=main_markup_admin,
                )
                return
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
    if int(chat_id) in admins:
        bot.send_message(
            int(chat_id),
            "Please choose an option:",
            reply_markup=main_markup_admin,
        )
        return
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
        f"Friend Found! Say HI to your friend :)\nFriends Detail:\nname:{user_data[str(partner_id)]['name']}\nage:{user_data[str(partner_id)]['age']}\ngender:{user_data[str(partner_id)]['gender']}",
        reply_markup=disconnect_markup,
    )
    bot.send_message(
        partner_id,
        f"Friend found! Say HI to your friend :)\nFriends Detail:\nname:{user_data[str(chat_id)]['name']}\nage:{user_data[str(chat_id)]['age']}\ngender:{user_data[str(chat_id)]['gender']}",
        reply_markup=disconnect_markup,
    )


@bot.message_handler(func=lambda message: message.text == "Disconnect")
def disconnect(message):
    chat_id = str(message.chat.id)
    if chat_id not in users_connections:
        if int(chat_id) in admins:
            bot.send_message(
                int(chat_id),
                "You are not in a chat.",
                reply_markup=main_markup_admin,
            )
            return
        bot.send_message(chat_id, "You are not in a chat.", reply_markup=main_markup)
        return

    conn = users_connections[chat_id]
    if conn.get("status") != "connected":
        if int(chat_id) in admins:
            bot.send_message(
                int(chat_id),
                "You are not currently connected.",
                reply_markup=main_markup_admin,
            )
            return
        bot.send_message(
            chat_id, "You are not currently connected.", reply_markup=main_markup
        )
        users_connections.pop(chat_id, None)
        save_connections()
        return

    partner_id = conn.get("partner")
    if partner_id and partner_id in users_connections:
        if int(chat_id) in admins:
            bot.send_message(
                int(chat_id),
                "The chat has been stopped by the other side. Choose from the buttons:",
                reply_markup=main_markup_admin,
            )
            return
        bot.send_message(
            int(partner_id),
            "The chat has been stopped by the other side. Choose from the buttons:",
            reply_markup=main_markup,
        )
        users_connections.pop(partner_id, None)

    users_connections.pop(chat_id, None)
    save_connections()
    if int(chat_id) in admins:
        bot.send_message(
            int(chat_id),
            "You stopped the chat. Choose from the buttons:",
            reply_markup=main_markup_admin,
        )
        return
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
        bot.send_message(
            user_chat_id,
            f"💬 Support reply:\n\n{message.text}\n\nIf you need more help click on support button!",
        )
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
    global user_data
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id, text="Returning to main menu", show_alert=False)
    bot.edit_message_text(
        "You are back to the main menu.",
        chat_id=chat_id,
        message_id=call.message.message_id,
    )
    if int(call.message.chat.id) in admins:
        bot.send_message(
            call.message.chat.id,
            f"Hi Admin {call.message.from_user.first_name}, welcome to your Bot!\nPlease choose an option below:",
            reply_markup=main_markup_admin,
        )
        return
    bot.send_message(chat_id, "Please choose an option:", reply_markup=main_markup)
    bot.clear_step_handler_by_chat_id(chat_id)
    try:
        with open(
            os.path.join(JSON_DIR, "users_database.json"), "r", encoding="utf-8"
        ) as f:
            user_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}


def name_gender_process(message):
    chat_id = str(message.chat.id)
    user_data[chat_id]["name"] = message.text

    gender_markup = types.InlineKeyboardMarkup()
    man_btn = types.InlineKeyboardButton("Man", callback_data="gender_man")
    woman_btn = types.InlineKeyboardButton("Woman", callback_data="gender_woman")
    unknown_btn = types.InlineKeyboardButton(
        "Prefer Not To Say", callback_data="gender_unknown"
    )
    back_btn = types.InlineKeyboardButton("Cancel", callback_data="support_back_btn")
    gender_markup.add(man_btn, woman_btn)
    gender_markup.add(unknown_btn)
    gender_markup.add(back_btn)
    bot.send_message(message.chat.id, "Choose your gender:", reply_markup=gender_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender_query(call):
    chat_id = str(call.message.chat.id)
    if chat_id not in user_data:
        bot.send_message(chat_id, "Session expired. Please Try Again.")
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
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton("Cancel", callback_data="support_back_btn")
    markup.row(back_btn)
    msg = bot.send_message(chat_id, "Enter your age:", reply_markup=markup)
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


def start_bot():
    bot.infinity_polling()
