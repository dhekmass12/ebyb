# Frontend Portal Klien & Invoices

Aplikasi front-end berbasis **React.js (Vite)** untuk Technical Test Sistem Layanan Digital & Chatbot.

## Fitur Utama

1. **Authentication Page (`AuthPage.jsx`)**:
   - Meminta input **Client ID** dan **Password**.
   - Validasi `Client ID` harus sesuai kolom `client_id` di tabel `clients` (misal: `CLI-001`, `CLI-002`, `CLI-003`).
   - Password tidak divalidasi (bebas diisi).
   - Menyimpan `client_id` ke dalam **Local Storage** saat login berhasil.
   - Dilengkapi tombol shortcut demo klien untuk memudahkan pengujian.

2. **Landing Page (`LandingPage.jsx`)**:
   - Menampilkan daftar semua klien dari tabel `clients`.
   - Menandai akun yang sedang aktif/login via Local Storage.
   - Ketika kartu klien diklik, menampilkan daftar invoice milik klien tersebut.
   - Invoice diperoleh dengan mencocokkan kolom `client_id` di tabel `invoices` dengan `client_id` di **Local Storage**.
   - Menyajikan informasi total tagihan, pembayaran diterima, dan sisa tagihan.

3. **Chatbot Widget (`ChatbotWidget.jsx`)**:
   - Icon floating action button di pojok kanan bawah.
   - Ketika diklik, menampilkan jendela interaktif Chatbot AI.
   - Mode tampilan (UI only) sesuai ketentuan, dengan saran cepat pertanyaan dan balasan mockup.

## Cara Menjalankan

### 1. Jalankan Backend (FastAPI)
```bash
# Dari root directory
.\venv\Scripts\python -m uvicorn main:app --reload --port 8000
```
Backend berjalan di `http://127.0.0.1:8000`.

### 2. Jalankan Frontend (React)
```bash
cd frontend
npm run dev
```
Frontend berjalan di `http://localhost:5173`.
Proxy API diarahkan otomatis ke backend di port 8000.
