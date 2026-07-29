import sys
import json
import os


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

os.chdir(BASE_DIR)


# ============================================================
# RESPONSE
# ============================================================

def response_success(data):
    print(
        json.dumps(
            {
                "status": "success",
                **data,
            },
            ensure_ascii=False,
        )
    )


def response_error(message):
    print(
        json.dumps(
            {
                "status": "error",
                "message": message,
            },
            ensure_ascii=False,
        )
    )

    sys.exit(1)


# ============================================================
# VALIDASI ARGUMENT
# ============================================================

if len(sys.argv) < 4:
    response_error(
        "Parameter part, level, "
        "dan jumlah diperlukan"
    )


try:
    part = int(
        sys.argv[1]
    )

    level = (
        sys.argv[2]
        .strip()
        .lower()
    )

    jumlah = int(
        sys.argv[3]
    )

except Exception:
    response_error(
        "Parameter tidak valid"
    )


# ============================================================
# VALIDASI PART
# ============================================================

if part < 1 or part > 7:
    response_error(
        "Part harus antara 1 sampai 7"
    )


# ============================================================
# VALIDASI LEVEL
# ============================================================

allowed_levels = [
    "beginner",
    "intermediate",
    "advanced",
]

if level not in allowed_levels:
    response_error(
        "Level harus beginner, "
        "intermediate, atau advanced"
    )


# ============================================================
# VALIDASI JUMLAH
# ============================================================

if jumlah < 1:
    response_error(
        "Jumlah soal minimal 1"
    )


if jumlah > 50:
    response_error(
        "Jumlah soal maksimal 50"
    )


# ============================================================
# GENERATE
# ============================================================

try:

    # --------------------------------------------------------
    # PART 1
    # --------------------------------------------------------

    if part == 1:

        from part1_photograph import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )


    elif part == 2:

        from part2_question_response import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )


    elif part == 3:

        from part3_conversation import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )

    elif part == 4:

        from part4_talks import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )

    elif part == 5:

        from part5_incomplete_sentences import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )

    elif part == 6:

        from part6_text_completion import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )

    elif part == 7:

        from part7_reading_comprehension import run

        total_generated = run(
            level=level,
            jumlah=jumlah,
        )

    else:

        response_error(
            f"Generator Part {part} "
            f"belum diaktifkan"
        )

    # ========================================================
    # HASIL
    # ========================================================

    if total_generated <= 0:
        response_error(
            "Tidak ada soal yang "
            "berhasil dibuat"
        )


    if total_generated < jumlah:

        response_success({
            "message":
                "Generate selesai, tetapi "
                "sebagian soal gagal dibuat",

            "part":
                part,

            "level":
                level,

            "requested":
                jumlah,

            "generated":
                total_generated,
        })

    else:

        response_success({
            "message":
                "Generate soal berhasil",

            "part":
                part,

            "level":
                level,

            "requested":
                jumlah,

            "generated":
                total_generated,
        })


except Exception as e:

    response_error(
        f"Gagal generate soal: {str(e)}"
    )