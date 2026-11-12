<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

define('PART6_PART_ID', 6);
define('PART6_QUESTIONS_PER_PASSAGE', 4);

// ============================================================
// FIX JSON
// ============================================================

function part6_fix_json($text) {
    $text = trim(str_replace(['```json', '```'], '', $text));

    if (preg_match('/\[.*\]/s', $text, $match)) {
        return $match[0];
    }

    return $text;
}

// ============================================================
// SHUFFLE OPTIONS
// ============================================================

function part6_shuffle_options($q) {
    $options = [
        ['A', $q['option_a']],
        ['B', $q['option_b']],
        ['C', $q['option_c']],
        ['D', $q['option_d']],
    ];

    $answer = strtoupper(trim((string) ($q['answer'] ?? '')));

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
        $letter = $letters[$index];
        $text = $opt[1];
        $newOptions[$letter] = $text;

        if ($text === $correctText) {
            $newAnswer = $letter;
        }
    }

    if ($newAnswer === null) {
        return null;
    }

    $q['option_a'] = $newOptions['A'];
    $q['option_b'] = $newOptions['B'];
    $q['option_c'] = $newOptions['C'];
    $q['option_d'] = $newOptions['D'];
    $q['answer'] = $newAnswer;

    return $q;
}

// ============================================================
// GENERATE QUESTIONS
// ============================================================

function part6_generate_questions($level, $passageCount, $maxRetries = 5) {
    $totalQuestions = $passageCount * PART6_QUESTIONS_PER_PASSAGE;

    $prompt = <<<PROMPT
Generate TOEIC Part 6 Text Completion questions.

Difficulty level: {$level}

Create EXACTLY {$passageCount} different passages.

Each passage MUST contain exactly 4 questions.

Therefore:
- Number of passages: {$passageCount}
- Questions per passage: 4
- Total questions: {$totalQuestions}

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
    {
        "passage": "Full passage containing ___(1)___, ___(2)___, ___(3)___, and ___(4)___.",
        "blank_number": 1,
        "question": "What best completes blank (1)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "A",
        "explanation": "Penjelasan Bahasa Indonesia."
    },
    {
        "passage": "SAME EXACT PASSAGE",
        "blank_number": 2,
        "question": "What best completes blank (2)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "B",
        "explanation": "Penjelasan Bahasa Indonesia."
    },
    {
        "passage": "SAME EXACT PASSAGE",
        "blank_number": 3,
        "question": "What best completes blank (3)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "C",
        "explanation": "Penjelasan Bahasa Indonesia."
    },
    {
        "passage": "SAME EXACT PASSAGE",
        "blank_number": 4,
        "question": "What best completes blank (4)?",
        "option_a": "...",
        "option_b": "...",
        "option_c": "...",
        "option_d": "...",
        "answer": "D",
        "explanation": "Penjelasan Bahasa Indonesia."
    }
]

Generate EXACTLY {$totalQuestions} question objects.
PROMPT;

    for ($attempt = 0; $attempt < $maxRetries; $attempt++) {
        try {

            $raw = gemini_generate_content($prompt);

            $cleaned = part6_fix_json($raw);

            $data = json_decode($cleaned, true);

            if (!is_array($data) || array_keys($data) !== range(0, count($data) - 1)) {
                sleep(5);
                continue;
            }

            if (count($data) !== $totalQuestions) {
                sleep(5);
                continue;
            }

            // ================================================
            // VALIDASI GROUP
            // ================================================

            $valid = true;

            for ($groupStart = 0; $groupStart < $totalQuestions; $groupStart += 4) {
                $group = array_slice($data, $groupStart, 4);

                if (count($group) !== 4) {
                    $valid = false;
                    break;
                }

                $passages = array_map(function ($q) {
                    return trim((string) ($q['passage'] ?? ''));
                }, $group);

                // Passage harus identik
                if (count(array_unique($passages)) !== 1) {
                    $valid = false;
                    break;
                }

                $passage = $passages[0];

                // Semua blank wajib ada
                for ($blank = 1; $blank <= 4; $blank++) {
                    $marker = "___({$blank})___";

                    if (strpos($passage, $marker) === false) {
                        $valid = false;
                        break;
                    }
                }

                if (!$valid) {
                    break;
                }

                $blankNumbers = [];

                foreach ($group as $q) {
                    $number = filter_var($q['blank_number'] ?? null, FILTER_VALIDATE_INT);
                    if ($number === false || $number === null) {
                        $valid = false;
                        break;
                    }
                    $blankNumbers[] = $number;
                }

                if (!$valid) {
                    break;
                }

                $sorted = $blankNumbers;
                sort($sorted);

                if ($sorted !== [1, 2, 3, 4]) {
                    $valid = false;
                    break;
                }
            }

            if (!$valid) {
                sleep(5);
                continue;
            }


            return $data;

        } catch (Exception $e) {
            $error = $e->getMessage();

            if (strpos($error, '503') !== false || strpos($error, 'UNAVAILABLE') !== false) {
                $wait = 30 * ($attempt + 1);
                sleep($wait);
            } elseif (strpos($error, '429') !== false || strpos($error, 'RESOURCE_EXHAUSTED') !== false) {
                sleep(60);
            } else {
                sleep(10);
            }
        }
    }

    return null;
}

// ============================================================
// GET MATERIAL PART 6
// ============================================================

function part6_get_material_id() {
    $conn = get_connection();

    try {
        $result = $conn->query(
            'SELECT id FROM materials WHERE part_id = 6 ORDER BY id ASC LIMIT 1'
        );

        $row = $result ? $result->fetch_row() : null;

        if (!$row) {
            throw new Exception('Material Part 6 belum tersedia di tabel materials.');
        }

        return $row[0];

    } finally {
        $conn->close();
    }
}

// ============================================================
// VALIDATE QUESTION
// ============================================================

function part6_validate_question($q) {
    if (!$q) {
        return false;
    }

    $blankNumber = filter_var($q['blank_number'] ?? null, FILTER_VALIDATE_INT);

    if ($blankNumber === false || $blankNumber === null || !in_array($blankNumber, [1, 2, 3, 4], true)) {
        return false;
    }

    $required = ['passage', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer'];

    foreach ($required as $field) {
        $value = $q[$field] ?? null;

        if ($value === null) {
            return false;
        }

        if (is_string($value) && trim($value) === '') {
            return false;
        }
    }

    $answer = strtoupper(trim((string) $q['answer']));

    if (!in_array($answer, ['A', 'B', 'C', 'D'], true)) {
        return false;
    }

    $options = [
        trim((string) $q['option_a']),
        trim((string) $q['option_b']),
        trim((string) $q['option_c']),
        trim((string) $q['option_d']),
    ];

    $lowered = array_map('strtolower', $options);

    if (count(array_unique($lowered)) !== 4) {
        return false;
    }

    $passage = (string) $q['passage'];

    for ($blank = 1; $blank <= 4; $blank++) {
        if (strpos($passage, "___({$blank})___") === false) {
            return false;
        }
    }

    return true;
}

// ============================================================
// SAVE QUESTIONS
// ============================================================

function part6_save_questions($level, $questions, $materialId) {
    $saved = 0;
    $skipped = 0;

    $total = count($questions);

    foreach ($questions as $index => $q) {

        if (!part6_validate_question($q)) {
            $skipped++;
            continue;
        }

        $passage = trim((string) $q['passage']);
        $question = trim((string) $q['question']);

        // ====================================================
        // QUESTION TEXT
        // ====================================================

        $questionText = "{$passage}\n\n{$question}";

        // ====================================================
        // SHUFFLE
        // ====================================================

        $shuffled = part6_shuffle_options([
            'option_a' => $q['option_a'],
            'option_b' => $q['option_b'],
            'option_c' => $q['option_c'],
            'option_d' => $q['option_d'],
            'answer' => strtoupper(trim((string) $q['answer'])),
        ]);

        if (!$shuffled) {
            $skipped++;
            continue;
        }

        // ====================================================
        // EXPLANATION
        // ====================================================

        $explanation = trim((string) ($q['explanation'] ?? ''));

        if (!$explanation) {
            $correctLetter = strtolower($shuffled['answer']);
            $correctText = $shuffled["option_{$correctLetter}"];

            $explanation = "Jawaban \"{$correctText}\" paling sesuai untuk melengkapi bagian kosong berdasarkan struktur kalimat dan konteks teks.";
        }

        // ====================================================
        // INSERT DATABASE
        // ====================================================

        try {
            insert_question(
                PART6_PART_ID,
                $materialId,
                $level,
                $questionText,
                $shuffled['option_a'],
                $shuffled['option_b'],
                $shuffled['option_c'],
                $shuffled['option_d'],
                $shuffled['answer'],
                $explanation,
                null,
                null
            );

            $saved++;


        } catch (Exception $e) {
            $skipped++;
        }

        if ($index < $total - 1) {
            sleep(DELAY_BETWEEN_QUESTION);
        }
    }


    return $saved;
}

// ============================================================
// RUN FROM ADMIN
// ============================================================

function part6_run($level, $jumlah) {
    $level = strtolower(trim($level));

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

    $jumlah = filter_var($jumlah, FILTER_VALIDATE_INT);
    if ($jumlah === false) {
        throw new Exception('Jumlah soal tidak valid');
    }

    if ($jumlah < 4) {
        throw new Exception('Part 6 minimal 4 soal');
    }

    if ($jumlah % 4 !== 0) {
        throw new Exception('Jumlah soal Part 6 harus kelipatan 4 (4, 8, 12, 16, ...)');
    }

    if ($jumlah > 40) {
        throw new Exception('Maksimal 40 soal dalam satu proses generate');
    }

    $passageCount = intdiv($jumlah, 4);

    // ========================================================
    // MATERIAL
    // ========================================================

    $materialId = part6_get_material_id();


    // ========================================================
    // GENERATE
    // ========================================================

    $questions = part6_generate_questions($level, $passageCount);

    if (!$questions) {
        return 0;
    }

    // ========================================================
    // SAVE
    // ========================================================

    $totalSaved = part6_save_questions($level, $questions, $materialId);


    return $totalSaved;
}

// ============================================================
// MANUAL TEST
// ============================================================

if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    part6_run('beginner', 4);
}