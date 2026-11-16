# Guardwell — AI-Powered Home Protection & Service Logistics Platform (Backend)

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-Multimodal_AI-8E75B2.svg?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![JWT](https://img.shields.io/badge/JWT-Secure_Auth-black.svg?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20Layered-success.svg)](#architecture--design-patterns)

A production-grade, asynchronous enterprise backend powering **Guardwell** — a home protection and exterior renovation services platform. The system features AI-driven multimodal image redesign (Google Gemini), high-throughput service ticket dispatching, viral referral growth loops with dynamic coupons, community feed with moderation pipelines, and an executive administration engine built using **Clean Layered Architecture (Controller-Service-Repository Pattern)**.


## 🏗️ Architecture & Design Patterns

The project strictly follows **Clean Architecture** and **Domain-Driven Design (DDD)** principles to guarantee complete decoupling of transport, business logic, persistence, and external third-party SDKs:

```
Guardwell/
├── app/
│   ├── api/                     # Presentation Layer (FastAPI Routers, Dependency Injection)
│   │   ├── deps.py              # RBAC & Token Auth Injectors (get_current_user, get_current_admin)
│   │   └── v1/endpoints/        # Versioned Modular API Endpoints
│   ├── core/                    # Cross-Cutting Infrastructure
│   │   ├── config.py            # 12-Factor App Pydantic BaseSettings (Single Source of Truth)
│   │   ├── database.py          # SQLAlchemy 2.0 Engine, Scoped SessionLocal, Declarative Base
│   │   ├── security.py          # Salted Bcrypt, RFC 7519 JWT Encoding/Decoding, Secrets OTP
│   │   ├── exceptions.py        # Centralized Domain Exceptions & HTTP Factories
│   │   ├── response.py          # Unified DRF-style Standard Envelope Middleware
│   │   └── admin.py             # SQLAdmin Dashboard & Authentication Backend
│   ├── models/                  # Domain Persistence Entities (SQLAlchemy ORM with Declarative Mixins)
│   ├── repositories/            # Data Access Layer (Repository Pattern isolating raw ORM queries)
│   ├── schemas/                 # Data Transfer Objects & Validation (Pydantic v2 Models)
│   └── services/                # Business Logic Layer (Transaction Orchestration & Third-Party APIs)
├── uploads/                     # Sanitized Multipart Media Storage (Isolated Async Buffering)
├── docs/                        # Architecture & Cryptography Deep Dives
└── Guardwell_Postman_Collection.json # Production-Ready Postman Test Suite
```

### Core Design Patterns Applied:
* **Repository Pattern:** Abstract data operations (`BaseRepository[T]`) decouple business workflows from SQLAlchemy ORM operations, preventing N+1 query leaks using eager loading (`joinedload`).
* **Service Layer Pattern:** Encapsulates business rules, external API orchestrations, and multi-entity transaction integrity away from API routers.
* **Dependency Injection (IoC):** Scoped database sessions (`SessionLocal`) and authenticated user principals are injected per request lifecycle via FastAPI `Depends()`.
* **Standard Response Envelope (Middleware):** Custom ASGI interceptor transforms all responses and validation exceptions into standardized `{ success, statusCode, message, data, timestamp }` schemas matching enterprise frontends.
* **Fail-Fast & Security by Default:** Multi-stage OTP verification avoids unverified entity creation in persistent tables. All sensitive credentials and tokens are loaded strictly via environment boundaries.

---

## 🚀 Key Functional Modules

### 1. 🤖 Multimodal AI Room & Exterior Redesign (`/ask_ai/`)
* Integrates Google's state-of-the-art **Gemini Vision/Image API (`google-genai`)** with native `responseModalities: ["TEXT", "IMAGE"]`.
* Accepts user room/exterior photos (kitchen, bathroom, fascia, roofing) along with styling preferences (color change, modern fixtures, materials).
* Generates realistic redesigned architectural visuals while maintaining spatial boundaries, perspective, and lighting, paired with contextual design/item recommendations.

### 2. 🔐 Dual-Stage Auth & Enterprise RBAC (`/api/v1/auth`)
* **Two-Step Registration:** Registration payloads are validated and cryptographically buffered with 6-digit numeric OTPs generated via `secrets`. Database records are only committed upon verification.
* **Role-Based Access Control (RBAC):** Token-scoped validation separating `customer` and `admin` privileges with granular authorization gates.
* **Token Rotation:** Independent short/long-lived RFC 7519 JWT Access tokens paired with Refresh token renewal endpoints (`/api/v1/auth/token/refresh/`).

### 3. 🎫 Service Request Logistics & Dispatching (`/api/v1/quotes`)
* Multi-part form handling for quotes, emergency repairs, and inspections across 9 property categories (`gutter_replacement`, `soffit`, `fascia`, `roofing`, etc.).
* Asynchronous media pipeline buffering high-resolution house photos and inspection videos without blocking API workers.
* Dynamic observer alerts notifying team dispatch recipients on new ticket creations.

### 4. 👥 Customer & Operations Admin Portal (`/api/v1/admin`)
* Real-time metrics computing operational health, active/urgent ticket counts, weekly booking distributions, and customer activity logs.
* Full-lifecycle ticket triage (assignment of field representatives, progression from `submitted` → `in_progress` → `completed`).
* Direct customer management (KYC verification badges, social feed restriction controls).

### 5. 🎁 Viral Referral Engine & Dynamic Coupon Configuration
* Generation of unique user referral codes upon registration.
* Multi-state bonus tracking (`signed_up` → `booked` → `completed`), providing audit trails for payout statuses (`pending` vs `paid`).
* Real-time administrative adjustment of global promotional referral incentives without requiring backend redeployment or downtime.

### 6. 💬 Social Community Feed & Moderation (`/api/v1/feed`)
* Instant community post publishing supporting photo and video uploads.
* Threaded commenting engine with atomic single-heart reaction toggling (`CommentReaction`).
* Crowd-sourced report generation (`PostReport`) feeding administrative content-review queues for one-click post removal or dismissal.

---

## 🛠️ Tech Stack

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.14+ | Modern async runtime with strict typing & structural pattern matching |
| **Framework** | FastAPI 0.162+ | Asynchronous web framework with automatic OpenAPI 3.1 documentation |
| **Database & ORM** | SQLAlchemy 2.0 & SQLite | Advanced declarative ORM configured for SQLite with instant Postgres compatibility |
| **Data Validation** | Pydantic v2 | High-performance C-based schema validation and serialization |
| **Generative AI** | Google Gemini SDK (`google-genai`) | Multimodal image-to-image synthesis and contextual interior design styling |
| **Security & Auth** | PyJWT & Native Bcrypt | Salted password cryptography and JWT token management |
| **File Buffering** | AIOFiles & Python-Multipart | Asynchronous, non-blocking chunked multipart file storage |
| **Admin Interface** | SQLAdmin & Custom REST API | Declarative admin engine + customized executive endpoints |
| **Server** | Uvicorn & ASGI | Production ASGI server with multi-worker support |

---

## ⚡ Quick Start & Local Setup

### 1. Clone & Environment Initialization
```bash
git clone https://github.com/Tasin44/Guardwell-Service_Providing_Platform.git
cd Guardwell-Service_Providing_Platform

# Create and activate virtual environment
python -m venv venv

# Windows (Command Prompt)
venv\Scripts\activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
# Or install directly
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-multipart aiofiles pyjwt bcrypt google-genai sqladmin
```

### 3. Environment Variables Configuration
Create a `.env` file in the root directory:
```env
# Base Configuration
PROJECT_NAME="Guardwell API"
ENVIRONMENT="development"
DEBUG=True
BASE_URL="http://127.0.0.1:8000"

# Security & JWT Tokens
SECRET_KEY="your-secure-jwt-secret-key-min-32-chars"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=43200
REFRESH_TOKEN_EXPIRE_DAYS=7
OTP_EXPIRE_MINUTES=10

# Database
DATABASE_URL="sqlite:///./guardwell.db"

# Initial Superuser Seed Credentials
FIRST_SUPERUSER_EMAIL="admin@guardwell.com"
FIRST_SUPERUSER_PASSWORD="AdminSecretPassword123!"

# Google Gemini AI Configuration
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_IMAGE_MODEL="gemini-2.5-flash-image"
```

### 4. Run Application Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
On startup, the system automatically initializes database schemas and seeds default administrative principals and notification dispatchers.

---

## 📖 API Documentation & Postman

* **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Specification:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **SQLAdmin Dashboard:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

A fully configured Postman collection is included in the root directory:
* [`Guardwell_Postman_Collection.json`](./Guardwell_Postman_Collection.json) (Includes pre-configured authentication headers, dynamic tokens, multipart uploads, and test scripts across all 8 modules).

---

## 🔒 Security Architecture Highlights

* **Input Sanitization & UUID Masking:** File uploads are scanned for MIME type conformity, assigned cryptographic UUID filenames, and stored outside executable server paths.
* **Anti-User Enumeration:** Forgot-password workflows return identical generic messages regardless of whether the email exists in the database.
* **Idempotent Community Reporting:** Enforced unique constraints preventing duplicate spam reports on posts and comments.
* **Token Invalidation Boundaries:** Refresh tokens require explicit claim types (`type: "refresh"`) and cannot be used to authenticate standard REST endpoints.

---

## 📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

