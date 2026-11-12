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


PART_ID = 7
QUESTIONS_PER_TEXT = 4


# ============================================================
# FIX JSON
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
# SHUFFLE OPTIONS
# ============================================================

def shuffle_options(q):
    options = [
        ("A", q["option_a"]),
        ("B", q["option_b"]),
        ("C", q["option_c"]),
        ("D", q["option_d"]),
    ]

    answer = str(
        q.get("answer", "")
    ).strip().upper()

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
        letter = letters[index]

        new_options[letter] = text

        if text == correct_text:
            new_answer = letter

    if new_answer is None:
        print(
            "Shuffle gagal menentukan "
            "jawaban benar"
        )
        return None

    q["option_a"] = new_options["A"]
    q["option_b"] = new_options["B"]
    q["option_c"] = new_options["C"]
    q["option_d"] = new_options["D"]
    q["answer"] = new_answer

    return q


# ============================================================
# VALIDATE QUESTION
# ============================================================

def validate_question(q):
    if not q:
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
        value = q.get(field)

        if value is None:
            return False

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            return False

    question = str(
        q["question"]
    ).strip()

    # Harus berupa pertanyaan
    if "?" not in question:
        return False

    answer = str(
        q["answer"]
    ).strip().upper()

    if answer not in [
        "A",
        "B",
        "C",
        "D",
    ]:
        return False

    # Pastikan opsi berbeda
    options = [
        str(q["option_a"]).strip().lower(),
        str(q["option_b"]).strip().lower(),
        str(q["option_c"]).strip().lower(),
        str(q["option_d"]).strip().lower(),
    ]

    if len(set(options)) != 4:
        return False

    return True


# ============================================================
# GENERATE TEXT + QUESTIONS
# ============================================================

def generate_text_with_questions(
    level,
    text_count,
    max_retries=5,
):
    total_questions = (
        text_count
        * QUESTIONS_PER_TEXT
    )

    prompt = f"""
Generate TOEIC Part 7 Reading Comprehension questions.

Difficulty level: {level}

Create EXACTLY {text_count} different reading texts.

Each text MUST contain exactly 4 questions.

Therefore:
- Number of texts: {text_count}
- Questions per text: 4
- Total questions: {total_questions}

TEXT RULES:

Each reading text can be:
- email
- memo
- notice
- advertisement
- article
- announcement
- letter
- schedule
- business message
- company information

Each text should contain approximately 1-3 paragraphs.

Use realistic TOEIC contexts such as:
- workplace communication
- business
- travel
- meetings
- schedules
- customer service
- events
- office activities
- advertisements
- company announcements

Do not create identical texts.

QUESTION RULES:

Each text MUST have exactly 4 questions.

Questions should test different reading skills such as:
- main idea
- purpose
- specific information
- inference
- vocabulary in context
- intended audience
- reason
- time or location

Each question MUST be a complete interrogative sentence.

Prefer question forms such as:
- What
- Why
- When
- Where
- Who
- How

Every question must contain:
- question
- option_a
- option_b
- option_c
- option_d
- answer
- explanation

Every question must have exactly 4 different options.

Only one option may be correct.

Distractors must be plausible based on the text.

Correct answers should vary between:
A, B, C, D

DIFFICULTY:

Beginner:
- shorter and simpler text
- common workplace vocabulary
- mostly explicit information
- straightforward questions

Intermediate:
- more detailed text
- business vocabulary
- explicit information and simple inference
- moderately challenging distractors

Advanced:
- more complex text
- advanced business vocabulary
- inference and contextual understanding
- subtle distractors

LANGUAGE RULES:

- Reading text MUST be English.
- Questions MUST be English.
- Options MUST be English.
- Explanation MUST be Bahasa Indonesia.

The explanation:
- must explain why the answer is correct
- must refer to information from the reading text
- must NOT mention option letters A/B/C/D

IMPORTANT:

Return VALID JSON ONLY.

Do NOT use Markdown.

Do NOT include comments.

Do NOT include text outside JSON.

Return EXACTLY {text_count} objects.

JSON format:

[
    {{
        "text": "Reading passage...",
        "questions": [
            {{
                "question": "What is the purpose of the email?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "A",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            }},
            {{
                "question": "When will the event take place?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "B",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            }},
            {{
                "question": "Why did the writer contact the recipient?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "C",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            }},
            {{
                "question": "What is suggested about the company?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "D",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            }}
        ]
    }}
]

Generate exactly:
{text_count} texts
and
{total_questions} total questions.
"""

    for attempt in range(
        max_retries
    ):
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

            raw = response.text

            cleaned = fix_json(
                raw
            )

            data = json.loads(
                cleaned
            )

            # =================================================
            # VALIDASI LIST
            # =================================================

            if not isinstance(
                data,
                list,
            ):
                print(
                    "Output Gemini bukan list"
                )

                time.sleep(5)
                continue

            # =================================================
            # VALIDASI JUMLAH TEXT
            # =================================================

            if len(data) != text_count:
                print(
                    f"Jumlah text salah. "
                    f"Target {text_count}, "
                    f"dapat {len(data)}"
                )

                time.sleep(5)
                continue

            valid = True
            calculated_questions = 0

            # =================================================
            # VALIDASI SETIAP TEXT
            # =================================================

            for index, item in enumerate(
                data
            ):
                text_content = str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()

                if not text_content:
                    print(
                        f"Text {index + 1} kosong"
                    )

                    valid = False
                    break

                questions = item.get(
                    "questions",
                    [],
                )

                if not isinstance(
                    questions,
                    list,
                ):
                    print(
                        f"Questions text "
                        f"{index + 1} bukan list"
                    )

                    valid = False
                    break

                if len(
                    questions
                ) != QUESTIONS_PER_TEXT:

                    print(
                        f"Text {index + 1} "
                        "tidak mempunyai "
                        "4 soal"
                    )

                    valid = False
                    break

                # Validasi setiap soal
                for question in questions:
                    if not validate_question(
                        question
                    ):
                        print(
                            f"Soal pada text "
                            f"{index + 1} "
                            "tidak valid"
                        )

                        valid = False
                        break

                if not valid:
                    break

                calculated_questions += (
                    len(questions)
                )

            if not valid:
                print(
                    "Validasi gagal. "
                    "Generate ulang..."
                )

                time.sleep(5)
                continue

            # =================================================
            # TOTAL QUESTION
            # =================================================

            if (
                calculated_questions
                != total_questions
            ):
                print(
                    "Jumlah total soal "
                    "tidak sesuai"
                )

                time.sleep(5)
                continue

            print(
                f"Berhasil generate "
                f"{text_count} text / "
                f"{total_questions} soal"
            )

            return data

        except Exception as e:
            error = str(e)

            if (
                "503" in error
                or
                "UNAVAILABLE" in error
            ):
                wait = (
                    30 * (attempt + 1)
                )

                print(
                    "Gemini sedang sibuk. "
                    f"Menunggu {wait} detik..."
                )

                time.sleep(wait)

            elif (
                "429" in error
                or
                "RESOURCE_EXHAUSTED"
                in error
            ):
                print(
                    "Rate limit Gemini. "
                    "Menunggu 60 detik..."
                )

                time.sleep(60)

            else:
                print(
                    "LLM error:",
                    e,
                )

                time.sleep(10)

    return None


# ============================================================
# GET MATERIAL PART 7
# ============================================================

def get_material_id_part7():
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
            WHERE part_id = 7
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if not row:
            raise ValueError(
                "Material Part 7 belum "
                "tersedia di tabel materials."
            )

        return row[0]

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# SAVE TEXT + QUESTIONS
# ============================================================

def save_text_with_questions(
    level,
    texts,
    material_id,
):
    saved = 0
    skipped = 0

    total_questions = sum(
        len(
            item.get(
                "questions",
                [],
            )
        )
        for item in texts
    )

    global_question_number = 1

    for text_index, item in enumerate(
        texts
    ):
        text_content = str(
            item.get(
                "text",
                "",
            )
        ).strip()

        questions = item.get(
            "questions",
            [],
        )

        if (
            not text_content
            or not questions
        ):
            print(
                f"Text {text_index + 1} "
                "tidak valid"
            )

            skipped += len(
                questions
            )

            continue

        print(
            f"\nReading Text "
            f"{text_index + 1}"
        )

        # ====================================================
        # QUESTIONS
        # ====================================================

        for question_index, q in enumerate(
            questions
        ):
            print(
                f"Processing question "
                f"{global_question_number}/"
                f"{total_questions} "
                f"({level})"
            )

            global_question_number += 1

            # ================================================
            # VALIDASI
            # ================================================

            if not validate_question(q):
                print(
                    "Format soal tidak valid"
                )

                skipped += 1
                continue

            # ================================================
            # SHUFFLE
            # ================================================

            shuffled = shuffle_options({
                "option_a":
                    q["option_a"],

                "option_b":
                    q["option_b"],

                "option_c":
                    q["option_c"],

                "option_d":
                    q["option_d"],

                "answer":
                    str(
                        q["answer"]
                    ).strip().upper(),
            })

            if not shuffled:
                print(
                    "Shuffle options gagal"
                )

                skipped += 1
                continue

            # ================================================
            # QUESTION TEXT
            # ================================================

            question_text = (
                f"{text_content}\n\n"
                f"{str(q['question']).strip()}"
            )

            # ================================================
            # EXPLANATION
            # ================================================

            explanation = str(
                q.get(
                    "explanation",
                    "",
                )
            ).strip()

            if not explanation:
                correct_letter = (
                    shuffled["answer"]
                    .lower()
                )

                correct_text = (
                    shuffled[
                        f"option_{correct_letter}"
                    ]
                )

                explanation = (
                    f"Jawaban \"{correct_text}\" "
                    "dapat ditentukan berdasarkan "
                    "informasi yang terdapat dalam "
                    "teks bacaan."
                )

            # ================================================
            # INSERT DATABASE
            # ================================================

            try:
                insert_question(
                    part_id=PART_ID,

                    material_id=material_id,

                    difficulty_level=level,

                    question_text=(
                        question_text
                    ),

                    option_a=(
                        shuffled["option_a"]
                    ),

                    option_b=(
                        shuffled["option_b"]
                    ),

                    option_c=(
                        shuffled["option_c"]
                    ),

                    option_d=(
                        shuffled["option_d"]
                    ),

                    correct_answer=(
                        shuffled["answer"]
                    ),

                    explanation=(
                        explanation
                    ),

                    image_file=None,

                    audio_file=None,
                )

                saved += 1

                print(
                    f"Saved "
                    f"({saved}/"
                    f"{total_questions}) ✔"
                )

            except Exception as e:
                print(
                    "Database error:",
                    e,
                )

                skipped += 1

            if (
                saved + skipped
                < total_questions
            ):
                time.sleep(
                    DELAY_BETWEEN_QUESTION
                )

    print(
        f"\nSaved: {saved}, "
        f"Skipped: {skipped}"
    )

    return saved


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

    if jumlah < 4:
        raise ValueError(
            "Part 7 minimal 4 soal"
        )

    if jumlah % 4 != 0:
        raise ValueError(
            "Jumlah soal Part 7 harus "
            "kelipatan 4 "
            "(4, 8, 12, 16, ...)"
        )

    if jumlah > 40:
        raise ValueError(
            "Maksimal 40 soal dalam "
            "satu proses generate"
        )

    text_count = (
        jumlah
        // QUESTIONS_PER_TEXT
    )

    # ========================================================
    # MATERIAL
    # ========================================================

    material_id = (
        get_material_id_part7()
    )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 7"
    )

    print(
        f"Level       : {level}"
    )

    print(
        f"Jumlah soal : {jumlah}"
    )

    print(
        f"Reading text: {text_count}"
    )

    print(
        f"Material ID : {material_id}"
    )

    print(
        "================================\n"
    )

    # ========================================================
    # GENERATE
    # ========================================================

    texts = (
        generate_text_with_questions(
            level=level,
            text_count=text_count,
        )
    )

    if not texts:
        print(
            "Gagal generate Part 7"
        )

        return 0

    # ========================================================
    # SAVE
    # ========================================================

    total_saved = (
        save_text_with_questions(
            level=level,
            texts=texts,
            material_id=material_id,
        )
    )

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
        jumlah=4,
    )