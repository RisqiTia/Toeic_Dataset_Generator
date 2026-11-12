<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

// ============================================================
// BASE DIRECTORY
// ============================================================

define('PART1_BASE_DIR', __DIR__);
define('PART1_IMAGE_DIR', PART1_BASE_DIR . '/part1/images');
define('PART1_AUDIO_DIR', PART1_BASE_DIR . '/part1/audio');

if (!is_dir(PART1_IMAGE_DIR)) {
    mkdir(PART1_IMAGE_DIR, 0777, true);
}
if (!is_dir(PART1_AUDIO_DIR)) {
    mkdir(PART1_AUDIO_DIR, 0777, true);
}

// ============================================================
// SHUFFLE OPTIONS
// ============================================================

function part1_shuffle_options($question) {
    $options = [
        ['A', $question['option_a']],
        ['B', $question['option_b']],
        ['C', $question['option_c']],
        ['D', $question['option_d']],
    ];

    $originalAnswer = strtoupper(trim($question['answer']));

    if (!in_array($originalAnswer, ['A', 'B', 'C', 'D'], true)) {
        throw new Exception('Jawaban dari Gemini tidak valid');
    }

    $optionMap = [];
    foreach ($options as $opt) {
        $optionMap[$opt[0]] = $opt[1];
    }
    $correctText = $optionMap[$originalAnswer];

    shuffle($options);

    $letters = ['A', 'B', 'C', 'D'];
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
    $question['option_d'] = $newOptions['D'];
    $question['answer'] = $newAnswer;

    // Gambar dicari berdasarkan deskripsi jawaban yang benar.
    $question['image_keyword'] = $correctText;

    return $question;
}

// ============================================================
// GENERATE QUESTIONS WITH GEMINI
// ============================================================

function part1_generate_questions($level, $jumlah) {
    $prompt = <<<PROMPT
Generate exactly {$jumlah} TOEIC Part 1 Photograph questions.

Difficulty level: {$level}

TOEIC Part 1 rules:
- Each item represents one photograph.
- Each item must have exactly 4 options: A, B, C, and D.
- Only one option may correctly describe the photograph.
- The other three options must be plausible but clearly incorrect.
- Use realistic TOEIC situations such as offices, streets, restaurants,
  airports, stations, stores, meetings, workplaces, and public places.
- Sentences must sound natural in English.
- Adjust vocabulary and sentence complexity to the {$level} level.
- Correct answers must vary between A, B, C, and D.

IMPORTANT:
- "question" may contain a short instruction appropriate for TOEIC Part 1.
- explanation MUST be written in Bahasa Indonesia.
- Do NOT mention the answer letter A/B/C/D inside explanation.
- Explanation must explain why the description matches the photograph.
- image_keyword must be a concise English search phrase that clearly
  represents the CORRECT option.
- image_keyword should describe visible people, objects, actions,
  and setting.
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
    "explanation": "",
    "image_keyword": ""
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

            // Jika Gemini menghasilkan lebih banyak dari yang diminta, ambil sesuai jumlah.
            $data = array_slice($data, 0, $jumlah);

            return $data;

        } catch (Exception $e) {
            if ($attempt < 4) {
                sleep(5);
            }
        }
    }

    return null;
}

// ============================================================
// VALIDASI SATU SOAL
// ============================================================

function part1_validate_question($question) {
    $requiredFields = [
        'question',
        'option_a',
        'option_b',
        'option_c',
        'option_d',
        'answer',
        'explanation',
    ];

    foreach ($requiredFields as $field) {
        if (!array_key_exists($field, $question)) {
            return false;
        }

        if ($question[$field] === null) {
            return false;
        }

        if (is_string($question[$field]) && trim($question[$field]) === '') {
            return false;
        }
    }

    $answer = strtoupper(trim((string) $question['answer']));

    if (!in_array($answer, ['A', 'B', 'C', 'D'], true)) {
        return false;
    }

    return true;
}

// ============================================================
// SAVE QUESTIONS
// ============================================================

function part1_save_questions($level, $questions, $maxQuestions) {
    // timestamp + random untuk mengurangi kemungkinan nama file sama.
    $batchId = time() . '_' . rand(1000, 9999);

    $savedCount = 0;

    foreach ($questions as $index => $question) {
        // Jangan simpan melebihi jumlah yang diminta admin.
        if ($savedCount >= $maxQuestions) {
            break;
        }

        try {
            if (!part1_validate_question($question)) {
                continue;
            }

            $question = part1_shuffle_options($question);

            $filename = "{$level}_{$batchId}_" . ($index + 1);

            $keyword = !empty($question['image_keyword'])
                ? $question['image_keyword']
                : $question['option_a'];

            // --------------------------------
            // IMAGE
            // --------------------------------

            $imagePath = download_image($keyword, $filename, PART1_IMAGE_DIR, 'part1/images/');

            sleep(1);

            // --------------------------------
            // AUDIO
            // --------------------------------

            $audioText = "\n{$question['question']}\n\nA. {$question['option_a']}\nB. {$question['option_b']}\nC. {$question['option_c']}\nD. {$question['option_d']}\n";

            $audioPath = create_audio($audioText, $filename, PART1_AUDIO_DIR, 'part1/audio/');

            sleep(1);

            // --------------------------------
            // DATABASE
            // --------------------------------

            insert_question(
                1,
                33, // Tetap menggunakan material yang sekarang dipakai generator.
                $level,
                $question['question'],
                $question['option_a'],
                $question['option_b'],
                $question['option_c'],
                $question['option_d'],
                $question['answer'],
                $question['explanation'],
                $imagePath,
                $audioPath
            );

            $savedCount++;

        } catch (Exception $e) {
            throw new Exception(
                "Insert Question gagal: " . $e->getMessage()
            );
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

function part1_run($level, $jumlah) {
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

    $totalSaved = 0;
    $generationRound = 1;

    // Jika Gemini menghasilkan kurang dari jumlah yang diminta atau ada soal
    // gagal disimpan, generate kekurangannya lagi.
    while ($totalSaved < $jumlah) {
        $remaining = $jumlah - $totalSaved;

        $questions = part1_generate_questions($level, $remaining);

        if (!$questions) {
            break;
        }

        $saved = part1_save_questions($level, $questions, $remaining);

        $totalSaved += $saved;

        if ($saved === 0) {
            break;
        }

        $generationRound++;

        // Hindari loop tanpa batas.
        if ($generationRound > 5) {
            break;
        }
    }

    return $totalSaved;
}

// ============================================================
// MANUAL RUN
// ============================================================

if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    // Hanya untuk testing langsung file ini. Dashboard tidak menggunakan bagian ini.
    part1_run('beginner', 1);
}