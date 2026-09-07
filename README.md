<div align="center">

# 🌱 EcoFlow - Smart Eco-Enzyme Management System Powered by AI

### Submission for ITECHNO CUP 2026 - Web Development
**BISMILLAH TEMBUS**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20Site-brightgreen?style=for-the-badge&logo=vercel)](https://ecoflow-demo.vercel.app)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/GomalRajaGula/prd-ecoflow-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

*Platform cerdas untuk digitalisasi manajemen eco-enzyme dari hulu ke hilir dengan integrasi AI*

</div>

---

## 📑 Daftar Isi

- [Tim Developer](#-tim-developer)
- [Tentang Proyek](#-tentang-proyek)
- [Fitur Unggulan](#-fitur-unggulan)
- [Demo & Screenshot](#-demo--screenshot)
- [Teknologi](#-teknologi)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Instalasi & Setup](#-instalasi--setup)
- [Penggunaan](#-penggunaan)
- [API Documentation](#-api-documentation)
- [Lisensi](#-lisensi)

---

## 👥 Tim Developer

| Nama | Role | GitHub |
|------|------|--------|
| **Firly Nurrohman** | Project Manager | [@firlyn113](https://github.com/firlyn113) |
| **Achmal Maulana** | Backend Developer | [@GomalRajaGula](https://github.com/GomalRajaGula) |
| **Muhammad Zaki** | Frontend Developer | [@muhzakifp](https://github.com/muhzakifp) |


---

## 📖 Tentang Proyek

### 🎯 Latar Belakang

Proses fermentasi eco-enzyme membutuhkan waktu **90 hari** dan memerlukan monitoring yang konsisten untuk menghasilkan produk berkualitas. Namun, sebagian besar praktisi menghadapi tantangan:

- ❌ Kesulitan mencatat dan memantau progres fermentasi secara sistematis
- ❌ Minimnya edukasi tentang penanganan masalah selama fermentasi
- ❌ Tidak ada panduan konversi eco-enzyme menjadi produk komersial
- ❌ Sulit menghitung dampak lingkungan dari aktivitas eco-enzyme

### 💡 Solusi

**EcoFlow** adalah platform manajemen eco-enzyme berbasis web yang mengintegrasikan teknologi AI untuk:

- ✅ **Digitalisasi penuh** proses fermentasi dari awal hingga akhir
- ✅ **Monitoring real-time** dengan pencatatan progres harian
- ✅ **Panduan cerdas** berbasis AI untuk penanganan masalah fermentasi
- ✅ **Roadmap pemrosesan** interaktif dari eco-enzyme menjadi produk jadi
- ✅ **Analisis bisnis** untuk konversi menjadi produk komersial
- ✅ **Perhitungan dampak lingkungan** (CO₂ avoided, waste diverted)

### 🎯 Tujuan

Menjadi ekosistem digital terlengkap untuk **digitalisasi manajemen eco-enzyme** yang membantu praktisi meningkatkan kualitas produksi, mengkomersialkan hasil fermentasi, dan memaksimalkan dampak positif terhadap lingkungan.

---

## ✨ Fitur Unggulan

### 🚀 Fitur Utama

| Fitur | Deskripsi | Status |
|-------|-----------|--------|
| **🧪 Manajemen Batch Cerdas** | Perhitungan otomatis rasio bahan (1:3:10), tracking status real-time, prediksi tanggal panen | ✅ Live |
| **📝 Pencatatan Progres Harian** | Log harian dengan dropdown tindakan & kondisi, emoji visual indicator, peringatan otomatis untuk kondisi berbahaya | ✅ Live |
| **🗺️ Roadmap Pemrosesan Interaktif** | Panduan step-by-step konversi eco-enzyme menjadi 8+ produk (cleaner, disinfectant, fertilizer, dll) dengan checklist progres | ✅ Live |
| **📊 Analisis Bisnis AI** | Rekomendasi produk berdasarkan karakteristik fermentasi, estimasi harga jual, analisis modal & profit margin | ✅ Live |
| **🤖 AI Fermentation Assistant** | Klasifikasi status fermentasi otomatis, saran tindakan korektif, health score calculation | ✅ Live |
| **👥 Komunitas & Leaderboard** | Sistem poin gamifikasi, regional rankings, kolaborasi antar praktisi | ✅ Live |

### 🔥 Fitur Tambahan

- 🌍 **Kalkulator Emisi Karbon** - Hitung CO₂ yang dihindari dari limbah organik yang diproses
- 📤 **Ekspor PDF** - Download laporan batch, roadmap progress, dan analisis bisnis
- 📸 **Upload Foto Batch** - Dokumentasi visual untuk setiap fermentation log
- 🔔 **Notifikasi & Reminder** - Push notification untuk milestone penting (hari ke-7, 30, 90)
- 📱 **Mobile-Responsive** - UI optimal untuk pencatatan di mana saja
- ☁️ **MinIO Object Storage** - Penyimpanan file aman dan scalable
- 🔐 **Firebase Authentication** - Login dengan Google/Email dengan secure token management
- 🌐 **Offline-First PWA** - Queue system untuk sync data saat offline

---

## 🖼️ Demo & Screenshot

### 🌐 Live Demo

**URL:** [https://ecoflow-demo.vercel.app](https://ecoflow-demo.vercel.app) *(Coming Soon)*

**Test Credentials:**
- Email: `demo@ecoflow.com`
- Password: `Demo2026!`

### 📸 Screenshots

#### 1. Dashboard Utama
![Dashboard](docs/screenshots/dashboard.png)
*Dashboard dengan statistik batch, progress bar fermentasi, dan quick actions*

#### 2. Roadmap Pemrosesan Interaktif
![Roadmap](docs/screenshots/roadmap.png)
*Step-by-step guide dengan checklist untuk konversi eco-enzyme menjadi produk*

#### 3. Pencatatan Progres Harian
![Daily Log](docs/screenshots/daily-log.png)
*Form input dengan emoji indicators dan timeline riwayat progres*

---

## 🛠️ Teknologi

### **Frontend Stack**

| Teknologi | Versi | Alasan Pemilihan |
|-----------|-------|------------------|
| [Next.js](https://nextjs.org/) | 15.5.22 | Framework React production-ready dengan SSR/SSG, App Router, dan optimasi performa otomatis |
| [Tailwind CSS](https://tailwindcss.com/) | 3.4+ | Utility-first CSS framework untuk rapid development dengan konsistensi desain |
| [Chakra UI](https://chakra-ui.com/) | 2.x | Component library dengan aksesibilitas tinggi dan theming system yang fleksibel |
| [TypeScript](https://www.typescriptlang.org/) | 5.x | Type safety untuk mengurangi bugs dan meningkatkan developer experience |
| [Firebase](https://firebase.google.com/) | 10.x | Authentication service dengan Google Sign-In dan secure token management |
| [Recharts](https://recharts.org/) | 2.x | Library visualisasi data untuk grafik dampak lingkungan dan analisis bisnis |
| [date-fns](https://date-fns.org/) | 2.x | Utility untuk format tanggal relatif ("2 hari yang lalu") |

### **Backend Stack**

| Teknologi | Versi | Alasan Pemilihan |
|-----------|-------|------------------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.115.0 | Modern Python framework dengan auto-generated OpenAPI docs dan async support |
| [PostgreSQL](https://www.postgresql.org/) | 15+ | RDBMS robust dengan JSONB support untuk data semi-structured |
| [SQLAlchemy](https://www.sqlalchemy.org/) | 2.x | ORM powerful dengan type hints support dan migration management |
| [Alembic](https://alembic.sqlalchemy.org/) | 1.x | Database migration tool untuk version control schema changes |
| [Pydantic](https://docs.pydantic.dev/) | 2.x | Data validation dengan Python type hints |
| [MinIO](https://min.io/) | Latest | S3-compatible object storage untuk file uploads (foto batch, exports) |
| [Redis](https://redis.io/) | 7.x | Caching dan rate limiting untuk optimasi performa API |

### **DevOps & Infrastructure**

| Teknologi | Alasan Pemilihan |
|-----------|------------------|
| [Docker](https://www.docker.com/) | Containerization untuk konsistensi environment development → production |
| [Docker Compose](https://docs.docker.com/compose/) | Orchestration multi-container (PostgreSQL, Redis, MinIO) |
| [GitHub Actions](https://github.com/features/actions) | CI/CD pipeline untuk automated testing dan deployment |
| [Vercel](https://vercel.com/) | Hosting frontend dengan edge network dan instant deployments |
| [Railway](https://railway.app/) / [Render](https://render.com/) | Hosting backend dengan PostgreSQL managed database |

---

## 🏗️ Arsitektur Sistem

### System Flow Diagram

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ HTTPS
       ▼
┌─────────────────────────────────────────┐
│         Next.js Frontend                │
│  ┌───────────────────────────────────┐  │
│  │  - App Router (React Server)      │  │
│  │  - Client Components              │  │
│  │  - Firebase Auth Context          │  │
│  │  - Chakra UI + Tailwind CSS       │  │
│  └───────────────────────────────────┘  │
└───────────────┬─────────────────────────┘
                │
                │ REST API (JSON)
                ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
│  ┌───────────────────────────────────┐  │
│  │  - API Routes (/api/v1/*)         │  │
│  │  - Firebase Token Verification    │  │
│  │  - Business Logic Services        │  │
│  │  - Pydantic Schemas (Validation)  │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼─────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐  ┌──────────────┐
│   PostgreSQL     │  │    MinIO     │
│   (Database)     │  │  (Storage)   │
│                  │  │              │
│ - Users          │  │ - Images     │
│ - Batches        │  │ - PDFs       │
│ - Daily Logs     │  │ - Exports    │
│ - Roadmaps       │  │              │
└──────────────────┘  └──────────────┘
         ▲
         │
    ┌────┴────┐
    │  Redis  │
    │ (Cache) │
    └─────────┘
```

### 📁 Struktur Folder Aplikasi

```
prd-ecoflow-ai/
│
├── 📁 frontend/                      # Next.js Frontend
│   ├── app/                          # App Router (Next.js 13+)
│   │   ├── dashboard/                # Dashboard page
│   │   │   ├── page.tsx              # Main dashboard
│   │   │   ├── batches/              # Batch management pages
│   │   │   ├── community/            # Community & leaderboard
│   │   │   ├── compare/              # Batch comparison
│   │   │   └── settings/             # User settings
│   │   ├── login/                    # Authentication pages
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Landing page
│   │
│   ├── src/                          # Source code
│   │   └── components/
│   │       └── features/             # Feature components
│   │           ├── BatchCard.tsx              # Batch display card
│   │           ├── CreateBatchModal.tsx       # Create batch form
│   │           ├── DailyLogModal.tsx          # Daily progress log form
│   │           ├── DailyProgressHistory.tsx   # Timeline history
│   │           ├── FermentationLogModal.tsx   # Fermentation log form
│   │           ├── ProductRecommendationModal.tsx
│   │           ├── BusinessAnalysisModal.tsx  # AI business analysis
│   │           ├── RoadmapModal.tsx           # Interactive roadmap
│   │           └── MilestonesPanel.tsx        # Milestone tracker
│   │
│   ├── lib/                          # Utilities & contexts
│   │   ├── api.ts                    # API client (axios)
│   │   ├── auth-context.tsx          # Firebase auth context
│   │   ├── batches-context.tsx       # Batches state management
│   │   ├── firebase.ts               # Firebase config
│   │   └── offline-queue.ts          # Offline sync queue
│   │
│   ├── public/                       # Static assets
│   ├── package.json                  # Dependencies
│   └── next.config.ts                # Next.js config
│
├── 📁 backend/                       # FastAPI Backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry point
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   └── base.py               # Database models
│   │   │       ├── User
│   │   │       ├── FermentationBatch
│   │   │       ├── FermentationLog
│   │   │       ├── BatchDailyLog          # ✨ NEW
│   │   │       ├── ProductTemplate
│   │   │       ├── ProductRecommendation
│   │   │       ├── RoadmapProgress
│   │   │       └── Community
│   │   │
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   └── base.py               # Request/response models
│   │   │
│   │   ├── routes/                   # API route handlers
│   │   │   ├── admin.py              # Admin endpoints
│   │   │   ├── impact.py             # Environmental impact
│   │   │   ├── recommendations.py    # Product recommendations
│   │   │   ├── roadmap.py            # Roadmap progress
│   │   │   └── users.py              # User management
│   │   │
│   │   ├── services/                 # Business logic
│   │   │   ├── eco_enzyme.py         # Calculation service
│   │   │   ├── fermentation_assistant.py  # AI classification
│   │   │   ├── product_recommendation.py  # ML recommendations
│   │   │   ├── business_analysis.py  # Business analytics
│   │   │   ├── environmental_impact.py
│   │   │   ├── roadmap.py
│   │   │   ├── report.py             # PDF exports
│   │   │   ├── admin.py
│   │   │   └── storage.py            # MinIO integration
│   │   │
│   │   ├── core/                     # Core configurations
│   │   │   ├── database.py           # DB connection
│   │   │   ├── auth.py               # Firebase auth verification
│   │   │   └── firebase.py           # Firebase admin SDK
│   │   │
│   │   └── api/                      # Additional API modules
│   │       ├── admin.py
│   │       ├── impact.py
│   │       ├── recommendations.py
│   │       └── sensors.py            # IoT sensor integration
│   │
│   ├── alembic/                      # Database migrations
│   │   ├── versions/                 # Migration files
│   │   │   └── 57cd71656cca_add_batch_daily_logs_table.py  # ✨ NEW
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── tests/                        # Unit & integration tests
│   ├── requirements.txt              # Python dependencies
│   └── Dockerfile                    # Docker image
│
├── 📁 docs/                          # Documentation
│   ├── screenshots/                  # App screenshots
│   ├── api/                          # API documentation
│   └── deployment/                   # Deployment guides
│
├── docker-compose.yml                # Multi-container setup
├── .env.example                      # Environment variables template
├── DAILY_PROGRESS_LOG_IMPLEMENTATION.md  # Feature docs ✨ NEW
├── QUICK_START_DAILY_LOG.md         # Quick start guide ✨ NEW
├── IMPLEMENTATION_CHECKLIST.md       # Development checklist ✨ NEW
├── CONTRIBUTING.md                   # Contribution guidelines
├── CHANGELOG.md                      # Version history
├── LICENSE                           # MIT License
└── README.md                         # This file
```

---

## 🚀 Instalasi & Setup

### Prerequisites

Pastikan sudah terinstall:

- **Node.js** 18+ dan **npm** / **yarn** / **pnpm**
- **Python** 3.10+
- **Docker** dan **Docker Compose** (untuk PostgreSQL, Redis, MinIO)
- **Git**

### 1️⃣ Clone Repository

```bash
git clone https://github.com/muhzakifp/Ecofloww-hosting.git
cd Ecofloww-hosting
```

### 2️⃣ Setup Database & Services (Docker)

```bash
# Jalankan PostgreSQL, Redis, dan MinIO dengan Docker Compose
docker-compose up -d postgres redis minio

# Verifikasi container berjalan
docker ps
```

**Akses MinIO Console:** http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

### 3️⃣ Setup Backend (FastAPI)

```bash
cd backend

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env dengan kredensial Firebase dan database

# Jalankan migrasi database
alembic upgrade head

# Jalankan backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend akan berjalan di:** http://localhost:8000

**API Docs (Swagger UI):** http://localhost:8000/docs

### 4️⃣ Setup Frontend (Next.js)

```bash
# Buka terminal baru
cd frontend

# Install dependencies
npm install
# atau
pnpm install
# atau
yarn install

# Copy environment variables
cp .env.example .env.local
# Edit .env.local dengan Firebase config

# Jalankan development server
npm run dev
```

**Frontend akan berjalan di:** http://localhost:3000

### 5️⃣ Verifikasi Setup

1. **Backend:** Buka http://localhost:8000/docs untuk melihat API documentation
2. **Frontend:** Buka http://localhost:3000 untuk melihat landing page
3. **Database:** Pastikan tabel sudah dibuat dengan `docker exec -it postgres-container psql -U postgres -d ecoflow_db -c "\dt"`

---

## 📱 Penggunaan

### Alur Pengguna

1. **Registrasi/Login**
   - Akses http://localhost:3000/login
   - Login dengan Google atau Email/Password
   - Firebase akan generate ID token

2. **Dashboard**
   - Lihat statistik: Total Batch, Batch Aktif, CO₂ Avoided
   - Quick action: "Mulai Batch Baru"

3. **Buat Batch Baru**
   - Klik "Mulai Batch Baru"
   - Isi: Nama batch, Berat sampah organik (kg)
   - Sistem auto-calculate: Air (L) & Gula (kg) dengan rasio 1:3:10
   - Submit → Batch masuk ke "Batch Aktif"

4. **Monitoring Harian** 📝 ✨ NEW
   - Klik "📝 Catat Progres Harian" pada batch aktif
   - Pilih tindakan: Buang gas, Cek kondisi, Aduk, dll
   - Pilih kondisi: Normal, Jamur Putih, Berbau Busuk, dll
   - (Opsional) Tambahkan catatan detail
   - Submit → Lihat timeline riwayat di bawah batch card

5. **Fermentation Log (Detail)**
   - Klik "Tambah Catatan Fermentasi"
   - Input: Aroma, Warna, Gas Presence, Temperatur, Upload Foto
   - AI classify status → Saran tindakan korektif

6. **Rekomendasi Produk (Hari ke-30+)**
   - Klik "Dapatkan Rekomendasi Produk"
   - AI analisis karakteristik fermentasi
   - Tampil 3 produk terbaik dengan compatibility score

7. **Roadmap Pemrosesan**
   - Klik "Lihat Roadmap Pemrosesan"
   - Pilih produk target (contoh: "Household Cleaner")
   - Follow step-by-step guide dengan checklist
   - Mark step as complete → Progress bar updates

8. **Analisis Bisnis**
   - Klik "Analisis Bisnis"
   - Input: Volume eco-enzyme (L), Target market
   - AI hitung: Estimasi harga jual, Modal, Profit margin
   - Rekomendasi strategi pemasaran

9. **Harvest & Export**
   - Hari ke-90: Status batch → "Harvested"
   - Export PDF: Laporan lengkap batch, roadmap progress
   - Lihat di "Batch Selesai"

---

## 📚 API Documentation

### Base URL

```
Development: http://localhost:8000
Production: https://api.ecoflow.app
```

### Authentication

Semua endpoint (kecuali `/health`) memerlukan **Firebase ID Token** di header:

```
Authorization: Bearer <firebase_id_token>
```

### 🔗 Endpoints

#### **Authentication & Users**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `POST` | `/api/v1/users/register` | Register new user |
| `GET` | `/api/v1/users/me` | Get current user profile |
| `PUT` | `/api/v1/users/me` | Update user profile |

#### **Batch Management**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batches` | Create new batch |
| `GET` | `/api/v1/batches` | List all user's batches |
| `GET` | `/api/v1/batches/{batch_id}` | Get batch details |
| `PUT` | `/api/v1/batches/{batch_id}` | Update batch |
| `DELETE` | `/api/v1/batches/{batch_id}` | Delete batch |

#### **Fermentation Logs**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batches/{batch_id}/logs` | Add fermentation log |
| `GET` | `/api/v1/batches/{batch_id}/logs` | Get batch logs |

#### **Daily Progress Logs** ✨ NEW

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batches/{batch_id}/daily-logs` | Create daily progress log |
| `GET` | `/api/v1/batches/{batch_id}/daily-logs` | Get daily progress history |

**Request Body (POST):**
```json
{
  "log_date": "2026-08-14T00:00:00Z",
  "action_taken": "Buka tutup botol (buang gas)",
  "condition": "Normal",
  "notes": "Gas keluar cukup banyak, tidak ada bau busuk"
}
```

**Response (GET):**
```json
{
  "status": "success",
  "data": {
    "daily_logs": [
      {
        "id": 1,
        "batch_id": 1,
        "log_date": "2026-08-14T00:00:00Z",
        "action_taken": "Buka tutup botol (buang gas)",
        "condition": "Normal",
        "notes": "Gas keluar cukup banyak",
        "created_at": "2026-08-14T10:30:00Z"
      }
    ],
    "total": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

#### **Product Recommendations**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batches/{batch_id}/recommendations` | Get AI product recommendations |
| `GET` | `/api/v1/batches/{batch_id}/recommendations` | Get saved recommendations |
| `GET` | `/api/v1/products/templates` | List all product templates |

#### **Roadmap Progress**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batches/{batch_id}/roadmap` | Create roadmap for selected product |
| `GET` | `/api/v1/batches/{batch_id}/roadmap` | Get roadmap progress |
| `PUT` | `/api/v1/roadmap/{roadmap_id}/steps/{step_index}` | Mark step as complete/incomplete |

#### **Business Analysis**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/batches/{batch_id}/business-analysis` | Generate AI business analysis |
| `GET` | `/api/v1/batches/{batch_id}/business-analysis` | Get saved analysis |

#### **Environmental Impact**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/impact/calculate` | Calculate CO₂ avoided & waste diverted |
| `GET` | `/api/v1/impact/user` | Get user's total environmental impact |
| `GET` | `/api/v1/impact/community/{community_id}` | Get community impact stats |

#### **Community & Leaderboard**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/community/leaderboard` | Get regional leaderboard |
| `GET` | `/api/v1/community/my-rank` | Get current user's rank |
| `POST` | `/api/v1/community/join/{community_id}` | Join community |

#### **File Upload**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload` | Upload image (batch photo, profile pic) |

#### **Admin Endpoints** (Role: admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/admin/users` | List all users |
| `GET` | `/api/v1/admin/stats` | Platform statistics |
| `POST` | `/api/v1/admin/products` | Create product template |
| `PUT` | `/api/v1/admin/products/{id}` | Update product template |

### 📖 Full API Documentation

Akses **Swagger UI** untuk dokumentasi interaktif lengkap:

**http://localhost:8000/docs**

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **MIT License**.

```
MIT License

Copyright (c) 2026 Bismillah Tembus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Lihat file [LICENSE](LICENSE) untuk detail lengkap.

---

<div align="center">

## 💚 Made with ❤️ by BISMILLAH TEMBUS for ITECHNO CUP 2026

**[⬆ Kembali ke Atas](#-ecoflow---smart-eco-enzyme-management-system-powered-by-ai)**

---

**Hubungi Saya:**

[![GitHub](https://img.shields.io/badge/GitHub-GomalRajaGula-181717?style=flat&logo=github)](https://github.com/GomalRajaGula)
[![Email](https://img.shields.io/badge/Email-Contact-EA4335?style=flat&logo=gmail)](mailto:achmal.maulana@example.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/achmal-maulana)

🌱 *"Mengubah sampah organik menjadi solusi berkelanjutan dengan teknologi"*

</div>
