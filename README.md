# Konversi Python → PHP: TOEIC Dataset Generator

## Isi

| File asli (.py) | File PHP | Keterangan |
|---|---|---|
| config.py | config.php | API key Gemini + fungsi `gemini_generate_content()` (pengganti SDK Python, pakai cURL ke REST API) |
| db.py | db.php | Koneksi MySQL pakai `mysqli` + prepared statements |
| (baru) | helpers.php | Fungsi bersama: `download_image()`, `create_audio()` (TTS), `extract_json_object/array()` |
| generate_materials.py | generate_materials.php | Generate materi Part 1-7 sekaligus |
| generate_material_admin.py | generate_material_admin.php | Generate 1 materi untuk part tertentu |
| generate_questions_admin.py | generate_questions_admin.php | Entry point dipanggil dari dashboard admin (bisa lewat CLI **atau** HTTP `?part=&level=&jumlah=`) |
| part1_photograph.py … part7_reading_comprehension.py | part1_photograph.php … part7_reading_comprehension.php | Generator soal per part |

## Cara pakai di hosting

1. Upload semua file `.php` ke satu folder (misalnya `toeic_dataset_generator/`).
2. Pastikan hosting mengizinkan **outbound cURL** ke `generativelanguage.googleapis.com`, `api.pexels.com`, dan `translate.google.com` (untuk TTS). Banyak shared hosting membatasi ini — cek dengan tim support hosting jika terjadi error koneksi.
3. Pastikan ekstensi PHP `curl`, `mysqli`, dan `json` aktif (biasanya sudah default di cPanel/hosting PHP standar).
4. Untuk generate soal dari dashboard admin, panggil:
   ```
   https://domainanda.com/toeic_dataset_generator/generate_questions_admin.php?part=1&level=beginner&jumlah=5
   ```
   Responnya JSON: `{"status":"success","message":...,"generated":...}`.
5. Untuk generate materi:
   ```
   php generate_material_admin.php 1
   ```
   (atau panggil `gma_run(1)` dari script PHP lain / endpoint web sendiri — file ini belum saya buatkan wrapper HTTP karena Python-nya juga dipakai lewat CLI/manual).

## Hal penting yang perlu Anda tindak lanjuti

1. **API key & password database ter-hardcode di kode dan sempat terunggah ke saya.**
   File `config.py` berisi Gemini API key & Pexels API key, dan `db.py` berisi password database (`Toeic12345*`) dalam bentuk plain text. Saya salin apa adanya ke PHP supaya perilakunya identik, tapi **saya sarankan Anda segera meng-generate ulang (rotate) key/password tersebut** setelah ini, lalu pindahkan ke environment variable atau file config di luar folder public (tidak bisa diakses lewat URL langsung).

2. **Text-to-Speech (gTTS) tidak punya library resmi di PHP.**
   Python memakai library `gTTS` yang sebenarnya hanya memanggil endpoint tidak resmi Google Translate (`translate_tts`). Saya reproduksi ulang pemanggilan endpoint yang sama langsung lewat cURL di `helpers.php` (fungsi `create_audio()`), termasuk logika memecah teks panjang jadi beberapa potongan seperti yang dilakukan gTTS. Ini **endpoint tidak resmi** — Google bisa membatasi/memblokir permintaan dari IP hosting kalau volume tinggi. Kalau ke depan bermasalah, pertimbangkan API TTS resmi (Google Cloud Text-to-Speech, dsb).

3. **Semua file awalnya adalah CLI script**, jadi bagian `if __name__ == "__main__"` saya konversi jadi pengecekan `php_sapi_name() === 'cli'` — supaya masih bisa dites lewat terminal (`php part1_photograph.php`), tapi normalnya dipanggil sebagai fungsi dari `generate_questions_admin.php`.

4. Saya tidak bisa menjalankan PHP di lingkungan saya untuk mengetes langsung (tidak ada interpreter PHP tersedia), jadi saya sudah mengecek keseimbangan tanda kurung/kurawal di semua file secara otomatis, tapi **sangat disarankan untuk mengetesnya dulu di staging/local sebelum dipakai produksi**, terutama bagian pemanggilan Gemini API dan penyimpanan gambar/audio.
