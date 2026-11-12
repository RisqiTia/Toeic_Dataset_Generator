import os
import json
import time
import requests
from gtts import gTTS
from upload_asset import upload_file

from file_py.config import client, PEXELS_API_KEY
from file_py.db import insert_material

PEXELS_URL = "https://api.pexels.com/v1/search"

START_PART = 1
END_PART = 7

os.makedirs("materials/images", exist_ok=True)
os.makedirs("materials/audio", exist_ok=True)

# ================= IMAGE =================
def download_image(query, filename):
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": query, "per_page": 1}

        r = requests.get(PEXELS_URL, headers=headers, params=params)
        data = r.json()

        if not data.get("photos"):
            return None

        img_url = data["photos"][0]["src"]["large"]
        img = requests.get(img_url).content

        path = f"materials/images/{filename}.jpg"

        with open(path, "wb") as f:
            f.write(img)

        hosting_path = upload_file(
            path,
            "materials/images")

        return hosting_path
    except:
        return None

# ================= AUDIO =================
def create_audio(text, filename):
    try:
        path = f"materials/audio/{filename}.mp3"
        gTTS(text=str(text), lang="en").save(path)
        
        hosting_path = upload_file(
            path,
            "materials/audio"
        )
        return hosting_path
    except:
        return None

# ================= GENERATE =================
def generate_material(part):

    # ===== PART 3 & 4 =====
    if part in [3, 4]:

        prompt = f"""
Buat materi TOEIC Part {part}.

Gunakan Bahasa Indonesia untuk penjelasan.
Gunakan Bahasa Inggris untuk soal.

Return JSON:

{{
"title": "",
"intro": "",
"what_is_tested": ["", "", ""],

"example": {{
    "conversation": "",
    "questions": [
        {{
            "question": "",
            "choices": {{
                "A": "",
                "B": "",
                "C": "",
                "D": ""
            }},
            "answer": "A",
            "explanation": ""
        }},
        {{
            "question": "",
            "choices": {{
                "A": "",
                "B": "",
                "C": "",
                "D": ""
            }},
            "answer": "A",
            "explanation": ""
        }},
        {{
            "question": "",
            "choices": {{
                "A": "",
                "B": "",
                "C": "",
                "D": ""
            }},
            "answer": "A",
            "explanation": ""
        }}
    ]
}},

"strategies": ["", "", ""],
"tips": ["", "", ""]
}}

ATURAN:
- conversation = bahasa Inggris
- HARUS 3 soal
- penjelasan = bahasa Indonesia
- JSON 1 baris
"""

    # ===== PART LAIN =====
    else:

        prompt = f"""
Buat materi TOEIC Part {part}.

Gunakan Bahasa Indonesia untuk penjelasan.
Gunakan Bahasa Inggris untuk contoh soal.

Return JSON:

{{
"title": "",
"intro": "",
"what_is_tested": ["", "", ""],

"example": {{
    "question": "",
    "choices": {{
        "A": "",
        "B": "",
        "C": "",
        "D": ""
    }},
    "answer": "A",
    "explanation": ""
}},

"strategies": ["", "", ""],
"tips": ["", "", ""],
"image_keyword": ""
}}

ATURAN:
- contoh soal menyesuaikan aturan toeic yang sebenarnya misal part 3 & 4 ada 2/3 pertanyaan, maka buatlah sesuai itu
- Part 1 tanpa question
- JSON 1 baris
"""

    for _ in range(5):
        try:
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            text = res.text.strip()
            text = text.replace("```json", "").replace("```", "")

            text = text[text.find("{"):text.rfind("}")+1]
            text = text.replace("\n", " ")

            return json.loads(text)

        except Exception as e:
            print("LLM error:", e)
            time.sleep(5)

    return None

# ================= BUILD TEXT =================
def build_material_text(part, data):

    intro = data.get("intro", "")
    what = data.get("what_is_tested", [])
    strategies = data.get("strategies", [])
    tips = data.get("tips", [])

    # ===== PART 3 & 4 =====
    if part in [3, 4]:

        example = data.get("example", {})
        convo = example.get("conversation", "")
        questions = example.get("questions", [])

        soal_text = f"\nPercakapan:\n{convo}\n"

        for i, q in enumerate(questions, 1):
            soal_text += f"\nQuestion {i}:\n{q['question']}\n"
            soal_text += f"A. {q['choices']['A']}\n"
            soal_text += f"B. {q['choices']['B']}\n"
            soal_text += f"C. {q['choices']['C']}\n"
            soal_text += f"D. {q['choices']['D']}\n"

        pembahasan = ""
        for i, q in enumerate(questions, 1):
            pembahasan += f"\nJawaban {i}: {q['answer']}\n{q['explanation']}\n"

    # ===== PART LAIN =====
    else:

        example = data.get("example", {})
        question = example.get("question", "")
        choices = example.get("choices", {})

        soal_text = ""
        if question:
            soal_text += f"{question}\n\n"

        soal_text += f"""A. {choices.get("A")}
B. {choices.get("B")}
C. {choices.get("C")}
D. {choices.get("D")}
"""

        pembahasan = f"Jawaban: {example.get('answer')}\n{example.get('explanation')}"

    return f"""{intro}

Apa yang diuji:
- {"\n- ".join(what)}

Contoh Soal:
{soal_text}

Pembahasan:
{pembahasan}

Strategi:
- {"\n- ".join(strategies)}

Tips:
- {"\n- ".join(tips)}
"""

# ================= AUDIO =================
def build_audio(part, data):

    if part in [3, 4]:
        return data.get("example", {}).get("conversation")

    example = data.get("example", {})
    choices = example.get("choices", {})
    question = example.get("question", "")

    if part == 1:
        return f"A. {choices.get('A')} B. {choices.get('B')} C. {choices.get('C')} D. {choices.get('D')}"

    if part == 2:
        return f"{question} A. {choices.get('A')} B. {choices.get('B')} C. {choices.get('C')}"

    return None

# ================= MAIN =================
def run():

    print("START GENERATE TOEIC MATERIAL")

    for part in range(START_PART, END_PART + 1):

        print(f"\nPart {part}")

        data = generate_material(part)
        if not data:
            continue

        text = build_material_text(part, data)

        image_path = None
        if part == 1:
            keyword = data.get("image_keyword")
            if keyword:
                image_path = download_image(keyword, f"part{part}")

        audio_script = build_audio(part, data)
        audio_path = create_audio(audio_script, f"part{part}") if audio_script else None

        insert_material(part, data.get("title"), image=image_path, audio=audio_path, text=text)

        print("Saved")
        time.sleep(10)

    print("DONE")

if __name__ == "__main__":
    run()