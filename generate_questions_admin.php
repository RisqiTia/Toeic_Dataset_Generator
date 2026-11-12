<?php

// ============================================================
// BASE DIRECTORY
// ============================================================

chdir(__DIR__);

require_once __DIR__ . '/part1_photograph.php';
require_once __DIR__ . '/part2_question_response.php';
require_once __DIR__ . '/part3_conversation.php';
require_once __DIR__ . '/part4_talks.php';
require_once __DIR__ . '/part5_incomplete_sentences.php';
require_once __DIR__ . '/part6_text_completion.php';
require_once __DIR__ . '/part7_reading_comprehension.php';

// ============================================================
// GENERATE QUESTIONS
// ============================================================
// Dipanggil oleh app/question_admin.php sebagai:
//   $result = gqa_run($partId, $level, $jumlah);
// Melempar Exception kalau ada kesalahan, dan mengembalikan
// array hasil (bukan langsung echo/exit) supaya bisa dibungkus
// sendResponse() oleh question_admin.php.
// ============================================================

function gqa_run($part, $level, $jumlah)
{
    // ========================================================
    // VALIDASI
    // ========================================================

    $part = filter_var($part, FILTER_VALIDATE_INT);
    $jumlah = filter_var($jumlah, FILTER_VALIDATE_INT);
    $level = strtolower(trim((string) $level));

    if ($part === false || $jumlah === false) {
        throw new Exception('Parameter tidak valid.');
    }

    if ($part < 1 || $part > 7) {
        throw new Exception('Part harus antara 1 sampai 7.');
    }

    $allowedLevels = [
        'beginner',
        'intermediate',
        'advanced',
    ];

    if (!in_array($level, $allowedLevels, true)) {
        throw new Exception(
            'Level harus beginner, intermediate, atau advanced.'
        );
    }

    if ($jumlah < 1) {
        throw new Exception('Jumlah minimal 1.');
    }

    if ($jumlah > 50) {
        throw new Exception('Jumlah maksimal 50.');
    }

    // ========================================================
    // GENERATE
    // ========================================================

    switch ($part) {

        case 1:
            $generated = part1_run($level, $jumlah);
            break;

        case 2:
            $generated = part2_run($level, $jumlah);
            break;

        case 3:
            $generated = part3_run($level, $jumlah);
            break;

        case 4:
            $generated = part4_run($level, $jumlah);
            break;

        case 5:
            $generated = part5_run($level, $jumlah);
            break;

        case 6:
            $generated = part6_run($level, $jumlah);
            break;

        case 7:
            $generated = part7_run($level, $jumlah);
            break;

        default:
            throw new Exception("Generator Part {$part} belum diaktifkan.");
    }

    if ($generated <= 0) {
        throw new Exception('Tidak ada soal yang berhasil dibuat.');
    }

    return [
        'part' => $part,
        'level' => $level,
        'requested' => $jumlah,
        'generated' => $generated,
        'success' => ($generated == $jumlah),
        'message' => ($generated == $jumlah)
            ? 'Generate soal berhasil.'
            : 'Generate selesai tetapi sebagian soal gagal dibuat.',
    ];
}