<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

// ============================================================
// CONFIG
// ============================================================

define('PART3_PART_ID', 3);
define('PART3_MATERIAL_ID', 35);

// ============================================================
// DIRECTORY
// ============================================================

define('PART3_BASE_DIR', __DIR__);
define('PART3_AUDIO_DIR', PART3_BASE_DIR . '/part3/audio/conversation');

if (!is_dir(PART3_AUDIO_DIR)) {
    mkdir(PART3_AUDIO_DIR, 0777, true);
}

// ============================================================
// CREATE CONVERSATION AUDIO
// ============================================================

function part3_create_conversation_audio($text, $filename) {
    try {
        return create_audio($text, $filename, PART3_AUDIO_DIR, 'part3/audio/conversation/');
    } catch (Exception $e) {
        return null;
    }
}

// ============================================================
// SHUFFLE OPTIONS
// ============================================================

function part3_shuffle_options($question) {
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

function part3_validate_question($question) {
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

    // Semua pilihan harus berbeda
    if (count(array_unique($options)) < 4) {
        return false;
    }

    return true;
}

// ============================================================
// VALIDATE CONVERSATION
// ============================================================

function part3_validate_conversation($conversation) {
    if (!is_array($conversation)) {
        return false;
    }

    $conversationText = $conversation['conversation'] ?? '';
    $questions = $conversation['questions'] ?? [];

    if (trim((string) $conversationText) === '') {
        return false;
    }

    if (!is_array($questions)) {
        return false;
    }

    // Kita gunakan tepat 3 soal untuk setiap conversation.
    if (count($questions) !== 3) {
        return false;
    }

    foreach ($questions as $question) {
        if (!part3_validate_question($question)) {
            return false;
        }
    }

    return true;
}

// ============================================================
// GENERATE CONVERSATIONS WITH GEMINI
// ============================================================

function part3_generate_questions($level, $jumlah) {
    $totalConversations = intdiv($jumlah, 3);

    $prompt = <<<PROMPT
Generate TOEIC Part 3 Conversations.

Difficulty level: {$level}

Create exactly {$totalConversations} conversations.

IMPORTANT:
- Each conversation MUST contain exactly 3 questions.
- Therefore the total number of questions MUST be exactly {$jumlah}.

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
- Adjust vocabulary and complexity to the {$level} level.

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
  {
    "conversation": "Man: ...\\nWoman: ...",
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
- {$totalConversations} conversations
- 3 questions per conversation
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
                throw new Exception('Gemini tidak menghasilkan conversation');
            }

            // Ambil sesuai jumlah conversation
            $data = array_slice($data, 0, $totalConversations);

            $validData = [];

            foreach ($data as $conversation) {
                if (part3_validate_conversation($conversation)) {
                    $validData[] = $conversation;
                } else {
                }
            }

            if ($validData) {
                return $validData;
            }

            throw new Exception('Tidak ada conversation valid');

        } catch (Exception $e) {

            if ($attempt < 4) {
                sleep(5);
            }
        }
    }

    return null;
}

// ============================================================
// SAVE CONVERSATIONS
// ============================================================

function part3_save_questions($level, $data, $maxQuestions) {
    $batchId = time() . '_' . rand(1000, 9999);

    $savedCount = 0;
    $conversationNumber = 1;

    foreach ($data as $conversationData) {
        if ($savedCount >= $maxQuestions) {
            break;
        }

        if (!part3_validate_conversation($conversationData)) {
            continue;
        }

        $conversation = $conversationData['conversation'];
        $questions = $conversationData['questions'];

        // Jangan simpan conversation parsial. Harus tersedia ruang untuk 3 soal.
        if ($savedCount + 3 > $maxQuestions) {
            break;
        }

        $startNumber = $savedCount + 1;
        $endNumber = $startNumber + 2;

        $convFilename = "{$level}_{$batchId}_conv_{$conversationNumber}_{$startNumber}-{$endNumber}";


        $conversationAudio = part3_create_conversation_audio($conversation, $convFilename);

        if (!$conversationAudio) {
            continue;
        }

        sleep(1);

        // ================================================
        // Siapkan seluruh soal dahulu
        // ================================================

        $preparedQuestions = [];
        $conversationValid = true;

        foreach ($questions as $question) {
            try {
                $question = part3_shuffle_options($question);

                if (!part3_validate_question($question)) {
                    $conversationValid = false;
                    break;
                }

                $preparedQuestions[] = $question;

            } catch (Exception $e) {
                $conversationValid = false;
                break;
            }
        }

        // Jika salah satu soal rusak, jangan simpan group parsial.
        if (!$conversationValid || count($preparedQuestions) !== 3) {

            // Hapus audio yang tidak digunakan
            $audioFullPath = PART3_BASE_DIR . '/' . $conversationAudio;

            if (file_exists($audioFullPath)) {
                @unlink($audioFullPath);
            }

            continue;
        }

        // ================================================
        // SIMPAN 3 SOAL
        // ================================================

        $groupSaved = 0;

        foreach ($preparedQuestions as $question) {
            $questionNumber = $savedCount + 1;


            try {
                insert_question(
                    PART3_PART_ID,
                    PART3_MATERIAL_ID,
                    $level,
                    $question['question'],
                    $question['option_a'],
                    $question['option_b'],
                    $question['option_c'],
                    $question['option_d'],
                    $question['answer'],
                    $question['explanation'],
                    null,
                    $conversationAudio // Ketiga soal memakai audio_file yang sama.
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
            $conversationNumber++;
        }
    }

    return $savedCount;
}

// ============================================================
// RUN FROM ADMIN
// ============================================================

function part3_run($level, $jumlah) {
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
        throw new Exception('Part 3 minimal menghasilkan 3 soal');
    }

    // ========================================================
    // PART 3 HARUS KELIPATAN 3
    // ========================================================

    if ($jumlah % 3 !== 0) {
        throw new Exception('Jumlah soal Part 3 harus kelipatan 3, misalnya 3, 6, 9, 12, dan seterusnya');
    }

    if ($jumlah > 48) {
        throw new Exception('Jumlah soal Part 3 maksimal 48 dalam satu proses');
    }


    $totalSaved = 0;
    $generationRound = 1;

    // ========================================================
    // GENERATE SAMPAI JUMLAH TERPENUHI
    // ========================================================

    while ($totalSaved < $jumlah) {
        $remaining = $jumlah - $totalSaved;

        // Karena setiap conversation harus 3 soal, remaining juga harus kelipatan 3.
        if ($remaining < 3) {
            break;
        }


        $data = part3_generate_questions($level, $remaining);

        if (!$data) {
            break;
        }

        $saved = part3_save_questions($level, $data, $remaining);

        $totalSaved += $saved;

        if ($saved === 0) {
            break;
        }

        // Pastikan hasil yang tersimpan tetap berupa group lengkap.
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
    part3_run('beginner', 3);
}