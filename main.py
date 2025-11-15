#!/usr/bin/env python3
"""
Production-ready Telegram QR Bot
"""
import os, io, time, logging, traceback
from threading import Thread
import qrcode, cv2, numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

try:
    import keep_alive
    KEEP_ALIVE_AVAILABLE = True
except Exception:
    KEEP_ALIVE_AVAILABLE = False

BOT_TOKEN = os.getenv("8098035786:AAFa2uNiOEI92nvApTySfGRqztzvd7CyHM0")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("qr_bot")

def generate_qr(text: str, box_size: int = 10, border: int = 4):
    qr = qrcode.QRCode(version=1, box_size=box_size, border=border)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

def decode_qr(image_bytes: bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        return data if data else None
    except Exception:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I generate and decode QR codes.
Send text to get a QR code.
Send a photo of a QR code to decode it."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/generate <text> - create QR
Send a photo to decode.")

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: /generate <text>")
        return
    await update.message.reply_photo(photo=generate_qr(text), caption=f"QR for:
{text}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(photo=generate_qr(update.message.text), caption="Here's your QR!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    data = decode_qr(await photo_file.download_as_bytearray())
    await update.message.reply_text(f"Decoded:
{data}" if data else "No QR found.")

def start_keep_alive():
    if KEEP_ALIVE_AVAILABLE:
        Thread(target=keep_alive.run, daemon=True).start()

def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("generate", generate_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    return app

def main():
    if not BOT_TOKEN:
        logger.error("Token missing.")
        return
    start_keep_alive()
    backoff = 1
    while True:
        try:
            app = build_app()
            app.run_polling()
            break
        except Exception:
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)

if __name__ == "__main__":
    main()
