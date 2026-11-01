"""
Botnoi Voice TTS provider for cow
API: https://api-voice.botnoi.ai/api/service/generate_audio
"""
import os
import time
import urllib.request

import requests

from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
from voice.voice import Voice


class BotnoiVoice(Voice):

    API_URL = "https://api-voice.botnoi.ai/api/service/generate_audio"

    def __init__(self):
        # อ่านค่าจาก config
        from config import conf
        self.api_key = conf().get("botnoi_api_key", "")
        self.speaker = str(conf().get("botnoi_speaker", "1"))
        self.speed = float(conf().get("botnoi_speed", 1))
        self.volume = float(conf().get("botnoi_volume", 1))
        if not self.api_key:
            logger.warning("[Botnoi] botnoi_api_key is empty in config.json")

    def voiceToText(self, voice_file):
        # Botnoi ไม่รองรับ ASR ใน endpoint นี้
        return None

    def textToVoice(self, text):
        if not self.api_key:
            logger.error("[Botnoi] missing api_key")
            return Reply(ReplyType.ERROR, "Botnoi API key not configured")

        payload = {
            "text": text,
            "speaker": self.speaker,
            "volume": self.volume,
            "speed": self.speed,
            "type_media": "mp3",
            "save_file": "true",
            "language": "th",
        }
        headers = {
            "Botnoi-Token": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                self.API_URL, json=payload, headers=headers, timeout=(5, 60)
            )
            if resp.status_code != 200:
                logger.error(
                    f"[Botnoi] HTTP {resp.status_code}: {resp.text[:200]}"
                )
                return Reply(ReplyType.ERROR, "Botnoi TTS failed")

            data = resp.json()
            audio_url = data.get("audio_url", "")
            if not audio_url:
                logger.error(f"[Botnoi] no audio_url: {data}")
                return Reply(ReplyType.ERROR, "Botnoi returned no audio")

            # ดาวน์โหลด mp3 ลง tmp
            fileName = (
                TmpDir().path()
                + "reply-"
                + str(int(time.time()))
                + "-"
                + str(hash(text) & 0x7FFFFFFF)
                + ".mp3"
            )
            urllib.request.urlretrieve(audio_url, fileName)

            logger.info(
                f"[Botnoi] textToVoice text={text[:40]} speaker={self.speaker} file={fileName}"
            )
            return Reply(ReplyType.VOICE, fileName)

        except Exception as e:
            logger.error(f"[Botnoi] textToVoice exception: {e}", exc_info=True)
            return Reply(ReplyType.ERROR, "Botnoi TTS error")
