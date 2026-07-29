import os
import json
import time
import random
import requests

from gtts import gTTS

from config import (
    client,
    PEXELS_API_KEY,
    DELAY_BETWEEN_QUESTION,
)

from db import insert_question


PEXELS_URL = "https://api.pexels.com/v1/search"


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

IMAGE_DIR = os.path.join(
    BASE_DIR,
    "part1",
    "images",
)

AUDIO_DIR = os.path.join(
    BASE_DIR,
    "part1",
    "audio",
)


# ============================================================
# CREATE FOLDER
# ============================================================

os.makedirs(
    IMAGE_DIR,
    exist_ok=True,
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True,
)


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(keyword, filename):
    try:
        headers = {
            "Authorization": PEXELS_API_KEY
        }

        params = {
            "query": keyword,
            "per_page": 1,
        }

        response = requests.get(
            PEXELS_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("photos"):
            print(
                f"Image tidak ditemukan: {keyword}"
            )
            return None

        img_url = (
            data["photos"][0]["src"]["large"]
        )

        img_response = requests.get(
            img_url,
            timeout=30,
        )

        img_response.raise_for_status()

        filename_with_ext = (
            f"{filename}.jpg"
        )

        full_path = os.path.join(
            IMAGE_DIR,
            filename_with_ext,
        )

        with open(
            full_path,
            "wb",
        ) as file:
            file.write(
                img_response.content
            )

        # Path yang disimpan ke database.
        # Tetap kompatibel dengan struktur generator lama.
        database_path = (
            f"part1/images/"
            f"{filename_with_ext}"
        )

        return database_path

    except Exception as e:
        print(
            "Image download error:",
            e,
        )

        return None


# ============================================================
# CREATE AUDIO
# ============================================================

def create_audio(
    question,
    a,
    b,
    c,
    d,
    filename,
):
    try:
        audio_text = f"""
{question}

A. {a}
B. {b}
C. {c}
D. {d}
"""

        tts = gTTS(
            text=audio_text,
            lang="en",
        )

        filename_with_ext = (
            f"{filename}.mp3"
        )

        full_path = os.path.join(
            AUDIO_DIR,
            filename_with_ext,
        )

        tts.save(full_path)

        # Path yang disimpan ke database.
        database_path = (
            f"part1/audio/"
            f"{filename_with_ext}"
        )

        return database_path

    except Exception as e:
        print(
            "Audio error:",
            e,
        )

        return None


# ============================================================
# SHUFFLE OPTIONS
# ============================================================

def shuffle_options(question):
    options = [
        (
            "A",
            question["option_a"],
        ),
        (
            "B",
            question["option_b"],
        ),
        (
            "C",
            question["option_c"],
        ),
        (
            "D",
            question["option_d"],
        ),
    ]

    original_answer = (
        question["answer"]
        .strip()
        .upper()
    )

    if original_answer not in [
        "A",
        "B",
        "C",
        "D",
    ]:
        raise ValueError(
            "Jawaban dari Gemini tidak valid"
        )

    correct_text = dict(
        options
    )[original_answer]

    random.shuffle(options)

    letters = [
        "A",
        "B",
        "C",
        "D",
    ]

    new_options = {}
    new_answer = None

    for index, (_, text) in enumerate(
        options
    ):
        new_letter = letters[index]

        new_options[new_letter] = text

        if text == correct_text:
            new_answer = new_letter

    question["option_a"] = (
        new_options["A"]
    )

    question["option_b"] = (
        new_options["B"]
    )

    question["option_c"] = (
        new_options["C"]
    )

    question["option_d"] = (
        new_options["D"]
    )

    question["answer"] = (
        new_answer
    )

    # Gambar dicari berdasarkan
    # deskripsi jawaban yang benar.
    question["image_keyword"] = (
        correct_text
    )

    return question


# ============================================================
# GENERATE QUESTIONS WITH GEMINI
# ============================================================

def generate_questions(
    level,
    jumlah,
):
    prompt = f"""
Generate exactly {jumlah} TOEIC Part 1 Photograph questions.

Difficulty level: {level}

TOEIC Part 1 rules:
- Each item represents one photograph.
- Each item must have exactly 4 options: A, B, C, and D.
- Only one option may correctly describe the photograph.
- The other three options must be plausible but clearly incorrect.
- Use realistic TOEIC situations such as offices, streets, restaurants,
  airports, stations, stores, meetings, workplaces, and public places.
- Sentences must sound natural in English.
- Adjust vocabulary and sentence complexity to the {level} level.
- Correct answers must vary between A, B, C, and D.

IMPORTANT:
- "question" may contain a short instruction appropriate for TOEIC Part 1.
- explanation MUST be written in Bahasa Indonesia.
- Do NOT mention the answer letter A/B/C/D inside explanation.
- Explanation must explain why the description matches the photograph.
- image_keyword must be a concise English search phrase that clearly
  represents the CORRECT option.
- image_keyword should describe visible people, objects, actions,
  and setting.
- Return valid JSON only.
- Do not return Markdown.
- Do not use ```json.
- Return EXACTLY {jumlah} objects.

JSON format:

[
  {{
    "question": "",
    "option_a": "",
    "option_b": "",
    "option_c": "",
    "option_d": "",
    "answer": "A",
    "explanation": "",
    "image_keyword": ""
  }}
]
"""

    for attempt in range(5):
        try:
            print(
                f"Gemini attempt "
                f"{attempt + 1}..."
            )

            response = (
                client.models
                .generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
            )

            text = (
                response.text
                .replace(
                    "```json",
                    "",
                )
                .replace(
                    "```",
                    "",
                )
                .strip()
            )

            # Cari array JSON.
            start = text.find("[")
            end = text.rfind("]")

            if start == -1 or end == -1:
                raise ValueError(
                    "JSON array tidak ditemukan"
                )

            text = text[
                start:end + 1
            ]

            data = json.loads(text)

            if not isinstance(
                data,
                list,
            ):
                raise ValueError(
                    "Respons Gemini bukan list"
                )

            if len(data) == 0:
                raise ValueError(
                    "Gemini tidak menghasilkan soal"
                )

            # Jika Gemini menghasilkan lebih banyak
            # dari yang diminta, ambil sesuai jumlah.
            data = data[:jumlah]

            return data

        except Exception as e:
            print(
                f"LLM error attempt "
                f"{attempt + 1}:",
                e,
            )

            if attempt < 4:
                time.sleep(5)

    return None


# ============================================================
# VALIDASI SATU SOAL
# ============================================================

def validate_question(question):
    required_fields = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
        "explanation",
    ]

    for field in required_fields:
        if field not in question:
            return False

        if question[field] is None:
            return False

        if (
            isinstance(
                question[field],
                str,
            )
            and
            not question[field].strip()
        ):
            return False

    answer = (
        str(question["answer"])
        .strip()
        .upper()
    )

    if answer not in [
        "A",
        "B",
        "C",
        "D",
    ]:
        return False

    return True


# ============================================================
# SAVE QUESTIONS
# ============================================================

def save_questions(
    level,
    questions,
    max_questions,
):
    # timestamp + random untuk mengurangi
    # kemungkinan nama file sama.
    batch_id = (
        f"{int(time.time())}_"
        f"{random.randint(1000, 9999)}"
    )

    saved_count = 0

    for index, question in enumerate(
        questions
    ):
        # Jangan simpan melebihi jumlah
        # yang diminta admin.
        if saved_count >= max_questions:
            break

        print(
            f"Processing question "
            f"{index + 1} "
            f"({level})"
        )

        try:
            if not validate_question(
                question
            ):
                print(
                    "Question tidak valid, "
                    "dilewati."
                )
                continue

            question = (
                shuffle_options(
                    question
                )
            )

            filename = (
                f"{level}_"
                f"{batch_id}_"
                f"{index + 1}"
            )

            keyword = (
                question.get(
                    "image_keyword",
                    "",
                )
                or
                question[
                    "option_a"
                ]
            )

            # --------------------------------
            # IMAGE
            # --------------------------------

            print(
                "Downloading image..."
            )

            image_path = (
                download_image(
                    keyword,
                    filename,
                )
            )

            time.sleep(1)

            # --------------------------------
            # AUDIO
            # --------------------------------

            print(
                "Creating audio..."
            )

            audio_path = (
                create_audio(
                    question["question"],
                    question["option_a"],
                    question["option_b"],
                    question["option_c"],
                    question["option_d"],
                    filename,
                )
            )

            time.sleep(1)

            # --------------------------------
            # DATABASE
            # --------------------------------

            insert_question(
                part_id=1,

                # Tetap menggunakan material
                # yang sekarang dipakai generator.
                material_id=33,

                difficulty_level=level,

                question_text=(
                    question["question"]
                ),

                option_a=(
                    question["option_a"]
                ),

                option_b=(
                    question["option_b"]
                ),

                option_c=(
                    question["option_c"]
                ),

                option_d=(
                    question["option_d"]
                ),

                correct_answer=(
                    question["answer"]
                ),

                explanation=(
                    question["explanation"]
                ),

                image_file=image_path,
                audio_file=audio_path,
            )

            saved_count += 1

            print(
                f"Saved to database "
                f"({saved_count}/"
                f"{max_questions})"
            )

        except Exception as e:
            print(
                "Question processing error:",
                e,
            )

        if (
            saved_count
            < max_questions
        ):
            time.sleep(
                DELAY_BETWEEN_QUESTION
            )

    return saved_count


# ============================================================
# RUN FROM ADMIN
# ============================================================

def run(
    level,
    jumlah,
):
    level = (
        str(level)
        .strip()
        .lower()
    )

    try:
        jumlah = int(jumlah)
    except (TypeError, ValueError):
        raise ValueError(
            "Jumlah soal tidak valid"
        )

    allowed_levels = [
        "beginner",
        "intermediate",
        "advanced",
    ]

    if level not in allowed_levels:
        raise ValueError(
            "Level harus beginner, "
            "intermediate, atau advanced"
        )

    if jumlah < 1:
        raise ValueError(
            "Jumlah soal minimal 1"
        )

    if jumlah > 50:
        raise ValueError(
            "Jumlah soal maksimal 50"
        )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 1"
    )

    print(
        f"Level  : {level}"
    )

    print(
        f"Jumlah : {jumlah}"
    )

    print(
        "================================\n"
    )

    total_saved = 0
    generation_round = 1

    # Jika Gemini menghasilkan kurang dari
    # jumlah yang diminta atau ada soal gagal
    # disimpan, generate kekurangannya lagi.
    while total_saved < jumlah:
        remaining = (
            jumlah - total_saved
        )

        print(
            f"\nGeneration round "
            f"{generation_round}"
        )

        print(
            f"Sisa soal: {remaining}"
        )

        questions = (
            generate_questions(
                level=level,
                jumlah=remaining,
            )
        )

        if not questions:
            print(
                "Generation failed"
            )
            break

        saved = save_questions(
            level=level,
            questions=questions,
            max_questions=remaining,
        )

        total_saved += saved

        if saved == 0:
            print(
                "Tidak ada soal yang "
                "berhasil disimpan."
            )
            break

        generation_round += 1

        # Hindari loop tanpa batas.
        if generation_round > 5:
            print(
                "Batas percobaan "
                "generate tercapai."
            )
            break

    print(
        "\n================================"
    )

    print(
        f"GENERATE SELESAI: "
        f"{total_saved}/{jumlah}"
    )

    print(
        "================================\n"
    )

    return total_saved


# ============================================================
# MANUAL RUN
# ============================================================

if __name__ == "__main__":
    # Hanya untuk testing langsung file ini.
    # Dashboard tidak menggunakan bagian ini.
    run(
        level="beginner",
        jumlah=1,
    )