import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types

# ================= CONFIG =================

TOKEN = "8294124416:AAEzx1Wh0AG5E_APmZGNQZklhy6ZdfDiyh4"
ADMINS = [6883454411, 7972510810]  # admin telegram IDs
DATA_FILE = "data.json"

# ==========================================

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =============== JSON HELPERS ==============

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": [],
            "requests": [],
            "admins": ADMINS
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =============== TIME CHECK ================

def bot_on():
    hour = datetime.now().hour
    return 11 <= hour < 23

# =============== START =====================

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.reply("🤖 APK Exchange Bot Ready\nSend APK file.")

# ============ APK RECEIVE ==================

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def receive_apk(msg: types.Message):
    data = load_data()

    uid = msg.from_user.id
    file_id = msg.document.file_id

    if uid not in data["users"]:
        data["users"].append(uid)

    req_id = len(data["requests"]) + 1

    data["requests"].append({
        "req_id": req_id,
        "user_id": uid,
        "file_id": file_id,
        "status": "pending",
        "time": str(datetime.now())
    })

    save_data(data)

    for admin in data["admins"]:
        await bot.send_document(
            admin,
            file_id,
            caption=f"📦 New APK\nUserID: {uid}\nReqID: {req_id}"
        )

    if bot_on():
        await msg.reply("✅ APK submit ho gaya")
    else:
        await msg.reply("⛔ Bot OFF hai\nAPK submit ho gaya — subah milega")

# ============ ADMIN SEND APK ================

@dp.message_handler(commands=["send"])
async def send_apk(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    args = msg.text.split()
    if len(args) != 3:
        await msg.reply("Usage:\n/send <req_id> <file_id>")
        return

    req_id = int(args[1])
    new_file_id = args[2]

    data = load_data()
    req = next((r for r in data["requests"] if r["req_id"] == req_id), None)

    if not req:
        await msg.reply("❌ Invalid ReqID")
        return

    await bot.send_document(
        req["user_id"],
        new_file_id,
        caption="🎯 Your APK is ready"
    )

    req["status"] = "done"
    save_data(data)

    await msg.reply("✅ APK sent to correct user")

# ============ ADMIN BROADCAST ===============

@dp.message_handler(commands=["broadcast"])
async def broadcast(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    text = msg.text.replace("/broadcast", "").strip()
    if not text:
        await msg.reply("❌ Message missing")
        return

    data = load_data()
    count = 0

    for u in data["users"]:
        try:
            await bot.send_message(u, text)
            count += 1
        except:
            pass

    await msg.reply(f"📢 Broadcast sent to {count} users")

# ============ DASHBOARD =====================

@dp.message_handler(commands=["stats"])
async def stats(msg: types.Message):
    if msg.from_user.id not in ADMINS:
        return

    data = load_data()
    total_users = len(data["users"])
    pending = len([r for r in data["requests"] if r["status"] == "pending"])
    done = len([r for r in data["requests"] if r["status"] == "done"])

    await msg.reply(
        f"📊 BOT STATS\n"
        f"Users: {total_users}\n"
        f"Pending APKs: {pending}\n"
        f"Completed: {done}"
    )

# ============ RUN ===========================

if __name__ == "__main__":
    print("Bot started...")
    executor.start_polling(dp, skip_updates=True)