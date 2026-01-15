# -*- coding: utf-8 -*-
import telebot
import subprocess
import os
import threading
import sys
import time
import logging
from flask import Flask

# ────────────────────────────────────────────────
#                  RENDER.COM AYARI (FLASK)
# ────────────────────────────────────────────────
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running on Render!", 200

# Render'ın portunu yakalıyoruz
PORT = int(os.environ.get("PORT", 10000))

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ────────────────────────────────────────────────
#                  BOT AYARLARI
# ────────────────────────────────────────────────
TOKEN = '8539846290:AAGVJJtCnGcfFwOl7uS5eZFQyDrKUHig_3Q'
ADMIN_ID = -1003661302600  # Senin ID'n
bot = telebot.TeleBot(TOKEN)

# Dosyaların saklanacağı yer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOTS_DIR = os.path.join(BASE_DIR, 'user_bots')
os.makedirs(BOTS_DIR, exist_ok=True)

# Çalışan botları takip etmek için
active_processes = {}

logging.basicConfig(level=logging.INFO)

# ────────────────────────────────────────────────
#             DOSYA ÇALIŞTIRMA MANTIĞI
# ────────────────────────────────────────────────

def run_user_bot(path, uid, filename):
    key = f"{uid}_{filename}"
    log_file = open(f"{path}.log", "w")
    
    try:
        # Alt işlemi başlat (Python botu)
        proc = subprocess.Popen(
            [sys.executable, path],
            stdout=log_file,
            stderr=log_file,
            text=True
        )
        active_processes[key] = proc
        bot.send_message(uid, f"✅ `{filename}` başarıyla başlatıldı!\n🚀 Durum: **Çalışıyor**", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(uid, f"❌ Başlatma hatası: {e}")

# ────────────────────────────────────────────────
#             BOT MESAJ İŞLEYİCİLERİ
# ────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🌟 **Host Botuna Hoş Geldin Sevgilim!**\n\nBana bir `.py` dosyası at, senin yerine 7/24 çalıştırayım.")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    uid = message.from_user.id
    doc = message.document
    
    if not doc.file_name.endswith('.py'):
        bot.reply_to(message, "⚠️ Sadece `.py` dosyalarını çalıştırabilirim sevgilim.")
        return

    # Dosyayı indir
    msg = bot.reply_to(message, "📥 Dosya alınıyor ve sunucuya kuruluyor...")
    
    file_info = bot.get_file(doc.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    user_folder = os.path.join(BOTS_DIR, str(uid))
    os.makedirs(user_folder, exist_ok=True)
    
    file_path = os.path.join(user_folder, doc.file_name)
    
    with open(file_path, 'wb') as f:
        f.write(downloaded_file)
    
    bot.edit_message_text("⚙️ **Dosya yüklendi, kütüphaneler kontrol ediliyor ve başlatılıyor...**", uid, msg.message_id)
    
    # Botu ayrı bir thread'de çalıştır (Ana bot donmasın)
    threading.Thread(target=run_user_bot, args=(file_path, uid, doc.file_name)).start()

# ────────────────────────────────────────────────
#                ANA ÇALIŞTIRICI
# ────────────────────────────────────────────────

if __name__ == '__main__':
    # Flask'ı arka planda başlat (Render'ın kapanmaması için)
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print(f"🚀 Host Botu ve Web Sunucusu (Port: {PORT}) Aktif!")
    
    # Telegram Polling
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            time.sleep(5)
