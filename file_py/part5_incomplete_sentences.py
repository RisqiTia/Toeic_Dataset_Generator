import json
import time
import random
import re

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

PART_ID = 5


# ============================================================
# FIX JSON DARI LLM
# ============================================================

def fix_json(text):
    text = (
        text
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    match = re.search(
        r"\[.*\]",
        text,
        re.DOTALL,
    )

    if match:
        return match.group(0)

    return text


# ============================================================
# NORMALIZE QUESTION
# ============================================================

def normalize_question(question):
    try:
        question_text = (
            question.get("question")
            or question.get("sentence")
        )

        # ====================================================
        # OPTIONS
        # ====================================================

        if (
            "options" in question
            and isinstance(
                question["options"],
                list,
            )
            and len(question["options"]) == 4
        ):
            (
                option_a,
                option_b,
                option_c,
                option_d,
            ) = question["options"]

        else:
            option_a = (
                question.get("option_a")
                or question.get("A")
            )

            option_b = (
                question.get("option_b")
                or question.get("B")
            )

            option_c = (
                question.get("option_c")
                or question.get("C")
            )

            option_d = (
                question.get("option_d")
                or question.get("D")
            )

        options = [
            option_a,
            option_b,
            option_c,
            option_d,
        ]

        # ====================================================
        # ANSWER
        # ====================================================

        raw_answer = question.get(
            "answer"
        )

        if raw_answer is None:
            return None

        raw_answer = str(
            raw_answer
        ).strip()

        answer_letter = None

        if raw_answer.upper() in [
            "A",
            "B",
            "C",
            "D",
        ]:
            answer_letter = (
                raw_answer.upper()
            )

        else:
            # Kalau Gemini memberikan
            # teks jawaban, cari hurufnya.
            for index, option in enumerate(
                options
            ):
                if (
                    option is not None
                    and str(option).strip()
                    == raw_answer
                ):
                    answer_letter = [
                        "A",
                        "B",
                        "C",
                        "D",
                    ][index]

                    break

        return {
            "question": question_text,
            "option_a": option_a,
            "option_b": option_b,
            "option_c": option_c,
            "option_d": option_d,
            "answer": answer_letter,
            "explanation": question.get(
                "explanation",
                "",
            ),
        }

    except Exception as e:
        print(
            "Normalize error:",
            e,
        )

        return None


# ============================================================
# VALIDATE QUESTION
# ============================================================

def validate_question(question):
    if not question:
        return False

    required_fields = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
    ]

    for field in required_fields:
        value = question.get(field)

        if value is None:
            return False

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            return False

    # Part 5 wajib memiliki blank
    if "___" not in question["question"]:
        return False

    if question["answer"] not in [
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

    # Semua pilihan harus berbeda.
    normalized_options = [
        str(option)
        .strip()
        .lower()
        for option in options
    ]

    if len(
        set(normalized_options)
    ) != 4:
        return False

    return True


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
        return None

    correct_text = dict(
        options
    ).get(answer)

    if correct_text is None:
        return None

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

        new_options[
            new_letter
        ] = text

        if text == correct_text:
            new_answer = new_letter

    if new_answer is None:
        print(
            "Shuffle gagal menentukan "
            "jawaban benar"
        )
        return None

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

    return question


# ============================================================
# GENERATE QUESTIONS
# ============================================================

def generate_questions(
    level,
    jumlah,
):
    prompt = f"""
Generate exactly {jumlah} TOEIC Part 5
Incomplete Sentences questions.

Difficulty level: {level}

TOEIC Part 5 rules:
- Create EXACTLY {jumlah} questions.
- Every question must be an incomplete sentence.
- Every sentence MUST contain exactly one blank written as ___.
- Each question must have exactly 4 answer choices.
- Only one answer can correctly complete the sentence.
- Distractors must be grammatically or contextually plausible.
- Correct answers should vary between A, B, C, and D.

Question topics should include a variety of:
- verb tense
- subject-verb agreement
- word forms
- prepositions
- conjunctions
- pronouns
- relative clauses
- adjectives
- adverbs
- vocabulary
- business expressions
- workplace vocabulary

Difficulty:
- beginner: common vocabulary and basic grammar
- intermediate: more varied grammar and business vocabulary
- advanced: complex grammar, vocabulary, and sentence structure

IMPORTANT:
- Question must be written in English.
- Options must be written in English.
- Explanation MUST be written in Bahasa Indonesia.
- Explanation should explain the grammar, vocabulary,
  or context that makes the answer correct.
- Do NOT mention option letters A/B/C/D
  in the explanation.
- Do NOT include Markdown.
- Do NOT include comments.
- Return valid JSON only.
- Return EXACTLY {jumlah} objects.

JSON format:

[
  {{
    "question": "The manager ___ the report before the meeting.",
    "options": [
      "reviewed",
      "reviewing",
      "review",
      "reviews"
    ],
    "answer": "A",
    "explanation": "Kalimat ini membutuhkan bentuk kata kerja yang sesuai dengan konteks waktu dan struktur kalimat."
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

            raw_text = (
                response.text
            )

            cleaned_text = fix_json(
                raw_text
            )

            data = json.loads(
                cleaned_text
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

            print(
                f"Gemini menghasilkan "
                f"{len(data)} soal"
            )

            # Jika Gemini memberikan
            # lebih banyak dari permintaan.
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
# GET MATERIAL ID PART 5
# ============================================================

def get_material_id_part5():
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
            WHERE part_id = 5
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if not row:
            raise ValueError(
                "Tidak ada material untuk Part 5. "
                "Buat minimal 1 material Part 5 "
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
    saved_count = 0

    for index, raw_question in enumerate(
        questions
    ):
        if saved_count >= max_questions:
            break

        print(
            f"Processing question "
            f"{index + 1} "
            f"({level})"
        )

        # ====================================================
        # NORMALIZE
        # ====================================================

        question = normalize_question(
            raw_question
        )

        if not question:
            print(
                "Format soal tidak dapat "
                "dinormalisasi"
            )
            continue

        # ====================================================
        # VALIDATE
        # ====================================================

        if not validate_question(
            question
        ):
            print(
                "Soal tidak valid / "
                "bukan incomplete sentence"
            )
            continue

        # ====================================================
        # SHUFFLE
        # ====================================================

        question = shuffle_options(
            question
        )

        if not question:
            print(
                "Gagal melakukan shuffle"
            )
            continue

        # ====================================================
        # EXPLANATION
        # ====================================================

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
                f"Kata atau frasa "
                f"\"{correct_text}\" paling "
                "tepat untuk melengkapi "
                "kalimat karena sesuai dengan "
                "struktur tata bahasa dan "
                "konteks kalimat."
            )

        # ====================================================
        # DATABASE
        # ====================================================

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

                explanation=explanation,

                image_file=None,

                audio_file=None,
            )

            saved_count += 1

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

    # ========================================================
    # VALIDASI LEVEL
    # ========================================================

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

    # ========================================================
    # VALIDASI JUMLAH
    # ========================================================

    if jumlah < 1:
        raise ValueError(
            "Jumlah soal minimal 1"
        )

    if jumlah > 50:
        raise ValueError(
            "Jumlah soal maksimal 50 "
            "dalam satu proses"
        )

    # ========================================================
    # MATERIAL
    # ========================================================

    material_id = (
        get_material_id_part5()
    )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 5"
    )

    print(
        f"Level       : {level}"
    )

    print(
        f"Jumlah soal : {jumlah}"
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

        # Mencegah loop tidak terbatas
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
        jumlah=1,
    )