# Fullstack AI Chatbot & Client Billing Portal

Sistem terpadu portal klien, manajemen tagihan, dan AI Chatbot berbasis **FastAPI**, **SQLite**, **React.js**, serta **Google Gemini API**.

Repositori ini terdiri dari:
- `backend/`: REST API FastAPI dengan validasi Pydantic v2, Google Gemini Tool Calling & Vector Search, Policy Gate aktivasi layanan, dan unit testing Pytest.
- `frontend/`: Portal klien berbasis React.js (Vite + Tailwind CSS) dengan dashboard invoice dan widget chatbot AI interaktif.
- `DEBUGGING.md`: Analisis teknis dan arsitektur untuk studi kasus kebocoran konteks, prompt injection, dan reliabilitas LLM provider.

---

## 1. Menjalankan Backend

### Persiapan & Inisialisasi Database
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Inisialisasi database SQLite dan data simulasi awal (clients, invoices, knowledge_bases)
python init_db.py
```

### Menjalankan Server FastAPI
```powershell
python -m uvicorn main:app --reload --port 8000
```
- Swagger UI (OpenAPI Docs): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Endpoint Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Menjalankan Unit Testing Backend (94 Tests)
```powershell
cd backend
python -m pytest -v
```

Dokumentasi lengkap mengenai API endpoint, struktur backend, dan skenario pengujian TC-01 s/d TC-10 tersedia di [backend/README.md](file:///backend/README.md).

---

## 2. Menjalankan Frontend

```powershell
cd frontend
npm install
npm run dev
```
Aplikasi frontend dapat diakses melalui browser di `http://localhost:5173`.
