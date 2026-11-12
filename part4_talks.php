<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

// ============================================================
// CONFIG
// ============================================================

define('PART4_PART_ID', 4);

// ============================================================
// DIRECTORY
// ============================================================

define('PART4_BASE_DIR', __DIR__);
define('PART4_AUDIO_DIR', PART4_BASE_DIR . '/part4/audio/talk');

if (!is_dir(PART4_AUDIO_DIR)) {
    mkdir(PART4_AUDIO_DIR, 0777, true);
}

// ============================================================
// GET MATERIAL ID PART 4
// ============================================================

function part4_get_material_id() {
    $conn = get_connection();

    try {
        $result = $conn->query(
            'SELECT id FROM materials WHERE part_id = 4 ORDER BY id ASC LIMIT 1'
        );

        $row = $result ? $result->fetch_row() : null;

        if (!$row) {
            throw new Exception('Tidak ada material untuk Part 4. Buat minimal 1 material Part 4 pada tabel materials.');
        }

        return $row[0];

    } finally {
        $conn->close();
    }
}

// ============================================================
// CREATE TALK AUDIO
// ============================================================

function part4_create_talk_audio($text, $filename) {
    try {
        return create_audio($text, $filename, PART4_AUDIO_DIR, 'part4/audio/talk/');
    } catch (Exception $e) {
        return null;
    }
}

// ============================================================
// SHUFFLE OPTIONS
// ============================================================

function part4_shuffle_options($question) {
    $answer = strtoupper(trim((string) $question['answer']));

    if (!in_array($answer, ['A', 'B', 'C', 'D'], true)) {
        throw new Exception('Jawaban harus A, B, C, atau D');
    }

    $options = [
        $question['option_a'],
        $question['option_b'],
        $question['option_c'],
        $question['option_d'],
    ];

    $correctText = $question['option_' . strtolower($answer)];

    shuffle($options);

    $question['option_a'] = $options[0];
    $question['option_b'] = $options[1];
    $question['option_c'] = $options[2];
    $question['option_d'] = $options[3];

    if ($options[0] === $correctText) {
        $question['answer'] = 'A';
    } elseif ($options[1] === $correctText) {
        $question['answer'] = 'B';
    } elseif ($options[2] === $correctText) {
        $question['answer'] = 'C';
    } elseif ($options[3] === $correctText) {
        $question['answer'] = 'D';
    }

    return $question;
}

// ============================================================
// VALIDATE QUESTION
// ============================================================

function part4_validate_question($question) {
    $requiredFields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'answer', 'explanation'];

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

    if (!in_array($answer, ['A', 'B', 'C', 'D'], true)) {
        return false;
    }

    $options = [
        $question['option_a'],
        $question['option_b'],
        $question['option_c'],
        $question['option_d'],
    ];

    if (count(array_unique($options)) < 4) {
        return false;
    }

    return true;
}

// ============================================================
// VALIDATE TALK
// ============================================================

function part4_validate_talk($talkData) {
    if (!is_array($talkData)) {
        return false;
    }

    $talk = $talkData['talk'] ?? '';
    $questions = $talkData['questions'] ?? [];

    if (trim((string) $talk) === '') {
        return false;
    }

    if (!is_array($questions)) {
        return false;
    }

    // Part 4: satu talk = tepat 3 soal
    if (count($questions) !== 3) {
        return false;
    }

    foreach ($questions as $question) {
        if (!part4_validate_question($question)) {
            return false;
        }
    }

    return true;
}

// ============================================================
// GENERATE TALKS
// ============================================================

function part4_generate_questions($level, $jumlah) {
    $totalTalks = intdiv($jumlah, 3);

    $prompt = <<<PROMPT
Generate TOEIC Part 4 Listening Talks.

Difficulty level: {$level}

Create exactly {$totalTalks} talks.

IMPORTANT:
- Each talk MUST contain exactly 3 questions.
- Total questions MUST be exactly {$jumlah}.
- A talk is a monologue spoken by ONE speaker.

TOEIC Part 4 rules:
- Each talk should contain approximately 5 to 8 sentences.
- Use natural spoken English.
- Use realistic TOEIC contexts such as:
  announcements,
  recorded messages,
  office updates,
  advertisements,
  tourism information,
  business presentations,
  company news,
  event announcements,
  transportation announcements,
  weather reports,
  customer service messages,
  introductions,
  instructions.
- Each question must test comprehension of the talk.
- Use varied question types such as:
  main purpose,
  speaker intention,
  location,
  audience,
  specific detail,
  reason,
  next action,
  implied meaning.
- Each question must have exactly four choices:
  A, B, C, and D.
- Only one answer can be correct.
- Distractors must be plausible.
- Correct answers should vary between A, B, C, and D.
- Adjust vocabulary and complexity to the {$level} level.

LANGUAGE RULES:
- Talk must be written in English.
- Questions must be written in English.
- Options must be written in English.
- Explanation MUST be written in Bahasa Indonesia.
- Explanation must explain why the answer is correct
  based on information in the talk.
- Do NOT mention option letters A/B/C/D
  in the explanation.

Return valid JSON only.
Do NOT return Markdown.
Do NOT use ```json.
Do NOT include comments inside JSON.

JSON format:

[
  {
    "talk": "",
    "questions": [
      {
        "question": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "answer": "A",
        "explanation": ""
      },
      {
        "question": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "answer": "B",
        "explanation": ""
      },
      {
        "question": "",
        "option_a": "",
        "option_b": "",
        "option_c": "",
        "option_d": "",
        "answer": "C",
        "explanation": ""
      }
    ]
  }
]

Generate EXACTLY:
- {$totalTalks} talks
- 3 questions per talk
- {$jumlah} questions total
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
                throw new Exception('Gemini tidak menghasilkan talk');
            }

            // Batasi sesuai jumlah talk
            $data = array_slice($data, 0, $totalTalks);

            $validData = [];

            foreach ($data as $talkData) {
                if (part4_validate_talk($talkData)) {
                    $validData[] = $talkData;
                } else {
                }
            }

            if ($validData) {
                return $validData;
            }

            throw new Exception('Tidak ada talk valid');

        } catch (Exception $e) {

            if ($attempt < 4) {
                sleep(5);
            }
        }
    }

    return null;
}

// ============================================================
// SAVE QUESTIONS
// ============================================================

function part4_save_questions($level, $data, $materialId, $maxQuestions) {
    $batchId = time() . '_' . rand(1000, 9999);

    $savedCount = 0;
    $talkNumber = 1;

    foreach ($data as $talkData) {
        if ($savedCount >= $maxQuestions) {
            break;
        }

        if (!part4_validate_talk($talkData)) {
            continue;
        }

        $talkText = $talkData['talk'];
        $questions = $talkData['questions'];

        // Jangan simpan talk parsial.
        if ($savedCount + 3 > $maxQuestions) {
            break;
        }

        $startNumber = $savedCount + 1;
        $endNumber = $startNumber + 2;

        $talkFilename = "{$level}_{$batchId}_talk_{$talkNumber}_{$startNumber}-{$endNumber}";


        $talkAudio = part4_create_talk_audio($talkText, $talkFilename);

        if (!$talkAudio) {
            continue;
        }

        sleep(1);

        // ====================================================
        // PREPARE QUESTIONS
        // ====================================================

        $preparedQuestions = [];
        $talkValid = true;

        foreach ($questions as $question) {
            try {
                $question = part4_shuffle_options($question);

                if (!part4_validate_question($question)) {
                    $talkValid = false;
                    break;
                }

                $preparedQuestions[] = $question;

            } catch (Exception $e) {
                $talkValid = false;
                break;
            }
        }

        // Jika salah satu soal invalid, jangan simpan talk parsial.
        if (!$talkValid || count($preparedQuestions) !== 3) {

            // Hapus audio yang tidak dipakai
            $fullAudioPath = PART4_BASE_DIR . '/' . $talkAudio;

            if (file_exists($fullAudioPath)) {
                @unlink($fullAudioPath);
            }

            continue;
        }

        // ====================================================
        // SAVE 3 QUESTIONS
        // ====================================================

        $groupSaved = 0;

        foreach ($preparedQuestions as $question) {
            $questionNumber = $savedCount + 1;


            try {
                insert_question(
                    PART4_PART_ID,
                    $materialId,
                    $level,
                    $question['question'],
                    $question['option_a'],
                    $question['option_b'],
                    $question['option_c'],
                    $question['option_d'],
                    $question['answer'],
                    $question['explanation'],
                    null,
                    $talkAudio // Semua soal dalam talk menggunakan audio yang sama
                );

                $savedCount++;
                $groupSaved++;


            } catch (Exception $e) {
            }

            if ($savedCount < $maxQuestions) {
                sleep(DELAY_BETWEEN_QUESTION);
            }
        }

        if ($groupSaved === 3) {
            $talkNumber++;
        }
    }

    return $savedCount;
}

// ============================================================
// RUN FROM ADMIN
// ============================================================

function part4_run($level, $jumlah) {
    $level = strtolower(trim($level));

    $jumlah = filter_var($jumlah, FILTER_VALIDATE_INT);
    if ($jumlah === false) {
        throw new Exception('Jumlah soal tidak valid');
    }

    $allowedLevels = ['beginner', 'intermediate', 'advanced'];

    if (!in_array($level, $allowedLevels, true)) {
        throw new Exception('Level harus beginner, intermediate, atau advanced');
    }

    if ($jumlah < 3) {
        throw new Exception('Part 4 minimal menghasilkan 3 soal');
    }

    // ========================================================
    // HARUS KELIPATAN 3
    // ========================================================

    if ($jumlah % 3 !== 0) {
        throw new Exception('Jumlah soal Part 4 harus kelipatan 3, misalnya 3, 6, 9, 12, dan seterusnya');
    }

    if ($jumlah > 48) {
        throw new Exception('Jumlah soal Part 4 maksimal 48 dalam satu proses');
    }

    // ========================================================
    // MATERIAL ID
    // ========================================================

    $materialId = part4_get_material_id();


    $totalSaved = 0;
    $generationRound = 1;

    // ========================================================
    // GENERATE SAMPAI JUMLAH TERPENUHI
    // ========================================================

    while ($totalSaved < $jumlah) {
        $remaining = $jumlah - $totalSaved;

        if ($remaining < 3) {
            break;
        }


        $data = part4_generate_questions($level, $remaining);

        if (!$data) {
            break;
        }

        $saved = part4_save_questions($level, $data, $materialId, $remaining);

        $totalSaved += $saved;

        if ($saved === 0) {
            break;
        }

        if ($totalSaved % 3 !== 0) {
            break;
        }

        $generationRound++;

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
    part4_run('beginner', 3);
}