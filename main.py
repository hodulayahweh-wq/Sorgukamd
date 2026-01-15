#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
import asyncio
import sys
import os
import threading
import subprocess
from datetime import datetime
from flask import Flask
import telebot # Kolay yönetim için telebot, ağır işler için diğer kütüphaneleri kullanabilirsin

# --- RENDER KEEPALIVE & WEB SERVER ---
app = Flask(__name__)
@app.route('/')
def health(): return "Titan System Active", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFİGÜRASYON ---
TOKEN = "8539846290:AAGimtN1IhpGW8m1ZitjZjl07TJDXRt9O2A"
ADMIN_ID =7970588822 # Senin Telegram ID'n
bot = telebot.TeleBot(TOKEN)

# Çalışan alt süreçleri takip etmek için
running_bots = {} 

# --- LOGGING AYARI ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- ADMİN FONKSİYONLARI ---

@bot.message_handler(commands=['start'])
def welcome(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu panel sadece sahibime özeldir sevgilim.")
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📂 Botları Listele", "🛑 Tümünü Durdur")
    bot.reply_to(message, "🌟 **Hoş geldin Sahibi!**\nSistemi yönetmeye hazırım. Bana bir `.py` dosyası atarsan onu anında mermi gibi çalıştırırım.", reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_bot_upload(message):
    if message.from_user.id != ADMIN_ID: return

    doc = message.document
    if not doc.file_name.endswith('.py'):
        bot.reply_to(message, "⚠️ Sadece `.py` dosyalarını kabul ediyorum sevgilim.")
        return

    # Dosyayı indir ve kaydet
    file_info = bot.get_file(doc.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    file_path = os.path.join(os.getcwd(), doc.file_name)
    with open(file_path, 'wb') as f:
        f.write(downloaded)

    # Botu başlat
    try:
        # Alt süreci başlat (Subprocess)
        proc = subprocess.Popen([sys.executable, file_path])
        running_bots[doc.file_name] = proc
        bot.reply_to(message, f"✅ `{doc.file_name}` mermi gibi başlatıldı!\n🚀 PID: `{proc.pid}`")
    except Exception as e:
        bot.reply_to(message, f"🚨 Başlatma hatası: {e}")

@bot.message_handler(func=lambda m: m.text == "📂 Botları Listele")
def list_bots(message):
    if not running_bots:
        bot.reply_to(message, "Şu an çalışan ek bir bot yok sevgilim.")
        return
    
    liste = "🏃 **Çalışan Botlar:**\n"
    for name, proc in running_bots.items():
        status = "🟢 Çalışıyor" if proc.poll() is None else "🔴 Durdu"
        liste += f"- `{name}` ({status})\n"
    bot.reply_to(message, liste, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛑 Tümünü Durdur")
def stop_all(message):
    if message.from_user.id != ADMIN_ID: return
    for name, proc in running_bots.items():
        proc.terminate()
    running_bots.clear()
    bot.reply_to(message, "🧨 Tüm alt botlar durduruldu sevgilim!")

# --- ANA DÖNGÜ ---
if __name__ == "__main__":
    # Render'ı uyanık tutmak için Flask thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("🚀 Titan Sistemi Render üzerinde başlatıldı...")
    bot.infinity_polling()
