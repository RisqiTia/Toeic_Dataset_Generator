<?php
// ============================================================
// CONFIG
// ============================================================

define('GEMINI_API_KEY', ''); // API
define('PEXELS_API_KEY', ''); //API Pexel

define('GEMINI_MODEL', 'gemini-2.5-flash');
define('GEMINI_URL', 'https://generativelanguage.googleapis.com/v1beta/models/' . GEMINI_MODEL . ':generateContent?key=' . GEMINI_API_KEY);

define('LEVELS', ['intermediate', 'advanced']);

define('TOTAL_QUESTIONS', 10);
define('TOTAL_BATCH', 1); // ubah kalau mau generate berkali-kali dalam 1 run
define('DELAY_BETWEEN_QUESTION', 1);
define('DELAY_BETWEEN_LEVEL', 60);

/**
 * Call Gemini generateContent REST API (menggantikan client Python SDK).
 *
 * @param string $prompt
 * @return string Teks respons dari Gemini
 * @throws Exception jika request gagal
 */
function gemini_generate_content($prompt) {
    $payload = [
        'contents' => [
            [
                'parts' => [
                    ['text' => $prompt]
                ]
            ]
        ]
    ];

    $ch = curl_init(GEMINI_URL);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS => json_encode($payload),
        CURLOPT_TIMEOUT => 60,
    ]);

    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno) {
        throw new Exception("cURL error: $error");
    }

    if ($httpCode < 200 || $httpCode >= 300) {
        throw new Exception("Gemini API HTTP $httpCode: $response");
    }

    $data = json_decode($response, true);

    if (!isset($data['candidates'][0]['content']['parts'][0]['text'])) {
        throw new Exception("Format respons Gemini tidak dikenali: $response");
    }

    return $data['candidates'][0]['content']['parts'][0]['text'];
}
