import os
import io
import qrcode
import cv2
import numpy as np
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- Helper functions ---

def generate_qr(data: str) -> io.BytesIO:
    """Generate QR code from text or URL"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save image to BytesIO for sending without saving to disk
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio


def decode_qr(image_bytes):
    """Decode QR code using OpenCV"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    if not data:
        return "No QR code detected."

    return data


# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I can generate and read QR codes.\n\n"
        "➡️ Send me any text or link to get its QR code.\n"
        "📸 Or send a photo of a QR code and I’ll decode it for you."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    bio = generate_qr(text)
    await update.message.reply_photo(photo=bio, caption="Here’s your QR code! 📦")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    file_bytes = await photo.download_as_bytearray()

    result = decode_qr(file_bytes)

    await update.message.reply_text(f"Decoded QR:\n{result}")


# --- Main Function ---

def main():
    if not BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set in .env file!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
