<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

// ============================================================
// BASE DIRECTORY
// ============================================================

define('PART2_BASE_DIR', __DIR__);
define('PART2_AUDIO_DIR', PART2_BASE_DIR . '/part2/audio/question');

if (!is_dir(PART2_AUDIO_DIR)) {
    mkdir(PART2_AUDIO_DIR, 0777, true);
}

// ============================================================
// SHUFFLE OPTIONS
// Part 2 hanya memiliki 3 pilihan: A, B, C
// ============================================================

function part2_shuffle_options($question) {
    $options = [
        ['A', $question['option_a']],
        ['B', $question['option_b']],
        ['C', $question['option_c']],
    ];

    $originalAnswer = strtoupper(trim((string) $question['answer']));

    if (!in_array($originalAnswer, ['A', 'B', 'C'], true)) {
        throw new Exception('Jawaban Part 2 harus A, B, atau C');
    }

    $optionMap = [];
    foreach ($options as $opt) {
        $optionMap[$opt[0]] = $opt[1];
    }
    $correctText = $optionMap[$originalAnswer];

    shuffle($options);

    $letters = ['A', 'B', 'C'];
    $newOptions = [];
    $newAnswer = null;

    foreach ($options as $index => $opt) {
        $newLetter = $letters[$index];
        $text = $opt[1];
        $newOptions[$newLetter] = $text;

        if ($text === $correctText) {
            $newAnswer = $newLetter;
        }
    }

    $question['option_a'] = $newOptions['A'];
    $question['option_b'] = $newOptions['B'];
    $question['option_c'] = $newOptions['C'];
    $question['option_d'] = '';
    $question['answer'] = $newAnswer;

    return $question;
}

// ============================================================
// CREATE AUDIO
// ============================================================

function part2_create_audio($question, $optionA, $optionB, $optionC, $filename) {
    try {
        $audioText = "\n{$question}\n\nA. {$optionA}\nB. {$optionB}\nC. {$optionC}\n";

        return create_audio($audioText, $filename, PART2_AUDIO_DIR, 'part2/audio/question/');

    } catch (Exception $e) {
        return null;
    }
}

// ============================================================
// VALIDASI QUESTION
// ============================================================

function part2_validate_question($question) {
    $requiredFields = [
        'question',
        'option_a',
        'option_b',
        'option_c',
        'answer',
        'explanation',
    ];

    foreach ($requiredFields as $field) {
        if (!array_key_exists($field, $question)) {
            return false;
        }

        $value = $question[$field];

        if ($value === null) {
            return false;
        }

        if (is_string($value) && trim($value) === '') {
            return false;
        }
    }

    $answer = strtoupper(trim((string) $question['answer']));

    if (!in_array($answer, ['A', 'B', 'C'], true)) {
        return false;
    }

    return true;
}

// ============================================================
// GENERATE QUESTIONS VIA GEMINI
// ============================================================

function part2_generate_questions($level, $jumlah) {
    $prompt = <<<PROMPT
Generate exactly {$jumlah} TOEIC Part 2 Question-Response questions.

Difficulty level: {$level}

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
- Adjust vocabulary and sentence complexity to the {$level} level.
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
- Return EXACTLY {$jumlah} objects.

JSON format:

[
  {
    "question": "",
    "option_a": "",
    "option_b": "",
    "option_c": "",
    "option_d": "",
    "answer": "A",
    "explanation": ""
  }
]
PROMPT;

    for ($attempt = 0; $attempt < 5; $attempt++) {
        try {

            $responseText = gemini_generate_content($prompt);

            $data = extract_json_array($responseText);

            if ($data === null) {
                throw new Exception('JSON array tidak ditemukan');
            }

            if (!is_array($data) || array_keys($data) !== range(0, count($data) - 1)) {
                throw new Exception('Respons Gemini bukan list');
            }

            if (count($data) === 0) {
                throw new Exception('Gemini tidak menghasilkan soal');
            }

            return array_slice($data, 0, $jumlah);

        } catch (Exception $e) {

            if ($attempt < 4) {
                sleep(5);
            }
        }
    }

    return null;
}

// ============================================================
// GET MATERIAL ID PART 2
// ============================================================

function part2_get_material_id() {
    $conn = get_connection();

    try {
        $result = $conn->query(
            'SELECT id FROM materials WHERE part_id = 2 ORDER BY id ASC LIMIT 1'
        );

        $row = $result ? $result->fetch_row() : null;

        if (!$row) {
            throw new Exception('Tidak ada material untuk Part 2. Buat minimal 1 material Part 2 pada tabel materials.');
        }

        return $row[0];

    } finally {
        $conn->close();
    }
}

// ============================================================
// SAVE QUESTIONS
// ============================================================

function part2_save_questions($level, $questions, $materialId, $maxQuestions) {
    $batchId = time() . '_' . rand(1000, 9999);

    $savedCount = 0;

    foreach ($questions as $index => $question) {
        if ($savedCount >= $maxQuestions) {
            break;
        }


        try {
            // --------------------------------------------
            // VALIDASI
            // --------------------------------------------

            if (!part2_validate_question($question)) {
                continue;
            }

            // --------------------------------------------
            // SHUFFLE
            // --------------------------------------------

            $question = part2_shuffle_options($question);

            // --------------------------------------------
            // EXPLANATION
            // --------------------------------------------

            $explanation = trim((string) ($question['explanation'] ?? ''));

            if (!$explanation) {
                $correctLetter = strtolower($question['answer']);
                $correctText = $question["option_{$correctLetter}"];

                $explanation = "Respons tersebut paling sesuai dengan konteks pertanyaan, yaitu \"{$correctText}\". Respons ini memberikan jawaban yang relevan dan logis terhadap pertanyaan yang diberikan.";
            }

            // --------------------------------------------
            // FILENAME
            // --------------------------------------------

            $filename = "{$level}_{$batchId}_" . ($index + 1);

            // --------------------------------------------
            // AUDIO
            // --------------------------------------------


            $audioPath = part2_create_audio(
                $question['question'],
                $question['option_a'],
                $question['option_b'],
                $question['option_c'],
                $filename
            );

            // --------------------------------------------
            // DATABASE
            // --------------------------------------------

            insert_question(
                2,
                $materialId,
                $level,
                $question['question'],
                $question['option_a'],
                $question['option_b'],
                $question['option_c'],
                '',
                $question['answer'],
                $explanation,
                null,
                $audioPath
            );

            $savedCount++;


        } catch (Exception $e) {
        }

        if ($savedCount < $maxQuestions) {
            sleep(DELAY_BETWEEN_QUESTION);
        }
    }

    return $savedCount;
}

// ============================================================
// RUN FROM ADMIN
// ============================================================

function part2_run($level, $jumlah) {
    $level = strtolower(trim($level));

    $jumlah = filter_var($jumlah, FILTER_VALIDATE_INT);
    if ($jumlah === false) {
        throw new Exception('Jumlah soal tidak valid');
    }

    $allowedLevels = ['beginner', 'intermediate', 'advanced'];

    if (!in_array($level, $allowedLevels, true)) {
        throw new Exception('Level harus beginner, intermediate, atau advanced');
    }

    if ($jumlah < 1) {
        throw new Exception('Jumlah soal minimal 1');
    }

    if ($jumlah > 50) {
        throw new Exception('Jumlah soal maksimal 50');
    }

    // ========================================================
    // MATERIAL
    // ========================================================

    $materialId = part2_get_material_id();


    $totalSaved = 0;
    $generationRound = 1;

    // ========================================================
    // GENERATE SAMPAI JUMLAH TERPENUHI
    // ========================================================

    while ($totalSaved < $jumlah) {
        $remaining = $jumlah - $totalSaved;


        $questions = part2_generate_questions($level, $remaining);

        if (!$questions) {
            break;
        }

        $saved = part2_save_questions($level, $questions, $materialId, $remaining);

        $totalSaved += $saved;

        if ($saved === 0) {
            break;
        }

        $generationRound++;

        // Mencegah loop tanpa batas.
        if ($generationRound > 5) {
            break;
        }
    }


    return $totalSaved;
}

// ============================================================
// MANUAL TEST
// ============================================================

if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    part2_run('beginner', 1);
}