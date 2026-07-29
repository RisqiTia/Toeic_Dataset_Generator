import os
import json
import time
import requests
from gtts import gTTS

from config import client, PEXELS_API_KEY
from db import insert_material


PEXELS_URL = "https://api.pexels.com/v1/search"

# Folder media
os.makedirs("materials/images", exist_ok=True)
os.makedirs("materials/audio", exist_ok=True)


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(query, filename):
    try:
        if not query:
            return None

        headers = {
            "Authorization": PEXELS_API_KEY
        }

        params = {
            "query": query,
            "per_page": 1
        }

        response = requests.get(
            PEXELS_URL,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("photos"):
            print("Gambar tidak ditemukan.")
            return None

        image_url = data["photos"][0]["src"]["large"]

        image_response = requests.get(
            image_url,
            timeout=30
        )

        image_response.raise_for_status()

        path = f"materials/images/{filename}.jpg"

        with open(path, "wb") as file:
            file.write(image_response.content)

        print(f"Image saved: {path}")

        return path

    except Exception as e:
        print("Image download error:", e)
        return None


# ============================================================
# CREATE AUDIO
# ============================================================

def create_audio(text, filename):
    try:
        if not text:
            return None

        path = f"materials/audio/{filename}.mp3"

        gTTS(
            text=str(text),
            lang="en"
        ).save(path)

        print(f"Audio saved: {path}")

        return path

    except Exception as e:
        print("Audio error:", e)
        return None


# ============================================================
# FIX JSON
# ============================================================

def clean_json(text):
    text = (
        text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "JSON tidak ditemukan pada respons Gemini."
        )

    return text[start:end + 1]


# ============================================================
# GENERATE MATERIAL
# ============================================================

def generate_material(part, max_retries=5):

    # --------------------------------------------------------
    # PART 3 & 4
    # --------------------------------------------------------

    if part in [3, 4]:

        prompt = f"""
Buat satu materi pembelajaran TOEIC Part {part}.

Gunakan Bahasa Indonesia untuk:
- intro
- what_is_tested
- explanation
- strategies
- tips

Gunakan Bahasa Inggris untuk:
- conversation
- question
- choices

Buat contoh sesuai format TOEIC Part {part}.

Satu conversation harus memiliki tepat 3 pertanyaan.

Return VALID JSON ONLY:

{{
    "title": "",
    "intro": "",
    "what_is_tested": [
        "",
        "",
        ""
    ],
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
                "answer": "B",
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
                "answer": "C",
                "explanation": ""
            }}
        ]
    }},
    "strategies": [
        "",
        "",
        ""
    ],
    "tips": [
        "",
        "",
        ""
    ]
}}

ATURAN:
- Conversation harus natural.
- Conversation menggunakan Bahasa Inggris.
- Harus tepat 3 pertanyaan.
- Setiap pertanyaan memiliki 4 pilihan.
- Hanya satu jawaban benar.
- Explanation menggunakan Bahasa Indonesia.
- Jangan menambahkan teks di luar JSON.
"""

    # --------------------------------------------------------
    # PART 1, 2, 5, 6, 7
    # --------------------------------------------------------

    else:

        prompt = f"""
Buat satu materi pembelajaran TOEIC Part {part}.

Gunakan Bahasa Indonesia untuk:
- intro
- what_is_tested
- explanation
- strategies
- tips

Gunakan Bahasa Inggris untuk contoh soal dan pilihan jawaban.

Return VALID JSON ONLY:

{{
    "title": "",
    "intro": "",
    "what_is_tested": [
        "",
        "",
        ""
    ],
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
    "strategies": [
        "",
        "",
        ""
    ],
    "tips": [
        "",
        "",
        ""
    ],
    "image_keyword": ""
}}

ATURAN:

- Materi harus sesuai dengan TOEIC Part {part}.
- Explanation menggunakan Bahasa Indonesia.
- Jangan menambahkan teks di luar JSON.

KHUSUS PART 1:
- question harus berupa string kosong "".
- Pilihan A-D berupa deskripsi foto dalam Bahasa Inggris.
- image_keyword harus menggambarkan jawaban yang benar.
- image_keyword menggunakan Bahasa Inggris.

KHUSUS PART 2:
- question berupa pertanyaan atau pernyataan listening.
- Hanya pilihan A, B, C yang digunakan.
- choices D harus berupa string kosong "".

KHUSUS PART 5:
- question harus berupa incomplete sentence.
- Gunakan ___ sebagai bagian yang kosong.
- Tidak membutuhkan gambar atau audio.

KHUSUS PART 6:
- Contoh harus menggambarkan konsep Text Completion.
- Tidak membutuhkan gambar atau audio.

KHUSUS PART 7:
- Contoh harus menggambarkan Reading Comprehension.
- Tidak membutuhkan gambar atau audio.
"""

    # --------------------------------------------------------
    # REQUEST GEMINI
    # --------------------------------------------------------

    for attempt in range(max_retries):

        try:

            print(
                f"Requesting Gemini "
                f"(attempt {attempt + 1})..."
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            cleaned = clean_json(
                response.text
            )

            data = json.loads(
                cleaned
            )

            # Validasi dasar
            if not data.get("title"):
                raise ValueError(
                    "Title materi kosong."
                )

            if not data.get("intro"):
                raise ValueError(
                    "Intro materi kosong."
                )

            if not data.get("example"):
                raise ValueError(
                    "Example materi kosong."
                )

            # Part 3 dan 4 harus punya 3 soal
            if part in [3, 4]:

                questions = (
                    data
                    .get("example", {})
                    .get("questions", [])
                )

                if len(questions) != 3:
                    raise ValueError(
                        "Part 3/4 harus memiliki "
                        "tepat 3 contoh soal."
                    )

            print("Materi berhasil di-generate.")

            return data

        except Exception as e:

            print(
                f"Generation error "
                f"attempt {attempt + 1}:",
                e
            )

            if attempt < max_retries - 1:
                time.sleep(5)

    return None


# ============================================================
# BUILD MATERIAL TEXT
# ============================================================

def build_material_text(part, data):

    intro = data.get(
        "intro",
        ""
    )

    what = data.get(
        "what_is_tested",
        []
    )

    strategies = data.get(
        "strategies",
        []
    )

    tips = data.get(
        "tips",
        []
    )

    # --------------------------------------------------------
    # PART 3 & 4
    # --------------------------------------------------------

    if part in [3, 4]:

        example = data.get(
            "example",
            {}
        )

        conversation = example.get(
            "conversation",
            ""
        )

        questions = example.get(
            "questions",
            []
        )

        question_text = (
            f"\nPercakapan:\n"
            f"{conversation}\n"
        )

        discussion = ""

        for index, question in enumerate(
            questions,
            1
        ):

            choices = question.get(
                "choices",
                {}
            )

            question_text += (
                f"\nQuestion {index}:\n"
                f"{question.get('question', '')}\n"
                f"A. {choices.get('A', '')}\n"
                f"B. {choices.get('B', '')}\n"
                f"C. {choices.get('C', '')}\n"
                f"D. {choices.get('D', '')}\n"
            )

            discussion += (
                f"\nJawaban {index}: "
                f"{question.get('answer', '')}\n"
                f"{question.get('explanation', '')}\n"
            )

    # --------------------------------------------------------
    # PART LAIN
    # --------------------------------------------------------

    else:

        example = data.get(
            "example",
            {}
        )

        question = example.get(
            "question",
            ""
        )

        choices = example.get(
            "choices",
            {}
        )

        question_text = ""

        if question:
            question_text += (
                f"{question}\n\n"
            )

        question_text += (
            f"A. {choices.get('A', '')}\n"
            f"B. {choices.get('B', '')}\n"
            f"C. {choices.get('C', '')}\n"
        )

        # Part 2 hanya A-C
        if part != 2:
            question_text += (
                f"D. {choices.get('D', '')}\n"
            )

        discussion = (
            f"Jawaban: "
            f"{example.get('answer', '')}\n"
            f"{example.get('explanation', '')}"
        )

    # --------------------------------------------------------
    # FINAL TEXT
    # --------------------------------------------------------

    what_text = "\n- ".join(
        str(item)
        for item in what
    )

    strategies_text = "\n- ".join(
        str(item)
        for item in strategies
    )

    tips_text = "\n- ".join(
        str(item)
        for item in tips
    )

    return f"""\
{intro}

Apa yang diuji:
- {what_text}

Contoh Soal:
{question_text}

Pembahasan:
{discussion}

Strategi:
- {strategies_text}

Tips:
- {tips_text}
"""


# ============================================================
# BUILD AUDIO
# ============================================================

def build_audio(part, data):

    example = data.get(
        "example",
        {}
    )

    # Part 3 & 4
    if part in [3, 4]:

        return example.get(
            "conversation",
            ""
        )

    choices = example.get(
        "choices",
        {}
    )

    question = example.get(
        "question",
        ""
    )

    # Part 1
    if part == 1:

        return (
            f"A. {choices.get('A', '')}. "
            f"B. {choices.get('B', '')}. "
            f"C. {choices.get('C', '')}. "
            f"D. {choices.get('D', '')}."
        )

    # Part 2
    if part == 2:

        return (
            f"{question}. "
            f"A. {choices.get('A', '')}. "
            f"B. {choices.get('B', '')}. "
            f"C. {choices.get('C', '')}."
        )

    # Part 5-7 tidak perlu audio
    return None


# ============================================================
# RUN
# ============================================================

def run(part):

    try:
        part = int(part)

    except (TypeError, ValueError):

        raise ValueError(
            "Part tidak valid."
        )

    if part < 1 or part > 7:

        raise ValueError(
            "Part harus antara 1 sampai 7."
        )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC MATERIAL"
    )

    print(
        f"Part : {part}"
    )

    print(
        "================================\n"
    )

    # ========================================================
    # GENERATE DATA
    # ========================================================

    data = generate_material(
        part
    )

    if not data:

        print(
            "Gagal generate materi."
        )

        return False

    # ========================================================
    # BUILD TEXT
    # ========================================================

    material_text = (
        build_material_text(
            part,
            data
        )
    )

    # ========================================================
    # UNIQUE FILE NAME
    # ========================================================

    timestamp = int(
        time.time()
    )

    filename = (
        f"part{part}_{timestamp}"
    )

    # ========================================================
    # IMAGE
    # ========================================================

    image_path = None

    if part == 1:

        keyword = data.get(
            "image_keyword",
            ""
        )

        if keyword:

            print(
                f"Downloading image: "
                f"{keyword}"
            )

            image_path = (
                download_image(
                    keyword,
                    filename
                )
            )

    # ========================================================
    # AUDIO
    # ========================================================

    audio_script = (
        build_audio(
            part,
            data
        )
    )

    audio_path = None

    if audio_script:

        print(
            "Creating audio..."
        )

        audio_path = (
            create_audio(
                audio_script,
                filename
            )
        )

    # ========================================================
    # DATABASE
    # ========================================================

    print(
        "Saving material to database..."
    )

    try:

        insert_material(
            part,
            data.get(
                "title",
                f"TOEIC Part {part}"
            ),
            image=image_path,
            audio=audio_path,
            text=material_text
        )

    except Exception as e:

        print(
            "Database insert error:",
            e
        )

        return False

    print(
        "\n================================"
    )

    print(
        "MATERIAL SAVED SUCCESSFULLY"
    )

    print(
        f"Part  : {part}"
    )

    print(
        f"Title : {data.get('title')}"
    )

    print(
        f"Image : {image_path or '-'}"
    )

    print(
        f"Audio : {audio_path or '-'}"
    )

    print(
        "================================\n"
    )

    return True


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            "Cara penggunaan:"
        )

        print(
            "python generate_material_admin.py <part>"
        )

        print(
            "Contoh:"
        )

        print(
            "python generate_material_admin.py 1"
        )

    else:

        selected_part = (
            sys.argv[1]
        )

        try:

            success = run(
                selected_part
            )

            if not success:
                raise SystemExit(1)

        except Exception as e:

            print(
                "ERROR:",
                e
            )

            raise SystemExit(1)