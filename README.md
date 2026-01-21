# DTG Workflow Automations

Master workflow automations for construction, engineering, and fabrications.

## 🏗️ Project Overview

This is a construction estimation and project management platform built with:

- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React 18 + TypeScript + Vite + Material-UI
- **Storage**: Local file system for documents
- **AI**: Claude 3.5 Sonnet & GPT-4o (optional, for plan parsing)

## 📊 Database Schema

The system uses 9 core tables:

1. **companies** - Company information
2. **users** - User accounts and authentication
3. **projects** - Construction projects
4. **project_documents** - Plans, specs, and other documents
5. **company_rates** - Labor, equipment, overhead, and margin rates (JSON)
6. **bid_items** - Standard bid item library
7. **project_bid_items** - Bid items for specific projects
8. **takeoff_items** - Quantity takeoffs from plans
9. **quotes** - Vendor quotes

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Start PostgreSQL

```bash
docker-compose up -d
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 3. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## 📁 Project Structure

```
DTGWorkflowAutomations/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   ├── ai/           # AI services (plan parsing)
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   ├── types/        # TypeScript types
│   │   └── App.tsx       # Main app
│   ├── package.json
│   └── vite.config.ts
├── uploads/              # Local file storage
│   ├── plans/           # Plan PDFs
│   └── specs/           # Specification PDFs
└── docker-compose.yml    # PostgreSQL container

```

## 🔧 Configuration

### Backend Environment Variables

Edit `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dtg_workflows

# Security
SECRET_KEY=your-secret-key-here

# AI APIs (optional)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### File Storage

Documents are stored locally in the `uploads/` directory:
- Plans: `uploads/plans/`
- Specs: `uploads/specs/`

## 🛠️ Development

### Backend Development

```bash
cd backend

# Run with auto-reload
uvicorn app.main:app --reload

# Create database migrations (when models change)
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Run dev server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check
```

## 🧪 Testing

### Check Backend Health

```bash
curl http://localhost:8000/health
```

### Check Database Connection

```bash
docker exec -it dtg_postgres psql -U postgres -d dtg_workflows -c "SELECT version();"
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🗄️ Database Management

### Access PostgreSQL

```bash
docker exec -it dtg_postgres psql -U postgres -d dtg_workflows
```

### Common SQL Commands

```sql
-- List all tables
\dt

-- Describe a table
\d companies

-- View data
SELECT * FROM companies LIMIT 10;
```

## 🔐 Security Notes

- Change the `SECRET_KEY` in production
- Use strong passwords for PostgreSQL
- Add API keys to `.env` (never commit them)
- Enable HTTPS in production

## 📦 Implementation Status

- ✅ **Phase 0**: Project initialization (FastAPI, React, PostgreSQL)
- ✅ **Phase 1**: Authentication (Registration, Login, JWT tokens)
- ✅ **Phase 2**: Company Settings (Rates, Equipment, Overhead, Margins)
- ✅ **Phase 3**: Project Management (Full CRUD, filtering, bid items)
- ✅ **Phase 4**: File Upload (Plans/specs with local storage)
- ⏳ **Phase 5**: AI Integration (Claude/GPT plan parsing)
- ⏳ **Phase 6**: Estimation Engine

**See QUICKSTART.md for step-by-step instructions to run the app!**

## 🎯 Phase 1: Authentication Features

The authentication system is complete with:

- User registration with company creation
- Login with JWT token authentication
- Protected routes using bearer tokens
- Password hashing with bcrypt
- Token refresh and validation

**API Endpoints:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `GET /api/v1/auth/me` - Get current user (protected)

**Test it:**
```bash
cd backend
python test_auth.py
```

## 🏢 Phase 2: Company Settings Features

Company settings allow users to configure their business parameters:

- View and update company information
- Configure labor rates (foreman, operator, laborer, etc.)
- Set equipment rates (excavator, bulldozer, crane, etc.)
- Define overhead costs (percentage, fixed costs, insurance)
- Set profit margins (default, minimum, target)
- Flexible JSON storage for easy customization

**API Endpoints:**
- `GET /api/v1/company/me` - Get company info
- `PUT /api/v1/company/me` - Update company info
- `GET /api/v1/company/rates` - Get company rates
- `POST /api/v1/company/rates` - Create company rates
- `PUT /api/v1/company/rates` - Update company rates
- `GET /api/v1/company/rates/examples` - Get example rate structures

**Test it:**
```bash
cd backend
python test_company.py
```

## 📋 Phase 3: Project Management Features

Full CRUD operations for construction projects:

- Create new projects with job numbers
- List all projects with pagination
- Filter projects by type (state, private, federal)
- Get individual project details
- Update project information
- Delete projects
- View project documents
- Manage project bid items

**API Endpoints:**
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects` - List projects (with pagination & filters)
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `GET /api/v1/projects/{id}/documents` - List project documents
- `GET /api/v1/projects/{id}/bid-items` - List project bid items
- `POST /api/v1/projects/{id}/bid-items` - Add bid item to project

**Features:**
- Company-scoped data (users only see their own projects)
- Unique job number validation
- Type filtering (state, private, federal, etc.)
- Pagination support

**Test it:**
```bash
cd backend
python test_projects.py
```

## 📁 Phase 4: File Upload Features

Document management for construction plans and specifications:

- Upload PDF plans and specifications to projects
- Local file storage with organized directory structure
- File validation (PDF only, 50MB max)
- Download/view uploaded documents
- List documents with filtering by type
- Delete documents (removes file and database record)
- Automatic file organization by project

**API Endpoints:**
- `POST /api/v1/projects/{id}/documents` - Upload document
- `GET /api/v1/projects/{id}/documents` - List documents (filter by type)
- `GET /api/v1/projects/{id}/documents/{doc_id}` - Download document
- `DELETE /api/v1/projects/{id}/documents/{doc_id}` - Delete document

**Features:**
- PDF file validation
- File size limits (50MB)
- Organized storage: `uploads/plans/{project_id}/` and `uploads/specs/{project_id}/`
- Secure file access (company-scoped)
- Document type filtering (plan, spec)

**Test it:**
```bash
cd backend
python test_documents.py
```

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart containers
docker-compose restart
```

### Frontend Can't Reach Backend

- Ensure backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Verify proxy settings in `frontend/vite.config.ts`

## 📄 License

MIT License - See LICENSE file for details
