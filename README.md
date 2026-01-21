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

## 📦 Next Steps

1. **Authentication**: Implement user registration and login
2. **Project Management**: Build CRUD for projects
3. **File Upload**: Add document upload endpoints
4. **AI Integration**: Connect Claude/GPT for plan parsing
5. **Estimation**: Build the estimation engine

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
