<?php

error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once 'config.php';
require_once 'db.php';
require_once 'helpers.php';

define('GMA_IMAGE_DIR', __DIR__ . '/materials/images');
define('GMA_AUDIO_DIR', __DIR__ . '/materials/audio');

if (!is_dir(GMA_IMAGE_DIR)) {
    mkdir(GMA_IMAGE_DIR, 0777, true);
}
if (!is_dir(GMA_AUDIO_DIR)) {
    mkdir(GMA_AUDIO_DIR, 0777, true);
}

// ============================================================
// DOWNLOAD IMAGE
// ============================================================

function gma_download_image($query, $filename) {
    if (!$query) {
        return null;
    }

    $path = download_image($query, $filename, GMA_IMAGE_DIR, 'materials/images/');

    return $path;
}

// ============================================================
// CREATE AUDIO
// ============================================================

function gma_create_audio($text, $filename) {
    if (!$text) {
        return null;
    }

    $path = create_audio($text, $filename, GMA_AUDIO_DIR, 'materials/audio/');

    return $path;
}

// ============================================================
// FIX JSON
// ============================================================

function gma_clean_json($text) {
    $text = trim(str_replace(['```json', '```'], '', $text));

    $start = strpos($text, '{');
    $end = strrpos($text, '}');

    if ($start === false || $end === false) {
        throw new Exception('JSON tidak ditemukan pada respons Gemini.');
    }

    return substr($text, $start, $end - $start + 1);
}

// ============================================================
// GENERATE MATERIAL
// ============================================================

function gma_generate_material($part, $maxRetries = 5) {

    // --------------------------------------------------------
    // PART 3 & 4
    // --------------------------------------------------------

    if (in_array($part, [3, 4], true)) {

        $prompt = <<<PROMPT
Buat satu materi pembelajaran TOEIC Part {$part}.

Gunakan Bahasa Indonesia untuk:
- intro
- what_is_tested
- explanation
- strategies
- tips

Gunakan Bahasa Inggris untuk:
- conversation
- question
- choices

Buat contoh sesuai format TOEIC Part {$part}.

Satu conversation harus memiliki tepat 3 pertanyaan.

Return VALID JSON ONLY:

{
    "title": "",
    "intro": "",
    "what_is_tested": [
        "",
        "",
        ""
    ],
    "example": {
        "conversation": "",
        "questions": [
            {
                "question": "",
                "choices": {
                    "A": "",
                    "B": "",
                    "C": "",
                    "D": ""
                },
                "answer": "A",
                "explanation": ""
            },
            {
                "question": "",
                "choices": {
                    "A": "",
                    "B": "",
                    "C": "",
                    "D": ""
                },
                "answer": "B",
                "explanation": ""
            },
            {
                "question": "",
                "choices": {
                    "A": "",
                    "B": "",
                    "C": "",
                    "D": ""
                },
                "answer": "C",
                "explanation": ""
            }
        ]
    },
    "strategies": [
        "",
        "",
        ""
    ],
    "tips": [
        "",
        "",
        ""
    ]
}

ATURAN:
- Conversation harus natural.
- Conversation menggunakan Bahasa Inggris.
- Harus tepat 3 pertanyaan.
- Setiap pertanyaan memiliki 4 pilihan.
- Hanya satu jawaban benar.
- Explanation menggunakan Bahasa Indonesia.
- Jangan menambahkan teks di luar JSON.
PROMPT;

    // --------------------------------------------------------
    // PART 1, 2, 5, 6, 7
    // --------------------------------------------------------

    } else {

        $prompt = <<<PROMPT
Buat satu materi pembelajaran TOEIC Part {$part}.

Gunakan Bahasa Indonesia untuk:
- intro
- what_is_tested
- explanation
- strategies
- tips

Gunakan Bahasa Inggris untuk contoh soal dan pilihan jawaban.

Return VALID JSON ONLY:

{
    "title": "",
    "intro": "",
    "what_is_tested": [
        "",
        "",
        ""
    ],
    "example": {
        "question": "",
        "choices": {
            "A": "",
            "B": "",
            "C": "",
            "D": ""
        },
        "answer": "A",
        "explanation": ""
    },
    "strategies": [
        "",
        "",
        ""
    ],
    "tips": [
        "",
        "",
        ""
    ],
    "image_keyword": ""
}

ATURAN:

- Materi harus sesuai dengan TOEIC Part {$part}.
- Explanation menggunakan Bahasa Indonesia.
- Jangan menambahkan teks di luar JSON.

KHUSUS PART 1:
- question harus berupa string kosong "".
- Pilihan A-D berupa deskripsi foto dalam Bahasa Inggris.
- image_keyword harus menggambarkan jawaban yang benar.
- image_keyword menggunakan Bahasa Inggris.

KHUSUS PART 2:
- question berupa pertanyaan atau pernyataan listening.
- Hanya pilihan A, B, C yang digunakan.
- choices D harus berupa string kosong "".

KHUSUS PART 5:
- question harus berupa incomplete sentence.
- Gunakan ___ sebagai bagian yang kosong.
- Tidak membutuhkan gambar atau audio.

KHUSUS PART 6:
- Contoh harus menggambarkan konsep Text Completion.
- Tidak membutuhkan gambar atau audio.

KHUSUS PART 7:
- Contoh harus menggambarkan Reading Comprehension.
- Tidak membutuhkan gambar atau audio.
PROMPT;
    }

    // --------------------------------------------------------
    // REQUEST GEMINI
    // --------------------------------------------------------

    for ($attempt = 0; $attempt < $maxRetries; $attempt++) {
        try {
            $responseText = gemini_generate_content($prompt);

            $cleaned = gma_clean_json($responseText);

            $data = json_decode($cleaned, true);

            if (!is_array($data)) {
                throw new Exception('Respons Gemini bukan JSON object.');
            }

            // Validasi dasar
            if (empty($data['title'])) {
                throw new Exception('Title materi kosong.');
            }

            if (empty($data['intro'])) {
                throw new Exception('Intro materi kosong.');
            }

            if (empty($data['example'])) {
                throw new Exception('Example materi kosong.');
            }

            // Part 3 dan 4 harus punya 3 soal
            if (in_array($part, [3, 4], true)) {
                $questions = $data['example']['questions'] ?? [];

                if (count($questions) !== 3) {
                    throw new Exception('Part 3/4 harus memiliki tepat 3 contoh soal.');
                }
            }

            return $data;

        } catch (Exception $e) {
            if ($attempt < $maxRetries - 1) {
                sleep(5);
            }
        }
    }

    return null;
}

// ============================================================
// BUILD MATERIAL TEXT
// ============================================================

function gma_build_material_text($part, $data) {
    $intro = $data['intro'] ?? '';
    $what = $data['what_is_tested'] ?? [];
    $strategies = $data['strategies'] ?? [];
    $tips = $data['tips'] ?? [];

    // --------------------------------------------------------
    // PART 3 & 4
    // --------------------------------------------------------

    if (in_array($part, [3, 4], true)) {

        $example = $data['example'] ?? [];
        $conversation = $example['conversation'] ?? '';
        $questions = $example['questions'] ?? [];

        $questionText = "\nPercakapan:\n{$conversation}\n";
        $discussion = '';

        foreach ($questions as $i => $question) {
            $index = $i + 1;
            $choices = $question['choices'] ?? [];

            $questionText .= "\nQuestion {$index}:\n"
                . ($question['question'] ?? '') . "\n"
                . 'A. ' . ($choices['A'] ?? '') . "\n"
                . 'B. ' . ($choices['B'] ?? '') . "\n"
                . 'C. ' . ($choices['C'] ?? '') . "\n"
                . 'D. ' . ($choices['D'] ?? '') . "\n";

            $discussion .= "\nJawaban {$index}: "
                . ($question['answer'] ?? '') . "\n"
                . ($question['explanation'] ?? '') . "\n";
        }

    // --------------------------------------------------------
    // PART LAIN
    // --------------------------------------------------------

    } else {

        $example = $data['example'] ?? [];
        $question = $example['question'] ?? '';
        $choices = $example['choices'] ?? [];

        $questionText = '';

        if ($question) {
            $questionText .= "{$question}\n\n";
        }

        $questionText .= 'A. ' . ($choices['A'] ?? '') . "\n"
            . 'B. ' . ($choices['B'] ?? '') . "\n"
            . 'C. ' . ($choices['C'] ?? '') . "\n";

        // Part 2 hanya A-C
        if ($part !== 2) {
            $questionText .= 'D. ' . ($choices['D'] ?? '') . "\n";
        }

        $discussion = 'Jawaban: ' . ($example['answer'] ?? '') . "\n" . ($example['explanation'] ?? '');
    }

    // --------------------------------------------------------
    // FINAL TEXT
    // --------------------------------------------------------

    $whatText = implode("\n- ", array_map('strval', $what));
    $strategiesText = implode("\n- ", array_map('strval', $strategies));
    $tipsText = implode("\n- ", array_map('strval', $tips));

    return <<<TEXT
{$intro}

Apa yang diuji:
- {$whatText}

Contoh Soal:
{$questionText}

Pembahasan:
{$discussion}

Strategi:
- {$strategiesText}

Tips:
- {$tipsText}

TEXT;
}

// ============================================================
// BUILD AUDIO
// ============================================================

function gma_build_audio($part, $data) {
    $example = $data['example'] ?? [];

    // Part 3 & 4
    if (in_array($part, [3, 4], true)) {
        return $example['conversation'] ?? '';
    }

    $choices = $example['choices'] ?? [];
    $question = $example['question'] ?? '';

    // Part 1
    if ($part === 1) {
        return 'A. ' . ($choices['A'] ?? '') . '. '
            . 'B. ' . ($choices['B'] ?? '') . '. '
            . 'C. ' . ($choices['C'] ?? '') . '. '
            . 'D. ' . ($choices['D'] ?? '') . '.';
    }

    // Part 2
    if ($part === 2) {
        return "{$question}. "
            . 'A. ' . ($choices['A'] ?? '') . '. '
            . 'B. ' . ($choices['B'] ?? '') . '. '
            . 'C. ' . ($choices['C'] ?? '') . '.';
    }

    // Part 5-7 tidak perlu audio
    return null;
}

// ============================================================
// RUN
// ============================================================

function gma_run($part)
{
    $part = filter_var($part, FILTER_VALIDATE_INT);

    if ($part === false) {
        throw new Exception("Part tidak valid.");
    }

    if ($part < 1 || $part > 7) {
        throw new Exception("Part harus antara 1 sampai 7.");
    }

    // Generate data dari Gemini
    $data = gma_generate_material($part);

    if (!$data) {
        throw new Exception("Gagal generate materi.");
    }

    // Build text materi
    $materialText = gma_build_material_text($part, $data);

    // Nama file
    $filename = "part{$part}_" . time();

    // Download gambar (khusus Part 1)
    $imagePath = null;

    if ($part == 1) {
        $keyword = $data["image_keyword"] ?? "";

        if (!empty($keyword)) {
            $imagePath = gma_download_image($keyword, $filename);
        }
    }

    // Generate audio
    $audioPath = null;

    $audioScript = gma_build_audio($part, $data);

    if (!empty($audioScript)) {
        $audioPath = gma_create_audio($audioScript, $filename);
    }

    // Simpan ke database
    $materialId = insert_material(
        $part,
        $data["title"] ?? "TOEIC Part {$part}",
        $imagePath,
        $audioPath,
        $materialText
    );

    if (!$materialId) {
        throw new Exception("Gagal menyimpan materi.");
    }

    return [
        "material_id" => $materialId,
        "part" => $part,
        "title" => $data["title"] ?? "",
        "image" => $imagePath,
        "audio" => $audioPath,
        "success" => true,
        "message" => "Generate materi berhasil."
    ];
}