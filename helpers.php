<?php

require_once __DIR__ . '/config.php';

define('PEXELS_URL', 'https://api.pexels.com/v1/search');

/**
 * Download 1 gambar dari Pexels berdasarkan keyword lalu simpan ke $dir.
 *
 * @param string $keyword
 * @param string $filename tanpa ekstensi
 * @param string $dir      folder absolut tujuan penyimpanan
 * @param string $dbPrefix path relatif yang disimpan ke database (mis. "part1/images/")
 * @return string|null path relatif untuk disimpan ke DB, atau null jika gagal
 */
function download_image($keyword, $filename, $dir, $dbPrefix) {
    try {
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => PEXELS_URL . '?' . http_build_query([
                'query' => $keyword,
                'per_page' => 1,
            ]),
            CURLOPT_HTTPHEADER => ['Authorization: ' . PEXELS_API_KEY],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 30,
        ]);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if (!$response || $httpCode < 200 || $httpCode >= 300) {
            echo "Image tidak ditemukan: $keyword\n";
            return null;
        }

        $data = json_decode($response, true);

        if (empty($data['photos'])) {
            echo "Image tidak ditemukan: $keyword\n";
            return null;
        }

        $imgUrl = $data['photos'][0]['src']['large'];

        $imgContent = @file_get_contents($imgUrl);
        if ($imgContent === false) {
            return null;
        }

        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }

        $filenameWithExt = "$filename.jpg";
        $fullPath = rtrim($dir, '/') . '/' . $filenameWithExt;

        file_put_contents($fullPath, $imgContent);

        return $dbPrefix . $filenameWithExt;

    } catch (Exception $e) {
        echo 'Image download error: ' . $e->getMessage() . "\n";
        return null;
    }
}

/**
 * Membuat audio TTS bahasa Inggris dari teks, menggantikan gTTS milik Python.
 * Menggunakan endpoint unofficial Google Translate TTS (yang sama dipakai gTTS),
 * dipecah per potongan <=200 karakter lalu digabung.
 *
 * @param string $text
 * @param string $filename tanpa ekstensi
 * @param string $dir      folder absolut tujuan penyimpanan
 * @param string $dbPrefix path relatif yang disimpan ke database (mis. "part1/audio/")
 * @return string|null path relatif untuk disimpan ke DB, atau null jika gagal
 */
function create_audio($text, $filename, $dir, $dbPrefix, $lang = 'en') {
    try {
        $chunks = gtts_split_text((string) $text);

        $audioData = '';
        foreach ($chunks as $chunk) {
            $url = 'https://translate.google.com/translate_tts?' . http_build_query([
                'ie' => 'UTF-8',
                'q' => $chunk,
                'tl' => $lang,
                'client' => 'tw-ob',
            ]);

            $ch = curl_init($url);
            curl_setopt_array($ch, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT => 30,
                CURLOPT_USERAGENT => 'Mozilla/5.0',
            ]);
            $chunkAudio = curl_exec($ch);
            curl_close($ch);

            if ($chunkAudio === false) {
                return null;
            }

            $audioData .= $chunkAudio;
        }

        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }

        $filenameWithExt = "$filename.mp3";
        $fullPath = rtrim($dir, '/') . '/' . $filenameWithExt;

        file_put_contents($fullPath, $audioData);

        return $dbPrefix . $filenameWithExt;

    } catch (Exception $e) {
        echo 'Audio error: ' . $e->getMessage() . "\n";
        return null;
    }
}

/**
 * Memecah teks menjadi potongan-potongan <=200 karakter agar aman
 * untuk endpoint translate_tts (mirip perilaku internal gTTS).
 */
function gtts_split_text($text, $maxLen = 200) {
    $text = trim($text);
    if ($text === '') {
        return [];
    }

    $sentences = preg_split('/(?<=[.!?])\s+/', $text);
    $chunks = [];
    $current = '';

    foreach ($sentences as $sentence) {
        if (strlen($current) + strlen($sentence) + 1 > $maxLen) {
            if ($current !== '') {
                $chunks[] = $current;
            }
            $current = $sentence;
        } else {
            $current = $current === '' ? $sentence : $current . ' ' . $sentence;
        }
    }

    if ($current !== '') {
        $chunks[] = $current;
    }

    return $chunks;
}

/**
 * Ekstrak & decode JSON object {} pertama dari teks respons Gemini.
 */
function extract_json_object($text) {
    $text = str_replace(['```json', '```'], '', $text);
    $text = trim($text);

    $start = strpos($text, '{');
    $end = strrpos($text, '}');

    if ($start === false || $end === false) {
        return null;
    }

    $json = substr($text, $start, $end - $start + 1);
    $json = str_replace("\n", ' ', $json);

    $decoded = json_decode($json, true);
    return $decoded;
}

/**
 * Ekstrak & decode JSON array [] pertama dari teks respons Gemini.
 */
function extract_json_array($text) {
    $text = str_replace(['```json', '```'], '', $text);
    $text = trim($text);

    $start = strpos($text, '[');
    $end = strrpos($text, ']');

    if ($start === false || $end === false) {
        return null;
    }

    $json = substr($text, $start, $end - $start + 1);

    $decoded = json_decode($json, true);
    return $decoded;
}
