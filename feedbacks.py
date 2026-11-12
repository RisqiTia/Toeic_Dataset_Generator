import json
import time
import random
from config import client
from db import insert_feedback


score_levels = ["rendah", "sedang", "tinggi"]
skill_levels = ["lemah", "cukup", "kuat"]




# =========================
# GENERATE 5 FEEDBACK SEKALIGUS
# =========================
def generate_feedbacks(score, listening, reading):


    prompt = f"""
Buat 5 variasi kalimat feedback TOEIC.


Kondisi:
- Skor: {score}
- Listening: {listening}
- Reading: {reading}


Aturan:
- Bahasa Indonesia santai tapi sopan
- Maksimal 25 kata per kalimat
- Natural seperti manusia (tidak kaku)
- Setiap kalimat HARUS berbeda gaya
- Jika bagus → apresiasi + saran ringan
- Jika lemah → dorongan + arahan belajar


Return JSON:
{{
"motivations": [
"",
"",
"",
"",
""
]
}}
"""


    for attempt in range(5):
        try:
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )


            text = res.text.strip()
            text = text.replace("```json", "").replace("```", "")
            text = text[text.find("{"):text.rfind("}")+1]


            data = json.loads(text)


            motivations = data.get("motivations", [])


            # validasi
            if isinstance(motivations, list) and len(motivations) == 5:
                return motivations


        except Exception as e:
            print(f"ERROR attempt {attempt+1}:", e)


        time.sleep(10)


    return None




# =========================
# FALLBACK 5 DATA
# =========================
def fallback_feedbacks(score, listening, reading):


    base = f"Skor kamu {score}, listening {listening}, reading {reading}"


    return [
        f"{base}, coba tingkatkan perlahan biar makin stabil.",
        f"{base}, latihan rutin bisa bantu hasil kamu naik.",
        f"{base}, tetap konsisten biar kemampuan makin seimbang.",
        f"{base}, fokus perbaiki bagian yang masih lemah ya.",
        f"{base}, sedikit demi sedikit pasti ada progress."
    ]




# =========================
# MAIN
# =========================
def run():


    print("START GENERATE FEEDBACK (5x per kondisi)")


    for score in score_levels:
        for listening in skill_levels:
            for reading in skill_levels:


                print(f"\n{score} | {listening} | {reading}")


                motivations = generate_feedbacks(score, listening, reading)

                if not motivations:
                    print("Fallback digunakan")
                    motivations = fallback_feedbacks(score, listening, reading)


                # simpan 5 data
                for mtvn in motivations:
                    print("✔", mtvn)
                    insert_feedback(score, listening, reading, mtvn)

                time.sleep(15)


    print("\nDONE - Semua feedback berhasil dibuat (135 data)")
   


# =========================
# RUN
# =========================
if __name__ == "__main__":
    run()
