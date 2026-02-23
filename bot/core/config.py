import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    bot_token: str = os.getenv("BOT_TOKEN")
    channel_id: int = int(os.getenv("CHANNEL_ID"))
    download_path: str = "downloads"

config = Config()

if not os.path.exists(config.download_path):
    os.makedirs(config.download_path)