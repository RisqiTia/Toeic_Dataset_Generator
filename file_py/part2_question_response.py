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
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

AUDIO_DIR = os.path.join(
    BASE_DIR,
    "part2",
    "audio",
    "question",
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True,
)


# ============================================================
# SHUFFLE OPTIONS
# Part 2 hanya memiliki 3 pilihan: A, B, C
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
    ]

    original_answer = (
        str(question["answer"])
        .strip()
        .upper()
    )

    if original_answer not in [
        "A",
        "B",
        "C",
    ]:
        raise ValueError(
            "Jawaban Part 2 harus A, B, atau C"
        )

    correct_text = dict(
        options
    )[original_answer]

    random.shuffle(options)

    letters = [
        "A",
        "B",
        "C",
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

    question["option_d"] = ""

    question["answer"] = (
        new_answer
    )

    return question


# ============================================================
# CREATE AUDIO
# ============================================================

def create_audio(
    question,
    option_a,
    option_b,
    option_c,
    filename,
):
    try:
        audio_text = f"""
{question}

A. {option_a}
B. {option_b}
C. {option_c}
"""

        filename_with_ext = (
            f"{filename}.mp3"
        )

        full_path = os.path.join(
            AUDIO_DIR,
            filename_with_ext,
        )

        tts = gTTS(
            text=audio_text,
            lang="en",
        )

        tts.save(
            full_path
        )

        # Path yang disimpan ke database.
        return (
            "part2/audio/question/"
            f"{filename_with_ext}"
        )

    except Exception as e:
        print(
            "Audio error:",
            e,
        )

        return None


# ============================================================
# VALIDASI QUESTION
# ============================================================

def validate_question(question):
    required_fields = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "answer",
        "explanation",
    ]

    for field in required_fields:

        if field not in question:
            print(
                f"Field {field} tidak ditemukan"
            )
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
    ]:
        return False

    return True


# ============================================================
# GENERATE QUESTIONS VIA GEMINI
# ============================================================

def generate_questions(
    level,
    jumlah,
):
    prompt = f"""
Generate exactly {jumlah} TOEIC Part 2 Question-Response questions.

Difficulty level: {level}

TOEIC Part 2 rules:
- Each item consists of one spoken question or statement.
- Each item must have exactly 3 possible responses: A, B, and C.
- There is NO option D.
- Only one response is the most appropriate.
- Distractors must sound plausible but must not correctly respond to the question or statement.
- Use natural spoken English.
- Use realistic TOEIC workplace and everyday contexts.
- Include varied question types such as:
  Who, What, When, Where, Why, How,
  Yes/No questions,
  requests,
  suggestions,
  offers,
  and statements.
- Adjust vocabulary and sentence complexity to the {level} level.
- Correct answers must vary between A, B, and C.

IMPORTANT:
- question must be written in English.
- option_a, option_b, and option_c must be written in English.
- option_d must always be an empty string.
- explanation MUST be written in Bahasa Indonesia.
- Explanation must clearly explain why the correct response is appropriate.
- Do NOT mention the answer letter A, B, or C in the explanation.
- Do NOT write comments inside JSON.
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
    "explanation": ""
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

            # Ambil JSON array saja.
            start = text.find("[")
            end = text.rfind("]")

            if start == -1 or end == -1:
                raise ValueError(
                    "JSON array tidak ditemukan"
                )

            text = text[
                start:end + 1
            ]

            data = json.loads(
                text
            )

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

            # Jika Gemini menghasilkan lebih banyak,
            # batasi sesuai permintaan.
            return data[:jumlah]

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
# GET MATERIAL ID PART 2
# ============================================================

def get_material_id_part2():
    connection = None
    cursor = None

    try:
        connection = (
            get_connection()
        )

        cursor = (
            connection.cursor()
        )

        cursor.execute(
            """
            SELECT id
            FROM materials
            WHERE part_id = 2
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if not row:
            raise ValueError(
                "Tidak ada material untuk Part 2. "
                "Buat minimal 1 material Part 2 "
                "pada tabel materials."
            )

        return row[0]

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# SAVE QUESTIONS
# ============================================================

def save_questions(
    level,
    questions,
    material_id,
    max_questions,
):
    batch_id = (
        f"{int(time.time())}_"
        f"{random.randint(1000, 9999)}"
    )

    saved_count = 0

    for index, question in enumerate(
        questions
    ):

        if saved_count >= max_questions:
            break

        print(
            f"Processing question "
            f"{index + 1} "
            f"({level})"
        )

        try:

            # --------------------------------------------
            # VALIDASI
            # --------------------------------------------

            if not validate_question(
                question
            ):
                print(
                    "Question tidak valid, "
                    "dilewati."
                )
                continue

            # --------------------------------------------
            # SHUFFLE
            # --------------------------------------------

            question = (
                shuffle_options(
                    question
                )
            )

            # --------------------------------------------
            # EXPLANATION
            # --------------------------------------------

            explanation = (
                str(
                    question.get(
                        "explanation",
                        "",
                    )
                )
                .strip()
            )

            if not explanation:

                correct_letter = (
                    question["answer"]
                    .lower()
                )

                correct_text = (
                    question[
                        f"option_{correct_letter}"
                    ]
                )

                explanation = (
                    "Respons tersebut paling sesuai "
                    "dengan konteks pertanyaan, yaitu "
                    f"\"{correct_text}\". Respons ini "
                    "memberikan jawaban yang relevan "
                    "dan logis terhadap pertanyaan "
                    "yang diberikan."
                )

            # --------------------------------------------
            # FILENAME
            # --------------------------------------------

            filename = (
                f"{level}_"
                f"{batch_id}_"
                f"{index + 1}"
            )

            # --------------------------------------------
            # AUDIO
            # --------------------------------------------

            print(
                "Creating audio..."
            )

            audio_path = (
                create_audio(
                    question["question"],
                    question["option_a"],
                    question["option_b"],
                    question["option_c"],
                    filename,
                )
            )

            # --------------------------------------------
            # DATABASE
            # --------------------------------------------

            insert_question(
                part_id=2,

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

                option_d="",

                correct_answer=(
                    question["answer"]
                ),

                explanation=explanation,

                image_file=None,

                audio_file=audio_path,
            )

            saved_count += 1

            print(
                f"Saved to database "
                f"({saved_count}/"
                f"{max_questions}) ✔"
            )

        except Exception as e:

            print(
                "Question processing error:",
                e,
            )

        if saved_count < max_questions:

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
        jumlah = int(
            jumlah
        )

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

    if jumlah < 1:

        raise ValueError(
            "Jumlah soal minimal 1"
        )

    if jumlah > 50:

        raise ValueError(
            "Jumlah soal maksimal 50"
        )

    # ========================================================
    # MATERIAL
    # ========================================================

    material_id = (
        get_material_id_part2()
    )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 2"
    )

    print(
        f"Level       : {level}"
    )

    print(
        f"Jumlah      : {jumlah}"
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

        generation_round += 1

        # Mencegah loop tanpa batas.
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
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    run(
        level="beginner",
        jumlah=1,
    )