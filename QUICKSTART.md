# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

### Step 1: Start PostgreSQL

```bash
docker-compose up -d
```

Verify it's running:
```bash
docker-compose ps
```

### Step 2: Start Backend

**Windows:**
```bash
cd backend
start_server.bat
```

**Mac/Linux:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend is now running at: http://localhost:8000

View API docs: http://localhost:8000/docs

### Step 3: Test Authentication

In a new terminal:

```bash
cd backend
python test_auth.py
```

This will:
1. Register a test user
2. Login and get a JWT token
3. Get current user info with the token

### Step 4: Start Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend is now running at: http://localhost:5173

## 🔑 API Endpoints

### Authentication

**Register User:**
```bash
POST http://localhost:8000/api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "yourpassword",
  "name": "Your Name",
  "company_name": "Your Company"
}
```

**Login:**
```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Get Current User:**
```bash
GET http://localhost:8000/api/v1/auth/me
Authorization: Bearer <your_token>
```

### Company Settings

**Get Company Info:**
```bash
GET http://localhost:8000/api/v1/company/me
Authorization: Bearer <your_token>
```

**Update Company Name:**
```bash
PUT http://localhost:8000/api/v1/company/me
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "name": "Updated Company Name"
}
```

**Create Company Rates:**
```bash
POST http://localhost:8000/api/v1/company/rates
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "labor_rate_json": {
    "foreman": 45.00,
    "operator": 35.00,
    "laborer": 25.00
  },
  "equipment_rate_json": {
    "excavator": 125.00,
    "bulldozer": 150.00
  },
  "overhead_json": {
    "percentage": 15.0,
    "fixed_costs": 10000.00
  },
  "margin_json": {
    "default_percentage": 10.0,
    "minimum_percentage": 5.0
  }
}
```

**Get Company Rates:**
```bash
GET http://localhost:8000/api/v1/company/rates
Authorization: Bearer <your_token>
```

**Update Company Rates:**
```bash
PUT http://localhost:8000/api/v1/company/rates
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "labor_rate_json": {
    "foreman": 50.00,
    "operator": 40.00
  }
}
```

**Get Rate Examples:**
```bash
GET http://localhost:8000/api/v1/company/rates/examples
Authorization: Bearer <your_token>
```

### Document Upload

**Upload Plan to Project:**
```bash
POST http://localhost:8000/api/v1/projects/{project_id}/documents
Authorization: Bearer <your_token>
Content-Type: multipart/form-data

file: (select PDF file)
doc_type: plan
```

**Upload Specification:**
```bash
POST http://localhost:8000/api/v1/projects/{project_id}/documents
Authorization: Bearer <your_token>
Content-Type: multipart/form-data

file: (select PDF file)
doc_type: spec
```

**List All Documents:**
```bash
GET http://localhost:8000/api/v1/projects/{project_id}/documents
Authorization: Bearer <your_token>
```

**List Only Plans:**
```bash
GET http://localhost:8000/api/v1/projects/{project_id}/documents?doc_type=plan
Authorization: Bearer <your_token>
```

**Download Document:**
```bash
GET http://localhost:8000/api/v1/projects/{project_id}/documents/{document_id}
Authorization: Bearer <your_token>
```

**Delete Document:**
```bash
DELETE http://localhost:8000/api/v1/projects/{project_id}/documents/{document_id}
Authorization: Bearer <your_token>
```

### AI Plan Parsing

**Check AI Service Status:**
```bash
GET http://localhost:8000/api/v1/ai/status
Authorization: Bearer <your_token>
```

**Parse Plan Document:**
```bash
POST http://localhost:8000/api/v1/ai/projects/{project_id}/documents/{document_id}/parse?max_pages=5
Authorization: Bearer <your_token>
```

**Parse and Save to Database:**
```bash
POST http://localhost:8000/api/v1/ai/projects/{project_id}/documents/{document_id}/parse-and-save?max_pages=5
Authorization: Bearer <your_token>
```

**Setup (Add to `.env` file):**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## 🧪 Testing with cURL

**Register:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "name": "Test User",
    "company_name": "Test Co"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"
```

**Get User (replace TOKEN):**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

**Upload Document (replace TOKEN and PROJECT_ID):**
```bash
curl -X POST http://localhost:8000/api/v1/projects/PROJECT_ID/documents \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@/path/to/plan.pdf" \
  -F "doc_type=plan"
```

## 📊 Database Access

```bash
docker exec -it dtg_postgres psql -U postgres -d dtg_workflows
```

Useful commands:
```sql
-- List tables
\dt

-- See users
SELECT * FROM users;

-- See companies
SELECT * FROM companies;

-- Exit
\q
```

## 🛠️ Troubleshooting

### Database Won't Start
```bash
docker-compose down
docker-compose up -d
docker-compose logs postgres
```

### Backend Won't Start
- Check Python version: `python --version` (need 3.11+)
- Check if port 8000 is free
- Check database connection in `.env`

### Frontend Won't Start
- Check Node version: `node --version` (need 18+)
- Clear cache: `rm -rf node_modules && npm install`
- Check if port 5173 is free

## 📝 Next Steps

Phase 1 (Authentication) is complete! Next phases:

1. **Phase 2**: Project management CRUD
2. **Phase 3**: File upload for plans/specs
3. **Phase 4**: AI integration for plan parsing
4. **Phase 5**: Estimation engine

See the full implementation guides in:
- `CONSTRUCTION_ESTIMATOR_COMPLETE_GUIDE.md`
- `CONSTRUCTION_ESTIMATOR_PART2.md`
