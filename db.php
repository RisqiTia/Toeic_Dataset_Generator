<?php

// ============================================================
// DATABASE CONFIG
// ============================================================

define('DB_HOST', 'localhost');
define('DB_NAME', 'toeicpre_toeic_prep_db1');
define('DB_USER', 'toeicpre_toeicta');
define('DB_PASS', 'Toeic12345*');

// ============================================================
// CONNECT DATABASE
// ============================================================

function get_connection()
{
    $conn = new mysqli(
        DB_HOST,
        DB_USER,
        DB_PASS,
        DB_NAME
    );

    if ($conn->connect_errno) {
        throw new Exception(
            "Database connection failed : " .
            $conn->connect_error
        );
    }

    $conn->set_charset("utf8mb4");

    return $conn;
}

// ============================================================
// INSERT MATERIAL
// ============================================================

function insert_material(
    $part_id,
    $title,
    $image = null,
    $audio = null,
    $text = null
) {

    $conn = get_connection();

    $sql = "
        INSERT INTO materials
        (
            part_id,
            title,
            image_file,
            audio_file,
            text_content
        )
        VALUES
        (
            ?, ?, ?, ?, ?
        )
    ";

    $stmt = $conn->prepare($sql);

    if (!$stmt) {
        throw new Exception($conn->error);
    }

    $stmt->bind_param(
        "issss",
        $part_id,
        $title,
        $image,
        $audio,
        $text
    );

    if (!$stmt->execute()) {
        throw new Exception(
            "MySQL Error : " . $stmt->error
        );
    }

    $question_id = $stmt->insert_id;

    $stmt->close();
    $conn->close();

    return $question_id;

    $material_id = $stmt->insert_id;

    $stmt->close();
    $conn->close();

    return $material_id;
}

// ============================================================
// INSERT QUESTION
// ============================================================

function insert_question(
    $part_id,
    $material_id,
    $difficulty_level,
    $question_text,
    $option_a,
    $option_b,
    $option_c,
    $option_d,
    $correct_answer,
    $explanation,
    $image_file = null,
    $audio_file = null
) {

    $conn = get_connection();

    $sql = "
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
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    ";

    $stmt = $conn->prepare($sql);

    if (!$stmt) {
        throw new Exception($conn->error);
    }

    $stmt->bind_param(
        "iissssssssss",
        $part_id,
        $material_id,
        $difficulty_level,
        $question_text,
        $option_a,
        $option_b,
        $option_c,
        $option_d,
        $correct_answer,
        $explanation,
        $image_file,
        $audio_file
    );

    $stmt->execute();

    if ($stmt->error) {
        throw new Exception($stmt->error);
    }

    $question_id = $stmt->insert_id;

    $stmt->close();
    $conn->close();

    return $question_id;
}