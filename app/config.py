from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")

ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID"))

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

DOMAIN = os.getenv("DOMAIN")
ADMIN_DOMAIN = os.getenv("ADMIN_DOMAIN")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

# 🔐 Admin Dashboard Secret
ADMIN_SECRET = os.getenv("ADMIN_SECRET")
