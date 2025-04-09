import os
import json
import time
from urllib.parse import urlparse, parse_qs

from agents.youtube_scraper import get_video_data_from_url
from agents.video_context_extractor import get_video_transcript, summarize_transcript
from agents.comment_analyzer import analyze_video_comments
from agents.provocation_agent import process_threatening_comments

DATA_DIR = "data/raw_comments"

def extract_video_id(url: str) -> str | None:
    qs = parse_qs(urlparse(url).query)
    return qs.get('v', [None])[0]

def load_existing_data(video_id: str) -> dict | None:
    path = os.path.join(DATA_DIR, f"{video_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(video_id: str, data: dict):
    path = os.path.join(DATA_DIR, f"{video_id}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Dati salvati in {path}")

def main():
    url = input("🎥 Inserisci l'URL del video YouTube: ").strip()
    video_id = extract_video_id(url)

    if not video_id:
        print("❌ URL non valido.")
        return

    print(f"\n📽️ VIDEO ID: {video_id}")

    # 1. Carica o inizializza
    existing_data = load_existing_data(video_id)
    if existing_data:
        print("📁 File esistente. Lo aggiorno.")
    else:
        print("📥 Estrazione commenti e titolo...")
        video_data = get_video_data_from_url(url)
        existing_data = {
            "video_id": video_id,
            "titolo": video_data["titolo"],
            "commenti": video_data["commenti"]
        }
        print(f"📝 Titolo: {video_data['titolo']}")
        print(f"💬 Trovati {len(video_data['commenti'])} commenti.")

    # 2. Trascrizione e riassunto
    if "riassunto_video" not in existing_data:
        print("📜 Recupero trascrizione...")
        transcript = get_video_transcript(video_id)
        if transcript:
            print("✍️ Riassumo il contenuto del video...")
            summary = summarize_transcript(transcript)
        else:
            summary = "Trascrizione non disponibile."
        existing_data["riassunto_video"] = summary

    # 3. Salvataggio iniziale
    save_data(video_id, existing_data)

    # 4. Analisi commenti
    print("🔍 Analizzo i commenti...")
    analyze_video_comments(video_id)

    # 5. Generazione risposte provocatorie
    print("🧨 Generazione delle risposte più controverse...")
    process_threatening_comments(video_id)

    print("✅ Tutto fatto. File completo salvato.")

if __name__ == "__main__":
    main()
