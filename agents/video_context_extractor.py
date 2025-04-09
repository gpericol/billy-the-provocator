import re
from openai import OpenAI
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

def get_video_title(video_url: str) -> str:
    """
    Estrae il titolo da un URL YouTube usando una semplice regex.
    NOTA: non sempre il titolo è affidabile senza scraping. Si consiglia caching.
    """
    video_id = video_url.split("v=")[-1].split("&")[0]
    return f"TITOLO_PLACEHOLDER_{video_id}"

def get_video_transcript(video_id: str) -> str | None:
    """
    Recupera la trascrizione del video da YouTube se disponibile.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['it', 'en'])
        text = " ".join([entry['text'] for entry in transcript])
        return text
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        print("⚠️ Trascrizione non disponibile per questo video.")
        return None
    except Exception as e:
        print(f"❌ Errore durante il recupero della trascrizione: {e}")
        return None

def summarize_transcript(transcript: str) -> str:
    """
    Usa OpenAI per riassumere la trascrizione in massimo 10 righe.
    """
    system_prompt = """
Sei un assistente specializzato nel sintetizzare contenuti video.

Riceverai la trascrizione di un video YouTube. Riassumila in massimo 10 righe, evidenziando i temi principali trattati, il tono generale, eventuali opinioni forti o argomenti controversi.

Non includere testo introduttivo, rispondi solo con il riassunto.
"""

    user_prompt = f"""
Questa è la trascrizione del video:

\"\"\"{transcript[:4000]}\"\"\"

Riassumila.
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("❌ Errore nel riassunto:", e)
        return "Errore durante la generazione del riassunto"
