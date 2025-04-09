import json
import os
import time
import re
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

BATCH_SIZE = 10


system_prompt = """
Sei un analista esperto in dinamiche di comunicazione aggressiva online.

Riceverai una lista numerata di commenti YouTube. Per ciascuno, restituisci un oggetto JSON con:

- livello_flame: intero tra 0 e 100
- contiene_insulti: true o false
- tono: "ironico", "aggressivo", "costruttivo", "provocatorio", "informativo", "altro"
- indice_minaccia: intero da 0 a 100 → indica un utente propenso a mincaccairmi di morte se lo provoco con una risposta controversa ma posta in maniera civile

Rispondi con una **lista JSON**, mantenendo lo stesso ordine dei commenti. Nessuna spiegazione.
"""

def batch_comments(comments, batch_size=BATCH_SIZE):
    for i in range(0, len(comments), batch_size):
        yield comments[i:i+batch_size]

def extract_json_from_response(response_content: str):
    try:
        json_text = re.search(r"\[.*\]", response_content, re.DOTALL).group(0)
        return json.loads(json_text)
    except Exception as e:
        print("⚠️ Errore nel parsing del JSON:", e)
        print("🔴 Contenuto ricevuto:\n", response_content[:500])
        return None

def analyze_batch(batch):
    formatted_comments = "\n".join(
        [f"{i+1}. \"{c['comment']}\"" for i, c in enumerate(batch)]
    )

    user_prompt = f"""
Analizza i seguenti commenti e rispondi **solo con il JSON puro**, senza spiegazioni.

{formatted_comments}
"""

    #print("\n📤 Prompt inviato:")
    #print(user_prompt.strip())

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()

        #print("\n📥 Risposta ricevuta:")
        #print(content[:500])  # Limita la stampa se è lunga

        parsed = extract_json_from_response(content)
        return parsed if parsed else [None] * len(batch)

    except Exception as e:
        print("❌ Errore batch:", e)
        return [None] * len(batch)

def analyze_video_comments(video_id):
    path = f"data/raw_comments/{video_id}.json"
    if not os.path.exists(path):
        print(f"❌ File non trovato: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "commenti" not in data:
        print("❌ Nessun commento trovato nel file.")
        return

    comments = data["commenti"]
    unprocessed = [c for c in comments if 'analisi' not in c]
    print(f"🧪 Commenti da analizzare: {len(unprocessed)}")

    if len(unprocessed) == 0:
        print("✅ Tutti i commenti sono già stati analizzati.")
        return

    for batch in batch_comments(unprocessed):
        results = analyze_batch(batch)

        for i, r in enumerate(results):
            comment = batch[i]
            if r and isinstance(r, dict):
                comment["analisi"] = r
            else:
                print(f"⚠️ Analisi fallita per commento: {comment.get('comment', '???')}")
                comment["analisi"] = {"errore": True}

        # Riscrive tutto il file con i commenti aggiornati
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        time.sleep(1)

    print(f"✅ Analisi completata e salvata in {path}")
