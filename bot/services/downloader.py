import os
import uuid
import asyncio
import yt_dlp
import logging
import re
from typing import Optional, Tuple
from bot.core.config import config


INSTAGRAM_PATTERN: re.Pattern[str] = re.compile(
    r"^https?://(www\.)?instagram\.com/reel/[\w\-]+"
)

TIKTOK_PATTERN: re.Pattern[str] = re.compile(
    r"^https?://((?:vm|vt|www)\.)?tiktok\.com/.*"
)


class VideoDownloader:
    def __init__(self):
        # Путь к JSON файлу с куками
        self.cookie_path = "/app/cookies.txt"

        self.ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
            'outtmpl': '/app/downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'cookiefile': self.cookie_path if os.path.exists(self.cookie_path) else None,
            'extractor_args': {'tiktok': {'webpage_download': True}},
            # Это критично: заставляем ffmpeg просто копировать потоки
            'postprocessor_args': ['-c:v', 'copy', '-c:a', 'aac', '-map', '0'],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }

    async def download_video(self, url: str) -> Tuple[Optional[str], float]:
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                if not info:
                    return None, 0
                
                path = ydl.prepare_filename(info)
                if not os.path.exists(path):
                    path = path.rsplit('.', 1)[0] + ".mp4"
                
                # Получаем размер файла в мегабайтах
                file_size = os.path.getsize(path) / (1024 * 1024)
                return path, file_size
        except Exception as e:
            logging.error(f"YT-DLP Error: {e}")
            return None, 0
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        if INSTAGRAM_PATTERN.match(url):
            return True
        if TIKTOK_PATTERN.match(url):
            return True
        return False

    @staticmethod
    def remove_file(file_path: str) -> None:
        if os.path.exists(file_path):
            os.remove(file_path)