import json
import time
import random
import re

from config import (
    client,
    DELAY_BETWEEN_QUESTION,
)

from db import (
    insert_question,
    get_connection,
)


PART_ID = 6
QUESTIONS_PER_PASSAGE = 4


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

    correct_text = dict(options).get(
        answer
    )

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
        return None

    q["option_a"] = new_options["A"]
    q["option_b"] = new_options["B"]
    q["option_c"] = new_options["C"]
    q["option_d"] = new_options["D"]
    q["answer"] = new_answer

    return q


# ============================================================
# GENERATE QUESTIONS
# ============================================================

def generate_questions(
    level,
    passage_count,
    max_retries=5,
):
    total_questions = (
        passage_count
        * QUESTIONS_PER_PASSAGE
    )

    prompt = f"""
Generate TOEIC Part 6 Text Completion questions.

Difficulty level: {level}

Create EXACTLY {passage_count} different passages.

Each passage MUST contain exactly 4 questions.

Therefore:
- Number of passages: {passage_count}
- Questions per passage: 4
- Total questions: {total_questions}

PASSAGE RULES:

Each passage can be:
- email
- memo
- announcement
- letter
- notice
- advertisement
- article
- business correspondence

Each passage MUST contain exactly four blanks:

___(1)___
___(2)___
___(3)___
___(4)___

IMPORTANT:

For every passage, create exactly four question objects.

Question 1 asks about ___(1)___.
Question 2 asks about ___(2)___.
Question 3 asks about ___(3)___.
Question 4 asks about ___(4)___.

The FULL passage MUST be repeated identically
for all four questions belonging to the same passage.

DO NOT fill the other blanks.

For example, when asking blank (2),
the passage must STILL contain:

___(1)___
___(2)___
___(3)___
___(4)___

QUESTION RULES:

Each question must contain:
- passage
- blank_number
- question
- option_a
- option_b
- option_c
- option_d
- answer
- explanation

The answer must be one of:
A, B, C, D

Correct answers should vary.

All four options must be different.

The options must be plausible TOEIC distractors.

Difficulty rules:

beginner:
- basic grammar
- common vocabulary
- simple sentence relationships

intermediate:
- business vocabulary
- conjunctions
- word forms
- tense
- contextual relationships

advanced:
- complex grammar
- advanced vocabulary
- discourse relationships
- sentence insertion/contextual reasoning

LANGUAGE:

- Passage: English
- Question: English
- Options: English
- Explanation: Bahasa Indonesia

The explanation must:
- explain why the answer is correct
- be based on grammar or context
- NOT mention option letters A/B/C/D

Return VALID JSON ONLY.

Do not use Markdown.

Do not write anything outside JSON.

Output format:

[
    {{
        "passage": "Full passage containing ___(1)___, ___(2)___, ___(3)___, and ___(4)___.",
        "blank_number": 1,
        "question": "What best completes blank (1)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "A",
        "explanation": "Penjelasan Bahasa Indonesia."
    }},
    {{
        "passage": "SAME EXACT PASSAGE",
        "blank_number": 2,
        "question": "What best completes blank (2)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "B",
        "explanation": "Penjelasan Bahasa Indonesia."
    }},
    {{
        "passage": "SAME EXACT PASSAGE",
        "blank_number": 3,
        "question": "What best completes blank (3)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "C",
        "explanation": "Penjelasan Bahasa Indonesia."
    }},
    {{
        "passage": "SAME EXACT PASSAGE",
        "blank_number": 4,
        "question": "What best completes blank (4)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "D",
        "explanation": "Penjelasan Bahasa Indonesia."
    }}
]

Generate EXACTLY {total_questions} question objects.
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

            cleaned = fix_json(raw)

            data = json.loads(
                cleaned
            )

            if not isinstance(
                data,
                list,
            ):
                print(
                    "Output bukan list"
                )
                time.sleep(5)
                continue

            if len(data) != total_questions:
                print(
                    f"Jumlah soal salah. "
                    f"Target {total_questions}, "
                    f"dapat {len(data)}"
                )

                time.sleep(5)
                continue

            # ================================================
            # VALIDASI GROUP
            # ================================================

            valid = True

            for group_start in range(
                0,
                total_questions,
                4,
            ):
                group = data[
                    group_start:
                    group_start + 4
                ]

                if len(group) != 4:
                    valid = False
                    break

                passages = [
                    str(
                        q.get(
                            "passage",
                            "",
                        )
                    ).strip()
                    for q in group
                ]

                # Passage harus identik
                if (
                    len(set(passages))
                    != 1
                ):
                    print(
                        "Passage dalam satu "
                        "group tidak identik"
                    )

                    valid = False
                    break

                passage = passages[0]

                # Semua blank wajib ada
                for blank in range(
                    1,
                    5,
                ):
                    marker = (
                        f"___({blank})___"
                    )

                    if marker not in passage:
                        print(
                            f"Blank {marker} "
                            "tidak ditemukan"
                        )

                        valid = False
                        break

                if not valid:
                    break

                blank_numbers = []

                for q in group:
                    try:
                        number = int(
                            q.get(
                                "blank_number"
                            )
                        )

                        blank_numbers.append(
                            number
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):
                        valid = False
                        break

                if not valid:
                    break

                if sorted(
                    blank_numbers
                ) != [1, 2, 3, 4]:

                    print(
                        "Nomor blank dalam "
                        "group tidak lengkap"
                    )

                    valid = False
                    break

            if not valid:
                print(
                    "Validasi group gagal. "
                    "Generate ulang..."
                )

                time.sleep(5)
                continue

            print(
                f"Berhasil generate "
                f"{passage_count} passage / "
                f"{total_questions} soal"
            )

            return data

        except Exception as e:
            error = str(e)

            if (
                "503" in error
                or "UNAVAILABLE" in error
            ):
                wait = (
                    30 * (attempt + 1)
                )

                print(
                    "Gemini sedang sibuk. "
                    f"Retry {wait} detik..."
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
# GET MATERIAL PART 6
# ============================================================

def get_material_id_part6():
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
            WHERE part_id = 6
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if not row:
            raise ValueError(
                "Material Part 6 belum "
                "tersedia di tabel materials."
            )

        return row[0]

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# VALIDATE QUESTION
# ============================================================

def validate_question(q):
    if not q:
        return False

    try:
        blank_number = int(
            q.get("blank_number")
        )

    except (
        TypeError,
        ValueError,
    ):
        return False

    if blank_number not in [
        1,
        2,
        3,
        4,
    ]:
        return False

    required = [
        "passage",
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "answer",
    ]

    for field in required:
        value = q.get(field)

        if value is None:
            return False

        if (
            isinstance(value, str)
            and not value.strip()
        ):
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

    options = [
        str(q["option_a"]).strip(),
        str(q["option_b"]).strip(),
        str(q["option_c"]).strip(),
        str(q["option_d"]).strip(),
    ]

    if len(
        set(
            option.lower()
            for option in options
        )
    ) != 4:
        return False

    passage = str(
        q["passage"]
    )

    for blank in range(
        1,
        5,
    ):
        if (
            f"___({blank})___"
            not in passage
        ):
            return False

    return True


# ============================================================
# SAVE QUESTIONS
# ============================================================

def save_questions(
    level,
    questions,
    material_id,
):
    saved = 0
    skipped = 0

    total = len(
        questions
    )

    for index, q in enumerate(
        questions
    ):
        print(
            f"Processing "
            f"{index + 1}/{total} "
            f"[{level}]"
        )

        if not validate_question(q):
            print(
                "Format soal tidak valid"
            )

            skipped += 1
            continue

        passage = str(
            q["passage"]
        ).strip()

        question = str(
            q["question"]
        ).strip()

        # ====================================================
        # QUESTION TEXT
        # ====================================================

        question_text = (
            f"{passage}\n\n"
            f"{question}"
        )

        # ====================================================
        # SHUFFLE
        # ====================================================

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
                "Shuffle gagal"
            )

            skipped += 1
            continue

        # ====================================================
        # EXPLANATION
        # ====================================================

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
                "paling sesuai untuk "
                "melengkapi bagian kosong "
                "berdasarkan struktur "
                "kalimat dan konteks teks."
            )

        # ====================================================
        # INSERT DATABASE
        # ====================================================

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
                f"({saved}/{total}) ✔"
            )

        except Exception as e:
            print(
                "Database error:",
                e,
            )

            skipped += 1

        if index < total - 1:
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
            "Part 6 minimal 4 soal"
        )

    if jumlah % 4 != 0:
        raise ValueError(
            "Jumlah soal Part 6 harus "
            "kelipatan 4 "
            "(4, 8, 12, 16, ...)"
        )

    if jumlah > 40:
        raise ValueError(
            "Maksimal 40 soal dalam "
            "satu proses generate"
        )

    passage_count = (
        jumlah // 4
    )

    # ========================================================
    # MATERIAL
    # ========================================================

    material_id = (
        get_material_id_part6()
    )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 6"
    )

    print(
        f"Level       : {level}"
    )

    print(
        f"Jumlah soal : {jumlah}"
    )

    print(
        f"Passage     : {passage_count}"
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

    questions = generate_questions(
        level=level,
        passage_count=passage_count,
    )

    if not questions:
        print(
            "Gagal generate Part 6"
        )

        return 0

    # ========================================================
    # SAVE
    # ========================================================

    total_saved = save_questions(
        level=level,
        questions=questions,
        material_id=material_id,
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