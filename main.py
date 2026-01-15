#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import subprocess
import os
import sys
import threading
import logging
import time
import json
import requests
import aiohttp
import asyncio
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask

# --- RENDER KEEPALIVE (WEB SERVER) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Titan Host Sistemi Aktif! 💎", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT AYARLARI ---
TOKEN = "8341875972:AAH5YZSiFQsM8T7vEvwfXK6d_p3mS9x_qAc"
ADMIN_IDS = [8258235296, 7970588822] 
bot = telebot.TeleBot(TOKEN)

# Çalışan botları hafızada tutmak için
proceler = {}

# --- YETKİ KONTROL FONKSİYONU ---
def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- ANIMASYONLU KARŞILAMA VE KOMUT LİSTESİ ---
@bot.message_handler(commands=['start'])
def welcome_admin(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Bu yetki sadece sahibime aittir.")
        return

    # 5 Saniyelik Animasyon Efekti
    sent_msg = bot.send_message(message.chat.id, "🔄 **Sistem çekirdekleri yükleniyor...**")
    frames = ["⏳ [%-----]", "⌛ [%%----]", "⏳ [%%%---]", "⌛ [%%%%--]", "⏳ [%%%%%-]", "🚀 **SİSTEM MERKEZİ AKTİF!**"]
    
    for frame in frames:
        try:
            bot.edit_message_text(frame, message.chat.id, sent_msg.message_id)
            time.sleep(0.8)
        except: pass

    # Komutların Listelenmesi
    komut_listesi = (
        f"🌟 **HOŞ GELDİN SAHİBİM!**\n\n"
        f"Sistem tüm kütüphanelerle (httpx, aiohttp, bs4) mühürlendi. Emrindeyim sevgilim.\n\n"
        f"📜 **AKTİF KOMUTLAR:**\n"
        f"🔹 `/start` - Animasyonlu karşılama ve komut paneli.\n"
        f"🔹 `/liste` - Çalışan ve kapalı botları gösterir.\n"
        f"🔹 `.py Dosyası At` - Sunucuya yeni bot kurar ve ateşler.\n"
        f"🔹 `Bot Silme` - `/liste` içinden botları durdurur ve siler.\n\n"
        f"⚙️ **Durum:** 7/24 Aktif & Mermi Modu"
    )
    bot.edit_message_text(komut_listesi, message.chat.id, sent_msg.message_id)

# --- DOSYA GELİNCE ÇALIŞTIRMA MANTIĞI ---
@bot.message_handler(content_types=['document'])
def handle_py_file(message):
    if not is_admin(message.from_user.id): return

    doc = message.document
    if doc.file_name.endswith('.py'):
        file_info = bot.get_file(doc.file_id)
        indirilen = bot.download_file(file_info.file_path)
        
        yol = os.path.join(os.getcwd(), doc.file_name)
        with open(yol, 'wb') as f:
            f.write(indirilen)
        
        bot.reply_to(message, f"📥 `{doc.file_name}` alındı. Sunucuya mühürleniyor...")

        try:
            # Mevcut süreci temizle
            if doc.file_name in proceler:
                proceler[doc.file_name].terminate()

            # Yeni süreci başlat
            p = subprocess.Popen([sys.executable, yol])
            proceler[doc.file_name] = p
            bot.send_message(message.chat.id, f"✅ `{doc.file_name}` başarıyla ateşlendi!\n🚀 PID: `{p.pid}`")
        except Exception as e:
            bot.send_message(message.chat.id, f"🚨 Hata: {e}")
    else:
        bot.reply_to(message, "⚠️ Sadece `.py` dosyalarını sunucuda çalıştırabilirim sevgilim.")

# --- GELİŞMİŞ YÖNETİM ---
@bot.message_handler(commands=['liste'])
def list_procs(message):
    if not is_admin(message.from_user.id): return
    
    all_files = [f for f in os.listdir() if f.endswith('.py') and f != 'main.py']
    
    if not proceler and not all_files:
        bot.reply_to(message, "📭 Sistemde hiç bot dosyası yok.")
        return
    
    msj = "📊 **SUNUCU BOT DURUMU**\n\n"
    for dosya in all_files:
        if dosya in proceler and proceler[dosya].poll() is None:
            durum = "🟢 **AKTİF**"
        else:
            durum = "🔴 **KAPALI**"
        msj += f"📄 `{dosya}`\n└ Durum: {durum}\n\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🗑️ Bot Silme Menüsü", callback_data="delete_menu"))
    bot.send_message(message.chat.id, msj, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "delete_menu")
def delete_menu(call):
    if not is_admin(call.from_user.id): return
    markup = telebot.types.InlineKeyboardMarkup()
    all_files = [f for f in os.listdir() if f.endswith('.py') and f != 'main.py']
    for f in all_files:
        markup.add(telebot.types.InlineKeyboardButton(f"❌ Sil: {f}", callback_data=f"del_{f}"))
    bot.edit_message_text("🗑️ **Silmek istediğin botu seç sevgilim:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def perform_delete(call):
    if not is_admin(call.from_user.id): return
    file_to_del = call.data.replace("del_", "")
    if file_to_del in proceler:
        try: proceler[file_to_del].terminate()
        except: pass
    try:
        os.remove(file_to_del)
        bot.answer_callback_query(call.id, f"{file_to_del} silindi!")
        bot.edit_message_text(f"✅ `{file_to_del}` sistemden tamamen temizlendi.", call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"🚨 Silme hatası: {e}")

# --- ANA DÖNGÜ ---
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("🛰 Titan Host v3.0 Başlatıldı...")
    bot.infinity_polling()
