<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

// ============================================================
// CONFIG
// ============================================================

define('PART5_PART_ID', 5);

// ============================================================
// FIX JSON DARI LLM
// ============================================================

function part5_fix_json($text) {
    $text = trim(str_replace(['```json', '```'], '', $text));

    if (preg_match('/\[.*\]/s', $text, $match)) {
        return $match[0];
    }

    return $text;
}

// ============================================================
// NORMALIZE QUESTION
// ============================================================

function part5_normalize_question($question) {
    try {
        $questionText = $question['question'] ?? ($question['sentence'] ?? null);

        // ====================================================
        // OPTIONS
        // ====================================================

        if (isset($question['options']) && is_array($question['options']) && count($question['options']) === 4) {
            $opts = array_values($question['options']);
            $optionA = $opts[0];
            $optionB = $opts[1];
            $optionC = $opts[2];
            $optionD = $opts[3];
        } else {
            $optionA = $question['option_a'] ?? ($question['A'] ?? null);
            $optionB = $question['option_b'] ?? ($question['B'] ?? null);
            $optionC = $question['option_c'] ?? ($question['C'] ?? null);
            $optionD = $question['option_d'] ?? ($question['D'] ?? null);
        }

        $options = [$optionA, $optionB, $optionC, $optionD];

        // ====================================================
        // ANSWER
        // ====================================================

        $rawAnswer = $question['answer'] ?? null;

        if ($rawAnswer === null) {
            return null;
        }

        $rawAnswer = trim((string) $rawAnswer);

        $answerLetter = null;

        if (in_array(strtoupper($rawAnswer), ['A', 'B', 'C', 'D'], true)) {
            $answerLetter = strtoupper($rawAnswer);
        } else {
            // Kalau Gemini memberikan teks jawaban, cari hurufnya.
            $letters = ['A', 'B', 'C', 'D'];
            foreach ($options as $index => $option) {
                if ($option !== null && trim((string) $option) === $rawAnswer) {
                    $answerLetter = $letters[$index];
                    break;
                }
            }
        }

        return [
            'question' => $questionText,
            'option_a' => $optionA,
            'option_b' => $optionB,
            'option_c' => $optionC,
            'option_d' => $optionD,
            'answer' => $answerLetter,
            'explanation' => $question['explanation'] ?? '',
        ];

    } catch (Exception $e) {
        return null;
    }
}

// ============================================================
// VALIDATE QUESTION
// ============================================================

function part5_validate_question($question) {
    if (!$question) {
        return false;
    }

    $requiredFields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer'];

    foreach ($requiredFields as $field) {
        $value = $question[$field] ?? null;

        if ($value === null) {
            return false;
        }

        if (is_string($value) && trim($value) === '') {
            return false;
        }
    }

    // Part 5 wajib memiliki blank
    if (strpos($question['question'], '___') === false) {
        return false;
    }

    if (!in_array($question['answer'], ['A', 'B', 'C', 'D'], true)) {
        return false;
    }

    $options = [
        $question['option_a'],
        $question['option_b'],
        $question['option_c'],
        $question['option_d'],
    ];

    // Semua pilihan harus berbeda.
    $normalizedOptions = array_map(function ($o) {
        return strtolower(trim((string) $o));
    }, $options);

    if (count(array_unique($normalizedOptions)) !== 4) {
        return false;
    }

    return true;
}

// ============================================================
// SHUFFLE OPTIONS
// ============================================================

function part5_shuffle_options($question) {
    $options = [
        ['A', $question['option_a']],
        ['B', $question['option_b']],
        ['C', $question['option_c']],
        ['D', $question['option_d']],
    ];

    $answer = strtoupper(trim((string) $question['answer']));

    if (!in_array($answer, ['A', 'B', 'C', 'D'], true)) {
        return null;
    }

    $optionMap = [];
    foreach ($options as $opt) {
        $optionMap[$opt[0]] = $opt[1];
    }
    $correctText = $optionMap[$answer] ?? null;

    if ($correctText === null) {
        return null;
    }

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

    if ($newAnswer === null) {
        return null;
    }

    $question['option_a'] = $newOptions['A'];
    $question['option_b'] = $newOptions['B'];
    $question['option_c'] = $newOptions['C'];
    $question['option_d'] = $newOptions['D'];
    $question['answer'] = $newAnswer;

    return $question;
}

// ============================================================
// GENERATE QUESTIONS
// ============================================================

function part5_generate_questions($level, $jumlah) {
    $prompt = <<<PROMPT
Generate exactly {$jumlah} TOEIC Part 5
Incomplete Sentences questions.

Difficulty level: {$level}

TOEIC Part 5 rules:
- Create EXACTLY {$jumlah} questions.
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
- Return EXACTLY {$jumlah} objects.

JSON format:

[
  {
    "question": "The manager ___ the report before the meeting.",
    "options": [
      "reviewed",
      "reviewing",
      "review",
      "reviews"
    ],
    "answer": "A",
    "explanation": "Kalimat ini membutuhkan bentuk kata kerja yang sesuai dengan konteks waktu dan struktur kalimat."
  }
]
PROMPT;

    for ($attempt = 0; $attempt < 5; $attempt++) {
        try {

            $rawText = gemini_generate_content($prompt);

            $cleanedText = part5_fix_json($rawText);

            $data = json_decode($cleanedText, true);

            if (!is_array($data) || array_keys($data) !== range(0, count($data) - 1)) {
                throw new Exception('Respons Gemini bukan list');
            }

            if (count($data) === 0) {
                throw new Exception('Gemini tidak menghasilkan soal');
            }


            // Jika Gemini memberikan lebih banyak dari permintaan.
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
// GET MATERIAL ID PART 5
// ============================================================

function part5_get_material_id() {
    $conn = get_connection();

    try {
        $result = $conn->query(
            'SELECT id FROM materials WHERE part_id = 5 ORDER BY id ASC LIMIT 1'
        );

        $row = $result ? $result->fetch_row() : null;

        if (!$row) {
            throw new Exception('Tidak ada material untuk Part 5. Buat minimal 1 material Part 5 pada tabel materials.');
        }

        return $row[0];

    } finally {
        $conn->close();
    }
}

// ============================================================
// SAVE QUESTIONS
// ============================================================

function part5_save_questions($level, $questions, $materialId, $maxQuestions) {
    $savedCount = 0;

    foreach ($questions as $index => $rawQuestion) {
        if ($savedCount >= $maxQuestions) {
            break;
        }


        // ====================================================
        // NORMALIZE
        // ====================================================

        $question = part5_normalize_question($rawQuestion);

        if (!$question) {
            continue;
        }

        // ====================================================
        // VALIDATE
        // ====================================================

        if (!part5_validate_question($question)) {
            continue;
        }

        // ====================================================
        // SHUFFLE
        // ====================================================

        $question = part5_shuffle_options($question);

        if (!$question) {
            continue;
        }

        // ====================================================
        // EXPLANATION
        // ====================================================

        $explanation = trim((string) ($question['explanation'] ?? ''));

        if (!$explanation) {
            $correctLetter = strtolower($question['answer']);
            $correctText = $question["option_{$correctLetter}"];

            $explanation = "Kata atau frasa \"{$correctText}\" paling tepat untuk melengkapi kalimat karena sesuai dengan struktur tata bahasa dan konteks kalimat.";
        }

        // ====================================================
        // DATABASE
        // ====================================================

        try {
            insert_question(
                PART5_PART_ID,
                $materialId,
                $level,
                $question['question'],
                $question['option_a'],
                $question['option_b'],
                $question['option_c'],
                $question['option_d'],
                $question['answer'],
                $explanation,
                null,
                null
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

function part5_run($level, $jumlah) {
    $level = strtolower(trim($level));

    $jumlah = filter_var($jumlah, FILTER_VALIDATE_INT);
    if ($jumlah === false) {
        throw new Exception('Jumlah soal tidak valid');
    }

    // ========================================================
    // VALIDASI LEVEL
    // ========================================================

    $allowedLevels = ['beginner', 'intermediate', 'advanced'];

    if (!in_array($level, $allowedLevels, true)) {
        throw new Exception('Level harus beginner, intermediate, atau advanced');
    }

    // ========================================================
    // VALIDASI JUMLAH
    // ========================================================

    if ($jumlah < 1) {
        throw new Exception('Jumlah soal minimal 1');
    }

    if ($jumlah > 50) {
        throw new Exception('Jumlah soal maksimal 50 dalam satu proses');
    }

    // ========================================================
    // MATERIAL
    // ========================================================

    $materialId = part5_get_material_id();


    $totalSaved = 0;
    $generationRound = 1;

    // ========================================================
    // GENERATE SAMPAI JUMLAH TERPENUHI
    // ========================================================

    while ($totalSaved < $jumlah) {
        $remaining = $jumlah - $totalSaved;


        $questions = part5_generate_questions($level, $remaining);

        if (!$questions) {
            break;
        }

        $saved = part5_save_questions($level, $questions, $materialId, $remaining);

        $totalSaved += $saved;

        if ($saved === 0) {
            break;
        }

        $generationRound++;

        // Mencegah loop tidak terbatas
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
    part5_run('beginner', 1);
}