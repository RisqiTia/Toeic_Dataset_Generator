<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

define('PART7_PART_ID', 7);
define('PART7_QUESTIONS_PER_TEXT', 4);

// ============================================================
// FIX JSON
// ============================================================

function part7_fix_json($text) {
    $text = trim(str_replace(['```json', '```'], '', $text));

    if (preg_match('/\[.*\]/s', $text, $match)) {
        return $match[0];
    }

    return $text;
}

// ============================================================
// SHUFFLE OPTIONS
// ============================================================

function part7_shuffle_options($q) {
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
// VALIDATE QUESTION
// ============================================================

function part7_validate_question($q) {
    if (!$q) {
        return false;
    }

    $requiredFields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer'];

    foreach ($requiredFields as $field) {
        $value = $q[$field] ?? null;

        if ($value === null) {
            return false;
        }

        if (is_string($value) && trim($value) === '') {
            return false;
        }
    }

    $question = trim((string) $q['question']);

    // Harus berupa pertanyaan
    if (strpos($question, '?') === false) {
        return false;
    }

    $answer = strtoupper(trim((string) $q['answer']));

    if (!in_array($answer, ['A', 'B', 'C', 'D'], true)) {
        return false;
    }

    // Pastikan opsi berbeda
    $options = [
        strtolower(trim((string) $q['option_a'])),
        strtolower(trim((string) $q['option_b'])),
        strtolower(trim((string) $q['option_c'])),
        strtolower(trim((string) $q['option_d'])),
    ];

    if (count(array_unique($options)) !== 4) {
        return false;
    }

    return true;
}

// ============================================================
// GENERATE TEXT + QUESTIONS
// ============================================================

function part7_generate_text_with_questions($level, $textCount, $maxRetries = 5) {
    $totalQuestions = $textCount * PART7_QUESTIONS_PER_TEXT;

    $prompt = <<<PROMPT
Generate TOEIC Part 7 Reading Comprehension questions.

Difficulty level: {$level}

Create EXACTLY {$textCount} different reading texts.

Each text MUST contain exactly 4 questions.

Therefore:
- Number of texts: {$textCount}
- Questions per text: 4
- Total questions: {$totalQuestions}

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

Return EXACTLY {$textCount} objects.

JSON format:

[
    {
        "text": "Reading passage...",
        "questions": [
            {
                "question": "What is the purpose of the email?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "A",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            },
            {
                "question": "When will the event take place?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "B",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            },
            {
                "question": "Why did the writer contact the recipient?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "C",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            },
            {
                "question": "What is suggested about the company?",
                "option_a": "...",
                "option_b": "...",
                "option_c": "...",
                "option_d": "...",
                "answer": "D",
                "explanation": "Penjelasan dalam Bahasa Indonesia."
            }
        ]
    }
]

Generate exactly:
{$textCount} texts
and
{$totalQuestions} total questions.
PROMPT;

    for ($attempt = 0; $attempt < $maxRetries; $attempt++) {
        try {

            $raw = gemini_generate_content($prompt);

            $cleaned = part7_fix_json($raw);

            $data = json_decode($cleaned, true);

            // =================================================
            // VALIDASI LIST
            // =================================================

            if (!is_array($data) || array_keys($data) !== range(0, count($data) - 1)) {
                sleep(5);
                continue;
            }

            // =================================================
            // VALIDASI JUMLAH TEXT
            // =================================================

            if (count($data) !== $textCount) {
                sleep(5);
                continue;
            }

            $valid = true;
            $calculatedQuestions = 0;

            // =================================================
            // VALIDASI SETIAP TEXT
            // =================================================

            foreach ($data as $index => $item) {
                $textContent = trim((string) ($item['text'] ?? ''));

                if (!$textContent) {
                    $valid = false;
                    break;
                }

                $questions = $item['questions'] ?? [];

                if (!is_array($questions)) {
                    $valid = false;
                    break;
                }

                if (count($questions) !== PART7_QUESTIONS_PER_TEXT) {
                    $valid = false;
                    break;
                }

                // Validasi setiap soal
                foreach ($questions as $question) {
                    if (!part7_validate_question($question)) {
                        $valid = false;
                        break;
                    }
                }

                if (!$valid) {
                    break;
                }

                $calculatedQuestions += count($questions);
            }

            if (!$valid) {
                sleep(5);
                continue;
            }

            // =================================================
            // TOTAL QUESTION
            // =================================================

            if ($calculatedQuestions !== $totalQuestions) {
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
// GET MATERIAL PART 7
// ============================================================

function part7_get_material_id() {
    $conn = get_connection();

    try {
        $result = $conn->query(
            'SELECT id FROM materials WHERE part_id = 7 ORDER BY id ASC LIMIT 1'
        );

        $row = $result ? $result->fetch_row() : null;

        if (!$row) {
            throw new Exception('Material Part 7 belum tersedia di tabel materials.');
        }

        return $row[0];

    } finally {
        $conn->close();
    }
}

// ============================================================
// SAVE TEXT + QUESTIONS
// ============================================================

function part7_save_text_with_questions($level, $texts, $materialId) {
    $saved = 0;
    $skipped = 0;

    $totalQuestions = 0;
    foreach ($texts as $item) {
        $totalQuestions += count($item['questions'] ?? []);
    }

    $globalQuestionNumber = 1;

    foreach ($texts as $textIndex => $item) {
        $textContent = trim((string) ($item['text'] ?? ''));
        $questions = $item['questions'] ?? [];

        if (!$textContent || !$questions) {
            $skipped += count($questions);
            continue;
        }


        // ====================================================
        // QUESTIONS
        // ====================================================

        foreach ($questions as $questionIndex => $q) {

            $globalQuestionNumber++;

            // ================================================
            // VALIDASI
            // ================================================

            if (!part7_validate_question($q)) {
                $skipped++;
                continue;
            }

            // ================================================
            // SHUFFLE
            // ================================================

            $shuffled = part7_shuffle_options([
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

            // ================================================
            // QUESTION TEXT
            // ================================================

            $questionText = "{$textContent}\n\n" . trim((string) $q['question']);

            // ================================================
            // EXPLANATION
            // ================================================

            $explanation = trim((string) ($q['explanation'] ?? ''));

            if (!$explanation) {
                $correctLetter = strtolower($shuffled['answer']);
                $correctText = $shuffled["option_{$correctLetter}"];

                $explanation = "Jawaban \"{$correctText}\" dapat ditentukan berdasarkan informasi yang terdapat dalam teks bacaan.";
            }

            // ================================================
            // INSERT DATABASE
            // ================================================

            try {
                insert_question(
                    PART7_PART_ID,
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

            if ($saved + $skipped < $totalQuestions) {
                sleep(DELAY_BETWEEN_QUESTION);
            }
        }
    }


    return $saved;
}

// ============================================================
// RUN FROM ADMIN
// ============================================================

function part7_run($level, $jumlah) {
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
        throw new Exception('Part 7 minimal 4 soal');
    }

    if ($jumlah % 4 !== 0) {
        throw new Exception('Jumlah soal Part 7 harus kelipatan 4 (4, 8, 12, 16, ...)');
    }

    if ($jumlah > 40) {
        throw new Exception('Maksimal 40 soal dalam satu proses generate');
    }

    $textCount = intdiv($jumlah, PART7_QUESTIONS_PER_TEXT);

    // ========================================================
    // MATERIAL
    // ========================================================

    $materialId = part7_get_material_id();


    // ========================================================
    // GENERATE
    // ========================================================

    $texts = part7_generate_text_with_questions($level, $textCount);

    if (!$texts) {
        return 0;
    }

    // ========================================================
    // SAVE
    // ========================================================

    $totalSaved = part7_save_text_with_questions($level, $texts, $materialId);


    return $totalSaved;
}

// ============================================================
// MANUAL TEST
// ============================================================

if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    part7_run('beginner', 4);
}