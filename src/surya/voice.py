"""Voice notes: Amazon Transcribe in (Hindi or English, detected), Amazon Polly out.

Audio goes to a bucket that deletes everything after a day; replies are served from it through a
short-lived presigned link, because WhatsApp fetches media by URL.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import uuid

import boto3
from botocore.config import Config

LANGUAGES = {"hi": "hi-IN", "en": "en-IN"}
VOICE = "Kajal"  # Polly's neural voice that speaks both Hindi and Indian English
POLL_S, MAX_WAIT_S = 1.5, 60
FORMATS = {"audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/mp4": "mp4", "audio/amr": "amr", "audio/wav": "wav", "audio/webm": "webm"}


def _bucket() -> str:
    return os.environ["VOICE_BUCKET"]


def transcribe(audio: bytes, media_type: str) -> tuple[str, str]:
    """(text, language) for a voice note; language is "hi" or "en"."""
    s3, tr = boto3.client("s3"), boto3.client("transcribe")
    key = f"in/{uuid.uuid4().hex}"
    s3.put_object(Bucket=_bucket(), Key=key, Body=audio, ContentType=media_type)
    job = f"surya-{uuid.uuid4().hex[:16]}"
    tr.start_transcription_job(
        TranscriptionJobName=job,
        Media={"MediaFileUri": f"s3://{_bucket()}/{key}"},
        MediaFormat=FORMATS.get(media_type.split(";")[0].strip(), "ogg"),
        IdentifyLanguage=True,
        LanguageOptions=list(LANGUAGES.values()),
    )
    waited = 0.0
    while waited < MAX_WAIT_S:
        j = tr.get_transcription_job(TranscriptionJobName=job)["TranscriptionJob"]
        if j["TranscriptionJobStatus"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(POLL_S)
        waited += POLL_S
    if j["TranscriptionJobStatus"] != "COMPLETED":
        return "", "hi"
    with urllib.request.urlopen(j["Transcript"]["TranscriptFileUri"], timeout=20) as r:
        text = json.load(r)["results"]["transcripts"][0]["transcript"]
    lang = "en" if j.get("LanguageCode", "hi-IN").startswith("en") else "hi"
    return text, lang


def speak(text: str, lang: str) -> str:
    """A presigned link to an MP3 of `text`, valid for an hour."""
    polly = boto3.client("polly")
    s3 = boto3.client("s3", config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}))
    audio = polly.synthesize_speech(Text=text[:2900], OutputFormat="mp3", VoiceId=VOICE, Engine="neural",
                                    LanguageCode=LANGUAGES.get(lang, "hi-IN"))["AudioStream"].read()
    key = f"out/{uuid.uuid4().hex}.mp3"
    s3.put_object(Bucket=_bucket(), Key=key, Body=audio, ContentType="audio/mpeg")
    return s3.generate_presigned_url("get_object", Params={"Bucket": _bucket(), "Key": key}, ExpiresIn=3600)
