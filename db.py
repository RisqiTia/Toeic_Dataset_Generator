import mysql.connector


def get_connection():

    # return mysql.connector.connect(
    #     host="localhost",
    #     user="toeicpre_toeicta",
    #     password="Toeic12345*",
    #     database="toeicpre_toeic_prep_db1"
    # )

    return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="toeic_prep_db2"
        )

def insert_material(part_id, title, image=None, audio=None, text=None):

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO materials(part_id, title, image_file, audio_file, text_content)
    VALUES(%s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (part_id, title, image, audio, text))
    conn.commit()

    material_id = cursor.lastrowid

    conn.close()

    return material_id


def insert_question(
    part_id,
    material_id,
    difficulty_level,
    question_text,
    option_a,
    option_b,
    option_c,
    option_d,
    correct_answer,
    explanation,
    image_file=None,
    audio_file=None
):

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO questions
    (
        part_id,
        material_id,
        difficulty_level,
        question_text,
        option_a,
        option_b,
        option_c,
        option_d,
        correct_answer,
        explanation,
        image_file,
        audio_file
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(sql, (
        part_id,
        material_id,
        difficulty_level,
        question_text,
        option_a,
        option_b,
        option_c,
        option_d,
        correct_answer,
        explanation,
        image_file,
        audio_file
    ))

    conn.commit()

    conn.close()