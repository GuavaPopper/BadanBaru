# Height Detection System

Sebuah aplikasi web berbasis computer vision untuk mengukur tinggi badan menggunakan kamera webcam.

## Fitur

- **Deteksi Jarak**: Mengukur jarak antara pengguna dan kamera untuk memastikan pengukuran yang akurat
- **Pengukuran Tinggi Badan**: Menggunakan MediaPipe Pose Detection untuk mendeteksi titik-titik kunci pada tubuh dan menghitung tinggi
- **Antarmuka Web**: Tampilan web yang mudah digunakan dan responsif

## Persyaratan

- Python 3.7 atau lebih baru
- Webcam
- Paket Python yang diperlukan (lihat `requirements.txt`)

## Instalasi

1. Clone repository ini atau download sebagai ZIP file

```bash
git clone https://github.com/yourusername/Height-Detection.git
```

2. Masuk ke direktori project

```bash
cd Height-Detection
```

3. Install semua dependensi yang diperlukan

```bash
pip install -r requirements.txt
```

## Cara Penggunaan

1. Jalankan aplikasi Flask

```bash
python app.py
```

2. Buka browser dan akses `http://127.0.0.1:5000/`

3. Klik tombol "Mulai Pengukuran" untuk memulai proses deteksi

4. Ikuti instruksi pada halaman Deteksi Jarak untuk memposisikan diri pada jarak yang tepat dari kamera

5. Setelah jarak optimal tercapai, klik tombol "Lakukan Ukur Badan" untuk melanjutkan ke pengukuran tinggi

6. Pada halaman Pengukuran Tinggi Badan, pastikan seluruh tubuh terlihat dalam frame kamera untuk mendapatkan hasil pengukuran tinggi badan

## Struktur File

- `app.py`: Aplikasi Flask utama
- `Body_Detection.py`: Script asli untuk deteksi tubuh dan pengukuran tinggi
- `ex.py`: Script asli untuk deteksi jarak
- `templates/`: Direktori berisi template HTML
  - `index.html`: Halaman utama
  - `face_detection.html`: Halaman deteksi jarak
  - `body_detection.html`: Halaman pengukuran tinggi badan

## Requirements

Buat file `requirements.txt` untuk menginstal semua dependensi yang diperlukan:

```
flask==2.3.3
opencv-python==4.8.0.76
mediapipe==0.10.3
numpy==1.24.3
pyttsx3==2.90
```

## Perbaikan Masalah Umum

1. **Webcam tidak terdeteksi**
   - Pastikan tidak ada aplikasi lain yang menggunakan webcam
   - Coba restart komputer dan jalankan aplikasi lagi

2. **Pengukuran tidak akurat**
   - Pastikan Anda berada pada jarak yang tepat (330-360 cm) dari kamera
   - Pastikan pencahayaan ruangan cukup baik
   - Pastikan seluruh tubuh terlihat dalam frame kamera

3. **Aplikasi crash**
   - Pastikan semua dependensi sudah terinstal dengan benar
   - Periksa apakah webcam berfungsi dengan baik

## Lisensi

[MIT License](LICENSE)

## Kontributor

- [Your Name](https://github.com/yourusername) 