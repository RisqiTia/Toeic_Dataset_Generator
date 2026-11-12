import os
import json
import time
import random

from gtts import gTTS

from file_py.config import (
    client,
    DELAY_BETWEEN_QUESTION,
)

from file_py.db import (
    insert_question,
    get_connection,
)


# ============================================================
# CONFIG
# ============================================================

PART_ID = 4


# ============================================================
# DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

AUDIO_DIR = os.path.join(
    BASE_DIR,
    "part4",
    "audio",
    "talk",
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True,
)


# ============================================================
# GET MATERIAL ID PART 4
# ============================================================

def get_material_id_part4():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM materials
            WHERE part_id = 4
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if not row:
            raise ValueError(
                "Tidak ada material untuk Part 4. "
                "Buat minimal 1 material Part 4 "
                "pada tabel materials."
            )

        return row[0]

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# CREATE TALK AUDIO
# ============================================================

def create_talk_audio(
    text,
    filename,
):
    try:
        filename_with_ext = (
            f"{filename}.mp3"
        )

        full_path = os.path.join(
            AUDIO_DIR,
            filename_with_ext,
        )

        tts = gTTS(
            text=text,
            lang="en",
        )

        tts.save(full_path)

        # Path yang disimpan ke database
        return (
            "part4/audio/talk/"
            f"{filename_with_ext}"
        )

    except Exception as e:
        print(
            "Talk audio error:",
            e,
        )

        return None


# ============================================================
# SHUFFLE OPTIONS
# ============================================================

def shuffle_options(question):
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
        raise ValueError(
            "Jawaban harus A, B, C, atau D"
        )

    options = [
        question["option_a"],
        question["option_b"],
        question["option_c"],
        question["option_d"],
    ]

    correct_text = question[
        f"option_{answer.lower()}"
    ]

    random.shuffle(options)

    question["option_a"] = options[0]
    question["option_b"] = options[1]
    question["option_c"] = options[2]
    question["option_d"] = options[3]

    if options[0] == correct_text:
        question["answer"] = "A"

    elif options[1] == correct_text:
        question["answer"] = "B"

    elif options[2] == correct_text:
        question["answer"] = "C"

    elif options[3] == correct_text:
        question["answer"] = "D"

    return question


# ============================================================
# VALIDATE QUESTION
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

        value = question[field]

        if value is None:
            return False

        if (
            isinstance(value, str)
            and not value.strip()
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

    options = [
        question["option_a"],
        question["option_b"],
        question["option_c"],
        question["option_d"],
    ]

    # Semua pilihan harus berbeda
    if len(set(options)) < 4:
        return False

    return True


# ============================================================
# VALIDATE TALK
# ============================================================

def validate_talk(talk_data):
    if not isinstance(
        talk_data,
        dict,
    ):
        return False

    talk = (
        talk_data.get(
            "talk",
            "",
        )
    )

    questions = (
        talk_data.get(
            "questions",
            [],
        )
    )

    if not str(talk).strip():
        return False

    if not isinstance(
        questions,
        list,
    ):
        return False

    # Part 4: satu talk = tepat 3 soal
    if len(questions) != 3:
        return False

    for question in questions:
        if not validate_question(
            question
        ):
            return False

    return True


# ============================================================
# GENERATE TALKS
# ============================================================

def generate_questions(
    level,
    jumlah,
):
    total_talks = jumlah // 3

    prompt = f"""
Generate TOEIC Part 4 Listening Talks.

Difficulty level: {level}

Create exactly {total_talks} talks.

IMPORTANT:
- Each talk MUST contain exactly 3 questions.
- Total questions MUST be exactly {jumlah}.
- A talk is a monologue spoken by ONE speaker.

TOEIC Part 4 rules:
- Each talk should contain approximately 5 to 8 sentences.
- Use natural spoken English.
- Use realistic TOEIC contexts such as:
  announcements,
  recorded messages,
  office updates,
  advertisements,
  tourism information,
  business presentations,
  company news,
  event announcements,
  transportation announcements,
  weather reports,
  customer service messages,
  introductions,
  instructions.
- Each question must test comprehension of the talk.
- Use varied question types such as:
  main purpose,
  speaker intention,
  location,
  audience,
  specific detail,
  reason,
  next action,
  implied meaning.
- Each question must have exactly four choices:
  A, B, C, and D.
- Only one answer can be correct.
- Distractors must be plausible.
- Correct answers should vary between A, B, C, and D.
- Adjust vocabulary and complexity to the {level} level.

LANGUAGE RULES:
- Talk must be written in English.
- Questions must be written in English.
- Options must be written in English.
- Explanation MUST be written in Bahasa Indonesia.
- Explanation must explain why the answer is correct
  based on information in the talk.
- Do NOT mention option letters A/B/C/D
  in the explanation.

Return valid JSON only.
Do NOT return Markdown.
Do NOT use ```json.
Do NOT include comments inside JSON.

JSON format:

[
  {{
    "talk": "",
    "questions": [
      {{
        "question": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "answer": "A",
        "explanation": ""
      }},
      {{
        "question": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "answer": "B",
        "explanation": ""
      }},
      {{
        "question": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "answer": "C",
        "explanation": ""
      }}
    ]
  }}
]

Generate EXACTLY:
- {total_talks} talks
- 3 questions per talk
- {jumlah} questions total
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

            # Cari JSON array
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
                    "Gemini tidak menghasilkan talk"
                )

            # Batasi sesuai jumlah talk
            data = data[:total_talks]

            valid_data = []

            for talk_data in data:
                if validate_talk(
                    talk_data
                ):
                    valid_data.append(
                        talk_data
                    )

                else:
                    print(
                        "Talk tidak valid "
                        "dan dilewati."
                    )

            if valid_data:
                return valid_data

            raise ValueError(
                "Tidak ada talk valid"
            )

        except Exception as e:
            print(
                f"LLM error attempt "
                f"{attempt + 1}:",
                e,
            )

            if attempt < 4:
                print(
                    "Retrying..."
                )

                time.sleep(5)

    return None


# ============================================================
# SAVE QUESTIONS
# ============================================================

def save_questions(
    level,
    data,
    material_id,
    max_questions,
):
    batch_id = (
        f"{int(time.time())}_"
        f"{random.randint(1000, 9999)}"
    )

    saved_count = 0
    talk_number = 1

    for talk_data in data:
        if saved_count >= max_questions:
            break

        if not validate_talk(
            talk_data
        ):
            print(
                "Invalid talk skipped"
            )
            continue

        talk_text = (
            talk_data["talk"]
        )

        questions = (
            talk_data["questions"]
        )

        # Jangan simpan talk parsial.
        if (
            saved_count + 3
            > max_questions
        ):
            break

        start_number = (
            saved_count + 1
        )

        end_number = (
            start_number + 2
        )

        talk_filename = (
            f"{level}_"
            f"{batch_id}_"
            f"talk_"
            f"{talk_number}_"
            f"{start_number}-"
            f"{end_number}"
        )

        print(
            f"\nCreating talk audio: "
            f"{talk_filename}"
        )

        talk_audio = (
            create_talk_audio(
                talk_text,
                talk_filename,
            )
        )

        if not talk_audio:
            print(
                "Audio talk gagal dibuat. "
                "Talk dilewati."
            )
            continue

        time.sleep(1)

        # ====================================================
        # PREPARE QUESTIONS
        # ====================================================

        prepared_questions = []
        talk_valid = True

        for question in questions:
            try:
                question = (
                    shuffle_options(
                        question
                    )
                )

                if not validate_question(
                    question
                ):
                    talk_valid = False
                    break

                prepared_questions.append(
                    question
                )

            except Exception as e:
                print(
                    "Question preparation error:",
                    e,
                )

                talk_valid = False
                break

        # Jika salah satu soal invalid,
        # jangan simpan talk parsial.
        if (
            not talk_valid
            or len(prepared_questions) != 3
        ):
            print(
                "Talk memiliki soal tidak valid. "
                "Group dilewati."
            )

            # Hapus audio yang tidak dipakai
            full_audio_path = os.path.join(
                BASE_DIR,
                talk_audio,
            )

            if os.path.exists(
                full_audio_path
            ):
                try:
                    os.remove(
                        full_audio_path
                    )
                except Exception:
                    pass

            continue

        # ====================================================
        # SAVE 3 QUESTIONS
        # ====================================================

        group_saved = 0

        for question in prepared_questions:
            question_number = (
                saved_count + 1
            )

            print(
                f"Processing question "
                f"{question_number} "
                f"({level})"
            )

            try:
                insert_question(
                    part_id=PART_ID,

                    material_id=material_id,

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

                    image_file=None,

                    # Semua soal dalam talk
                    # menggunakan audio yang sama
                    audio_file=talk_audio,
                )

                saved_count += 1
                group_saved += 1

                print(
                    f"Saved to database "
                    f"({saved_count}/"
                    f"{max_questions}) ✔"
                )

            except Exception as e:
                print(
                    "Database insert error:",
                    e,
                )

            if saved_count < max_questions:
                time.sleep(
                    DELAY_BETWEEN_QUESTION
                )

        if group_saved == 3:
            talk_number += 1

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

    except (
        TypeError,
        ValueError,
    ):
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

    if jumlah < 3:
        raise ValueError(
            "Part 4 minimal menghasilkan "
            "3 soal"
        )

    # ========================================================
    # HARUS KELIPATAN 3
    # ========================================================

    if jumlah % 3 != 0:
        raise ValueError(
            "Jumlah soal Part 4 harus "
            "kelipatan 3, misalnya "
            "3, 6, 9, 12, dan seterusnya"
        )

    if jumlah > 48:
        raise ValueError(
            "Jumlah soal Part 4 maksimal "
            "48 dalam satu proses"
        )

    # ========================================================
    # MATERIAL ID
    # ========================================================

    material_id = (
        get_material_id_part4()
    )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 4"
    )

    print(
        f"Level       : {level}"
    )

    print(
        f"Jumlah soal : {jumlah}"
    )

    print(
        f"Jumlah talk : {jumlah // 3}"
    )

    print(
        f"Material ID : {material_id}"
    )

    print(
        "================================\n"
    )

    total_saved = 0
    generation_round = 1

    # ========================================================
    # GENERATE SAMPAI JUMLAH TERPENUHI
    # ========================================================

    while total_saved < jumlah:
        remaining = (
            jumlah - total_saved
        )

        if remaining < 3:
            break

        print(
            f"\nGeneration round "
            f"{generation_round}"
        )

        print(
            f"Sisa soal: {remaining}"
        )

        data = generate_questions(
            level=level,
            jumlah=remaining,
        )

        if not data:
            print(
                "Generation failed"
            )
            break

        saved = save_questions(
            level=level,
            data=data,
            material_id=material_id,
            max_questions=remaining,
        )

        total_saved += saved

        if saved == 0:
            print(
                "Tidak ada soal yang "
                "berhasil disimpan."
            )
            break

        if total_saved % 3 != 0:
            print(
                "WARNING: jumlah soal tersimpan "
                "bukan kelipatan 3."
            )
            break

        generation_round += 1

        if generation_round > 5:
            print(
                "Batas percobaan generate "
                "tercapai."
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
# MANUAL TEST
# ============================================================

if __name__ == "__main__":
    run(
        level="beginner",
        jumlah=3,
    )