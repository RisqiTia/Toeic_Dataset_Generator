<?php

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/helpers.php';
require_once __DIR__ . '/db.php';

define('GM_PEXELS_URL', 'https://api.pexels.com/v1/search');

define('GM_START_PART', 1);
define('GM_END_PART', 7);

define('GM_IMAGE_DIR', __DIR__ . '/materials/images');
define('GM_AUDIO_DIR', __DIR__ . '/materials/audio');

if (!is_dir(GM_IMAGE_DIR)) {
    mkdir(GM_IMAGE_DIR, 0777, true);
}
if (!is_dir(GM_AUDIO_DIR)) {
    mkdir(GM_AUDIO_DIR, 0777, true);
}

// ================= IMAGE =================
function gm_download_image($query, $filename) {
    return download_image($query, $filename, GM_IMAGE_DIR, 'materials/images/');
}

// ================= AUDIO =================
function gm_create_audio($text, $filename) {
    return create_audio($text, $filename, GM_AUDIO_DIR, 'materials/audio/');
}

// ================= GENERATE =================
function gm_generate_material($part) {

    // ===== PART 3 & 4 =====
    if (in_array($part, [3, 4], true)) {

        $prompt = <<<PROMPT
Buat materi TOEIC Part {$part}.

Gunakan Bahasa Indonesia untuk penjelasan.
Gunakan Bahasa Inggris untuk soal.

Return JSON:

{
"title": "",
"intro": "",
"what_is_tested": ["", "", ""],

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
            "answer": "A",
            "explanation": ""
        }
    ]
},

"strategies": ["", "", ""],
"tips": ["", "", ""]
}

ATURAN:
- conversation = bahasa Inggris
- HARUS 3 soal
- penjelasan = bahasa Indonesia
- JSON 1 baris
PROMPT;

    // ===== PART LAIN =====
    } else {

        $prompt = <<<PROMPT
Buat materi TOEIC Part {$part}.

Gunakan Bahasa Indonesia untuk penjelasan.
Gunakan Bahasa Inggris untuk contoh soal.

Return JSON:

{
"title": "",
"intro": "",
"what_is_tested": ["", "", ""],

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

"strategies": ["", "", ""],
"tips": ["", "", ""],
"image_keyword": ""
}

ATURAN:
- contoh soal menyesuaikan aturan toeic yang sebenarnya misal part 3 & 4 ada 2/3 pertanyaan, maka buatlah sesuai itu
- Part 1 tanpa question
- JSON 1 baris
PROMPT;
    }

    for ($i = 0; $i < 5; $i++) {
        try {
            $responseText = gemini_generate_content($prompt);
            $data = extract_json_object($responseText);

            if ($data === null) {
                throw new Exception('JSON object tidak ditemukan');
            }

            return $data;

        } catch (Exception $e) {
            echo 'LLM error: ' . $e->getMessage() . "\n";
            sleep(5);
        }
    }

    return null;
}

// ================= BUILD TEXT =================
function gm_build_material_text($part, $data) {
    $intro = $data['intro'] ?? '';
    $what = $data['what_is_tested'] ?? [];
    $strategies = $data['strategies'] ?? [];
    $tips = $data['tips'] ?? [];

    // ===== PART 3 & 4 =====
    if (in_array($part, [3, 4], true)) {

        $example = $data['example'] ?? [];
        $convo = $example['conversation'] ?? '';
        $questions = $example['questions'] ?? [];

        $soalText = "\nPercakapan:\n{$convo}\n";

        foreach ($questions as $i => $q) {
            $n = $i + 1;
            $soalText .= "\nQuestion {$n}:\n{$q['question']}\n";
            $soalText .= "A. {$q['choices']['A']}\n";
            $soalText .= "B. {$q['choices']['B']}\n";
            $soalText .= "C. {$q['choices']['C']}\n";
            $soalText .= "D. {$q['choices']['D']}\n";
        }

        $pembahasan = '';
        foreach ($questions as $i => $q) {
            $n = $i + 1;
            $pembahasan .= "\nJawaban {$n}: {$q['answer']}\n{$q['explanation']}\n";
        }

    // ===== PART LAIN =====
    } else {

        $example = $data['example'] ?? [];
        $question = $example['question'] ?? '';
        $choices = $example['choices'] ?? [];

        $soalText = '';
        if ($question) {
            $soalText .= "{$question}\n\n";
        }

        $soalText .= 'A. ' . ($choices['A'] ?? '') . "\n";
        $soalText .= 'B. ' . ($choices['B'] ?? '') . "\n";
        $soalText .= 'C. ' . ($choices['C'] ?? '') . "\n";
        $soalText .= 'D. ' . ($choices['D'] ?? '') . "\n";

        $pembahasan = 'Jawaban: ' . ($example['answer'] ?? '') . "\n" . ($example['explanation'] ?? '');
    }

    $whatList = implode("\n- ", $what);
    $strategiesList = implode("\n- ", $strategies);
    $tipsList = implode("\n- ", $tips);

    return <<<TEXT
{$intro}

Apa yang diuji:
- {$whatList}

Contoh Soal:
{$soalText}

Pembahasan:
{$pembahasan}

Strategi:
- {$strategiesList}

Tips:
- {$tipsList}

TEXT;
}

// ================= AUDIO =================
function gm_build_audio($part, $data) {
    if (in_array($part, [3, 4], true)) {
        return $data['example']['conversation'] ?? null;
    }

    $example = $data['example'] ?? [];
    $choices = $example['choices'] ?? [];
    $question = $example['question'] ?? '';

    if ($part === 1) {
        return "A. {$choices['A']} B. {$choices['B']} C. {$choices['C']} D. {$choices['D']}";
    }

    if ($part === 2) {
        return "{$question} A. {$choices['A']} B. {$choices['B']} C. {$choices['C']}";
    }

    return null;
}

// ================= MAIN =================
function gm_run() {
    echo "START GENERATE TOEIC MATERIAL\n";

    for ($part = GM_START_PART; $part <= GM_END_PART; $part++) {

        echo "\nPart {$part}\n";

        $data = gm_generate_material($part);
        if (!$data) {
            continue;
        }

        $text = gm_build_material_text($part, $data);

        $imagePath = null;
        if ($part === 1) {
            $keyword = $data['image_keyword'] ?? null;
            if ($keyword) {
                $imagePath = gm_download_image($keyword, "part{$part}");
            }
        }

        $audioScript = gm_build_audio($part, $data);
        $audioPath = $audioScript ? gm_create_audio($audioScript, "part{$part}") : null;

        insert_material($part, $data['title'] ?? '', $imagePath, $audioPath, $text);

        echo "Saved\n";
        sleep(10);
    }

    echo "DONE\n";
}

if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['SCRIPT_FILENAME'] ?? '')) {
    gm_run();
}
