import json
import os
import time
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

MIN_THREAT_INDEX = 70  # soglia configurabile

def load_video_data(video_id: str):
    path = f"data/raw_comments/{video_id}.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Nessun file trovato per il video {video_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path

def save_video_data(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_controversial_reply(comment: str, summary: str) -> str:
    system_prompt = """
Sei un commentatore molto intelligente, provocatorio ma educato.

Riceverai un commento YouTube che ha un'alta probabilità di generare risposte aggressive. Il tuo compito è scrivere una risposta molto controversa, intellettualmente pungente, sarcastica o ironica, ma senza usare parolacce o insulti diretti ma se puo' corregge la grammatica e cerca di colpire sul personale (sempre elegantemente) la persona.

Contesto del video: """ + summary.strip()

    user_prompt = f"""
Rispondi a questo commento in modo pungente:

\"\"\"{comment}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Errore generazione risposta: {e}")
        return None

def process_threatening_comments(video_id: str):
    data, path = load_video_data(video_id)

    summary = data.get("riassunto_video", "Contesto non disponibile.")
    comments = data.get("commenti", [])

    count = 0
    for c in comments:
        analisi = c.get("analisi", {})
        if (
            not c.get("provocazione")
            and isinstance(analisi, dict)
            and analisi.get("indice_minaccia", 0) >= MIN_THREAT_INDEX
        ):
            print(f"\n⚠️ Commento da colpire:\n{c['comment']}\n")
            reply = generate_controversial_reply(c["comment"], summary)
            if reply:
                c["provocazione"] = {
                    "risposta": reply,
                    "stile": "controverso-intelligente"
                }
                print(f"🧨 Risposta generata:\n{reply}\n")
                count += 1
                save_video_data(path, data)  # salvataggio progressivo
                time.sleep(1)

    print(f"✅ Completato. Risposte generate per {count} commenti.")
