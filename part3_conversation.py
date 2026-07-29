import os
import json
import time
import random

from gtts import gTTS

from config import (
    client,
    DELAY_BETWEEN_QUESTION,
)

from db import insert_question


# ============================================================
# CONFIG
# ============================================================

PART_ID = 3
MATERIAL_ID = 35


# ============================================================
# DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

AUDIO_DIR = os.path.join(
    BASE_DIR,
    "part3",
    "audio",
    "conversation",
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True,
)


# ============================================================
# CREATE CONVERSATION AUDIO
# ============================================================

def create_conversation_audio(
    text,
    filename,
):
    try:
        full_path = os.path.join(
            AUDIO_DIR,
            f"{filename}.mp3",
        )

        tts = gTTS(
            text=text,
            lang="en",
        )

        tts.save(full_path)

        # Path yang disimpan ke database
        return (
            "part3/audio/conversation/"
            f"{filename}.mp3"
        )

    except Exception as e:
        print(
            "Conversation audio error:",
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
# VALIDATE CONVERSATION
# ============================================================

def validate_conversation(conversation):
    if not isinstance(
        conversation,
        dict,
    ):
        return False

    conversation_text = (
        conversation.get(
            "conversation",
            "",
        )
    )

    questions = conversation.get(
        "questions",
        [],
    )

    if not str(
        conversation_text
    ).strip():
        return False

    if not isinstance(
        questions,
        list,
    ):
        return False

    # Kita gunakan tepat 3 soal
    # untuk setiap conversation.
    if len(questions) != 3:
        return False

    for question in questions:
        if not validate_question(
            question
        ):
            return False

    return True


# ============================================================
# GENERATE CONVERSATIONS WITH GEMINI
# ============================================================

def generate_questions(
    level,
    jumlah,
):
    total_conversations = (
        jumlah // 3
    )

    prompt = f"""
Generate TOEIC Part 3 Conversations.

Difficulty level: {level}

Create exactly {total_conversations} conversations.

IMPORTANT:
- Each conversation MUST contain exactly 3 questions.
- Therefore the total number of questions MUST be exactly {jumlah}.

TOEIC Part 3 rules:
- Each conversation is spoken by 2 or 3 people.
- Each conversation should contain approximately 4 to 8 dialogue lines.
- Use natural spoken English.
- Use realistic TOEIC contexts such as:
  office,
  meetings,
  business,
  travel,
  hotels,
  restaurants,
  customer service,
  appointments,
  education,
  stores,
  transportation,
  workplace situations.
- Questions must test comprehension of the conversation.
- Include different question types such as:
  main purpose,
  speaker intention,
  location,
  problem,
  suggestion,
  next action,
  specific detail,
  implied meaning.
- Each question must have exactly 4 choices: A, B, C, D.
- Only one answer may be correct.
- Distractors must be plausible.
- Correct answers should vary between A, B, C, and D.
- Adjust vocabulary and complexity to the {level} level.

IMPORTANT LANGUAGE RULES:
- Conversation must be in English.
- Questions must be in English.
- Options must be in English.
- Explanation MUST be in Bahasa Indonesia.
- Explanation must explain why the answer is correct based on the conversation.
- Do NOT mention option letters A/B/C/D in the explanation.

Return valid JSON only.
Do NOT return Markdown.
Do NOT use ```json.

JSON format:

[
  {{
    "conversation": "Man: ...\\nWoman: ...",
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
- {total_conversations} conversations
- 3 questions per conversation
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
                    "Gemini tidak menghasilkan conversation"
                )

            # Ambil sesuai jumlah conversation
            data = data[
                :total_conversations
            ]

            valid_data = []

            for conversation in data:
                if validate_conversation(
                    conversation
                ):
                    valid_data.append(
                        conversation
                    )
                else:
                    print(
                        "Conversation tidak valid "
                        "dan akan dilewati."
                    )

            if valid_data:
                return valid_data

            raise ValueError(
                "Tidak ada conversation valid"
            )

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
# SAVE CONVERSATIONS
# ============================================================

def save_questions(
    level,
    data,
    max_questions,
):
    batch_id = (
        f"{int(time.time())}_"
        f"{random.randint(1000, 9999)}"
    )

    saved_count = 0
    conversation_number = 1

    for conversation_data in data:
        if saved_count >= max_questions:
            break

        if not validate_conversation(
            conversation_data
        ):
            print(
                "Invalid conversation skipped"
            )
            continue

        conversation = (
            conversation_data[
                "conversation"
            ]
        )

        questions = (
            conversation_data[
                "questions"
            ]
        )

        # Jangan simpan conversation parsial.
        # Harus tersedia ruang untuk 3 soal.
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

        conv_filename = (
            f"{level}_"
            f"{batch_id}_"
            f"conv_"
            f"{conversation_number}_"
            f"{start_number}-"
            f"{end_number}"
        )

        print(
            f"\nCreating conversation audio: "
            f"{conv_filename}"
        )

        conversation_audio = (
            create_conversation_audio(
                conversation,
                conv_filename,
            )
        )

        if not conversation_audio:
            print(
                "Audio conversation gagal dibuat. "
                "Conversation dilewati."
            )
            continue

        time.sleep(1)

        # ================================================
        # Siapkan seluruh soal dahulu
        # ================================================

        prepared_questions = []

        conversation_valid = True

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
                    conversation_valid = False
                    break

                prepared_questions.append(
                    question
                )

            except Exception as e:
                print(
                    "Question preparation error:",
                    e,
                )

                conversation_valid = False
                break

        # Jika salah satu soal rusak,
        # jangan simpan group parsial.
        if (
            not conversation_valid
            or len(prepared_questions) != 3
        ):
            print(
                "Conversation memiliki soal "
                "tidak valid. Group dilewati."
            )

            # Hapus audio yang tidak digunakan
            audio_full_path = os.path.join(
                BASE_DIR,
                conversation_audio,
            )

            if os.path.exists(
                audio_full_path
            ):
                try:
                    os.remove(
                        audio_full_path
                    )
                except Exception:
                    pass

            continue

        # ================================================
        # SIMPAN 3 SOAL
        # ================================================

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
                    material_id=MATERIAL_ID,
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

                    # Ketiga soal memakai
                    # audio_file yang sama.
                    audio_file=(
                        conversation_audio
                    ),
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
            conversation_number += 1

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
            "Part 3 minimal menghasilkan 3 soal"
        )

    # ========================================================
    # PART 3 HARUS KELIPATAN 3
    # ========================================================

    if jumlah % 3 != 0:
        raise ValueError(
            "Jumlah soal Part 3 harus "
            "kelipatan 3, misalnya "
            "3, 6, 9, 12, dan seterusnya"
        )

    if jumlah > 48:
        raise ValueError(
            "Jumlah soal Part 3 maksimal 48 "
            "dalam satu proses"
        )

    print(
        "\n================================"
    )

    print(
        "START GENERATE TOEIC PART 3"
    )

    print(
        f"Level        : {level}"
    )

    print(
        f"Jumlah soal  : {jumlah}"
    )

    print(
        f"Conversation : {jumlah // 3}"
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

        # Karena setiap conversation harus
        # 3 soal, remaining juga harus
        # kelipatan 3.
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
            max_questions=remaining,
        )

        total_saved += saved

        if saved == 0:
            print(
                "Tidak ada soal yang "
                "berhasil disimpan."
            )
            break

        # Pastikan hasil yang tersimpan
        # tetap berupa group lengkap.
        if total_saved % 3 != 0:
            print(
                "WARNING: jumlah soal tersimpan "
                "bukan kelipatan 3."
            )
            break

        generation_round += 1

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
        jumlah=3,
    )