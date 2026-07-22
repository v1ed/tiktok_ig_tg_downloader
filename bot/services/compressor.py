import asyncio
import logging
import os
import uuid


MAX_SIZE = 50 * 1024 * 1024
TARGET_SIZE = 48 * 1024 * 1024
logger = logging.getLogger(__name__)


class VideoCompressor:
    async def compress_if_needed(self, file_path: str) -> str:
        source_size = os.path.getsize(file_path)
        if source_size <= MAX_SIZE:
            logger.debug("Compression skipped: path=%s size=%.2f MB", file_path, source_size / 1024 / 1024)
            return file_path

        logger.info("Compressing video: path=%s size=%.2f MB", file_path, source_size / 1024 / 1024)
        duration = await self._duration(file_path)
        audio_bitrate = 96_000
        video_bitrate = max(100_000, int(TARGET_SIZE * 8 / duration) - audio_bitrate)
        output_path = f"{os.path.splitext(file_path)[0]}-{uuid.uuid4().hex}.mp4"

        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", file_path,
            "-c:v", "libx264", "-b:v", str(video_bitrate),
            "-c:a", "aac", "-b:a", str(audio_bitrate),
            "-movflags", "+faststart", output_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        if process.returncode:
            if os.path.exists(output_path):
                os.remove(output_path)
            error = stderr.decode(errors="replace")
            logger.error("Video compression failed: %s", error)
            raise RuntimeError(error)
        logger.info("Video compressed: path=%s size=%.2f MB", output_path, os.path.getsize(output_path) / 1024 / 1024)
        return output_path

    @staticmethod
    async def _duration(file_path: str) -> float:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode:
            error = stderr.decode(errors="replace")
            logger.error("Video duration detection failed: %s", error)
            raise RuntimeError(error)
        duration = float(stdout)
        logger.debug("Video duration: %.2f seconds", duration)
        return duration
