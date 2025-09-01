# Project Plan: DashAgent

## 1. Overview
Aplikasi dashboard dan analitik hotel dengan:
- Upload multi-jenis CSV (profile tamu, reservasi, chat WhatsApp, transaksi resto, dll)
- ETL/preprocessing otomatis per jenis data
- Dashboard visualisasi (occupancy rate, revenue, segmentasi, room type, dll)
- AI chatbot multi-agent (tanya jawab data + websearch)
- Multiuser dengan login & RBAC

## 2. Arsitektur
```
Frontend (Next.js, React, Tailwind, shadcn/ui)
        ↓
Backend API (FastAPI, Python)
├── Auth/RBAC
├── Upload/ETL CSV
└── Dashboard API
        ↓
Database (PostgreSQL)

Agent Service (FastAPI terpisah)
├── Multi-agent (DB access + websearch)
├── OpenAI integration
└── RBAC guardrails
```

## 3. Struktur Folder

```
dashagent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── database.py          # DB connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── config/              # Configuration
│   │   │   ├── __init__.py
│   │   │   ├── settings.py      # Environment variables
│   │   │   └── database_config.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py          # Login, JWT
│   │   │   ├── csv.py           # Upload CSV
│   │   │   └── dashboard.py     # Data queries
│   │   ├── controllers/         # Business logic
│   │   │   ├── auth_controller.py
│   │   │   ├── csv_controller.py
│   │   │   └── dashboard_controller.py
│   │   ├── services/            # DB operations
│   │   │   ├── auth_service.py
│   │   │   ├── csv_service.py
│   │   │   └── dashboard_service.py
│   │   ├── middlewares/         # Auth middleware
│   │   │   └── auth_middleware.py
│   │   ├── dependencies/        # RBAC, validations
│   │   │   └── rbac.py
│   │   └── csv_handlers/        # ETL per jenis CSV
│   │       ├── __init__.py      # Registry pattern
│   │       ├── profile_tamu.py
│   │       ├── reservasi.py
│   │       ├── chat_whatsapp.py
│   │       └── transaksi_resto.py
│   ├── .env                     # Environment variables
│   └── requirements.txt
├── agent/                       # AI Service terpisah
│   ├── main.py                  # FastAPI entry
│   ├── agents/                  # Multi-agent
│   ├── tools/                   # DB access, websearch
│   └── requirements.txt
├── frontend/                    # Next.js (menyusul)
│   └── ...
└── PROJECT_PLAN.md
```

## 4. Step-by-Step Development

### Phase 1: Backend Core (Week 1-2)
1. **Setup environment**
   ```bash
   cd backend && python -m venv venv && venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create folder structure** (sesuai struktur di atas)

3. **Database setup**
   - `database.py`: PostgreSQL connection
   - `models.py`: Tables untuk user, csv_data, dashboard_metrics

4. **Basic FastAPI setup**
   - `main.py`: Include routers
   - `routers/auth.py`: Login endpoint (JWT)
   - `middlewares/auth_middleware.py`: JWT validation

5. **CSV upload system**
   - `routers/csv.py`: Upload endpoint
   - `csv_handlers/__init__.py`: Registry pattern
   - Handler untuk 4 jenis CSV (profile_tamu, reservasi, chat_whatsapp, transaksi_resto)

**Outcome:** Backend bisa login, upload CSV, data masuk DB

### Phase 2: Dashboard API (Week 3)
1. **Dashboard endpoints**
   - `routers/dashboard.py`: Query occupancy, revenue, segmentasi
   - `controllers/dashboard_controller.py`: Business logic
   - `services/dashboard_service.py`: SQL queries, agregasi

2. **RBAC implementation**
   - `dependencies/rbac.py`: Role-based access control
   - User roles: admin, manager, viewer

**Outcome:** API dashboard siap, data bisa diquery dengan filter tanggal

### Phase 3: Agent Service (Week 4)
1. **Separate FastAPI service**
   - `agent/main.py`: FastAPI untuk chat
   - `agent/agents/`: Multi-agent setup
   - `agent/tools/`: DB access, websearch tools

2. **OpenAI integration**
   - Chat endpoint yang bisa akses data dari backend
   - Guardrails untuk RBAC

**Outcome:** AI chatbot bisa tanya jawab data + websearch

### Phase 4: Frontend (Week 5-6)
1. **Next.js setup** dengan Tailwind + shadcn/ui
2. **Dashboard pages** dengan chart/visualisasi
3. **Upload pages** untuk CSV
4. **Chat interface** untuk AI
5. **Login/auth integration**

## 5. Tech Stack
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, JWT, pytest
- **Agent:** FastAPI, OpenAI API, LangChain (optional)
- **Frontend:** Next.js, React, Tailwind CSS, shadcn/ui, Recharts
- **Database:** PostgreSQL
- **Deploy:** Docker (optional)

---

*Project plan ini final dan tidak akan berubah kecuali ada revisi besar yang disepakati.*
