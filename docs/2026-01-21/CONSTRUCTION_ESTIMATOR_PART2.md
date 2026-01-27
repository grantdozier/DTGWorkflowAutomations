# Construction Estimator - Implementation Guide Part 2

## PHASE 6 CONTINUED: Estimation Engine

### Step 6.1: Takeoff Calculator (continued)

```python
    def _extract_number(self, text: str) -> Optional[float]:
        """
        Extract numeric value from text
        """
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            return float(numbers[0])
        return None
```

### Step 6.2: Historical Data Analyzer

**File: `backend/app/ai/bid_correlator.py`**
```python
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor
import logging

logger = logging.getLogger(__name__)

class BidCorrelator:
    """
    Use ML to correlate current bid items with historical data
    and predict man-hours
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.model = RandomForestRegressor(n_estimators=100)
    
    async def find_similar_bid_items(
        self,
        current_item: Dict,
        historical_items: List[Dict],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar bid items from historical data
        """
        if not historical_items:
            return []
        
        # Extract descriptions
        current_desc = current_item.get("description", "")
        historical_descs = [item.get("description", "") for item in historical_items]
        
        # Vectorize
        all_descs = [current_desc] + historical_descs
        vectors = self.vectorizer.fit_transform(all_descs)
        
        # Calculate similarity
        current_vector = vectors[0:1]
        historical_vectors = vectors[1:]
        
        similarities = cosine_similarity(current_vector, historical_vectors)[0]
        
        # Get top k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        similar_items = []
        for idx in top_indices:
            item = historical_items[idx].copy()
            item["similarity_score"] = float(similarities[idx])
            similar_items.append(item)
        
        return similar_items
    
    async def predict_manhours(
        self,
        current_item: Dict,
        similar_items: List[Dict]
    ) -> Dict[str, float]:
        """
        Predict man-hours based on similar historical items
        """
        if not similar_items:
            return {
                "predicted_hours": 0,
                "confidence": 0,
                "range_low": 0,
                "range_high": 0
            }
        
        # Extract features and man-hours
        quantities = []
        manhours = []
        
        for item in similar_items:
            qty = item.get("quantity", 0)
            hours = item.get("labor_hours", 0)
            
            if qty > 0 and hours > 0:
                quantities.append(qty)
                manhours.append(hours)
        
        if not quantities:
            return {
                "predicted_hours": 0,
                "confidence": 0,
                "range_low": 0,
                "range_high": 0
            }
        
        # Calculate productivity rate (hours per unit)
        rates = [h / q for h, q in zip(manhours, quantities)]
        avg_rate = np.mean(rates)
        std_rate = np.std(rates)
        
        # Predict for current item
        current_qty = current_item.get("quantity_bid", 0)
        predicted_hours = avg_rate * current_qty
        
        # Calculate confidence based on consistency of historical data
        confidence = max(0, 1 - (std_rate / avg_rate)) if avg_rate > 0 else 0
        
        # Calculate range
        range_low = (avg_rate - std_rate) * current_qty
        range_high = (avg_rate + std_rate) * current_qty
        
        return {
            "predicted_hours": float(predicted_hours),
            "confidence": float(confidence),
            "range_low": float(max(0, range_low)),
            "range_high": float(range_high),
            "avg_productivity_rate": float(avg_rate)
        }
```

### Step 6.3: Quote Management Service

**File: `backend/app/services/email_service.py`**
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class QuoteEmailService:
    """
    Handle sending quote requests to suppliers
    """
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
    
    async def send_quote_request(
        self,
        supplier_email: str,
        supplier_name: str,
        project_info: Dict,
        takeoff_data: List[Dict],
        attachments: List[str] = None
    ) -> bool:
        """
        Send standardized quote request email
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = supplier_email
            msg['Subject'] = f"Quote Request - {project_info['name']}"
            
            # Create email body
            body = self._create_quote_request_body(
                supplier_name,
                project_info,
                takeoff_data
            )
            
            msg.attach(MIMEText(body, 'html'))
            
            # Attach files if provided
            if attachments:
                for file_path in attachments:
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=file_path.split('/')[-1])
                        part['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'
                        msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Quote request sent to {supplier_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send quote request: {str(e)}")
            return False
    
    def _create_quote_request_body(
        self,
        supplier_name: str,
        project_info: Dict,
        takeoff_data: List[Dict]
    ) -> str:
        """
        Create standardized HTML email body
        """
        html = f"""
        <html>
        <body>
            <h2>Quote Request</h2>
            <p>Dear {supplier_name},</p>
            
            <p>We are requesting a quote for materials on the following project:</p>
            
            <h3>Project Information:</h3>
            <ul>
                <li><strong>Project Name:</strong> {project_info['name']}</li>
                <li><strong>Location:</strong> {project_info.get('location', 'N/A')}</li>
                <li><strong>Bid Date:</strong> {project_info.get('bid_date', 'N/A')}</li>
            </ul>
            
            <h3>Materials Required:</h3>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <th>Item</th>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>Specifications</th>
                </tr>
        """
        
        for item in takeoff_data:
            html += f"""
                <tr>
                    <td>{item.get('item_number', '')}</td>
                    <td>{item.get('description', '')}</td>
                    <td>{item.get('quantity', '')}</td>
                    <td>{item.get('unit', '')}</td>
                    <td>{item.get('specifications', '')}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <p>Please provide your quote including:</p>
            <ul>
                <li>Unit price</li>
                <li>Total price</li>
                <li>Lead time</li>
                <li>Payment terms</li>
                <li>Delivery information</li>
            </ul>
            
            <p>Thank you for your prompt attention to this request.</p>
            
            <p>Best regards,</p>
        </body>
        </html>
        """
        
        return html
```

### Step 6.4: Specification Matcher

**File: `backend/app/ai/spec_extractor.py`**
```python
from typing import List, Dict, Optional
import logging
from app.ai.config import anthropic_client
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SpecificationMatcher:
    """
    Match extracted specification codes with specification library
    """
    
    async def match_specifications(
        self,
        spec_codes: List[str],
        db: Session
    ) -> List[Dict]:
        """
        Match specification codes and retrieve full details
        """
        from app.models.specification import SpecificationLibrary
        
        matched_specs = []
        
        for code in spec_codes:
            # Clean the code
            clean_code = self._normalize_spec_code(code)
            
            # Query database
            spec = db.query(SpecificationLibrary).filter(
                SpecificationLibrary.spec_code == clean_code
            ).first()
            
            if spec:
                matched_specs.append({
                    "code": spec.spec_code,
                    "title": spec.title,
                    "description": spec.description,
                    "requirements": spec.requirements,
                    "material_grades": spec.material_grades,
                    "source": spec.source
                })
            else:
                # Use Claude to find similar specs
                similar = await self._find_similar_spec(clean_code, db)
                if similar:
                    matched_specs.append(similar)
        
        return matched_specs
    
    async def _find_similar_spec(
        self,
        spec_code: str,
        db: Session
    ) -> Optional[Dict]:
        """
        Use Claude to find similar specification if exact match not found
        """
        from app.models.specification import SpecificationLibrary
        
        # Get all specs to compare
        all_specs = db.query(SpecificationLibrary).limit(100).all()
        
        if not all_specs:
            return None
        
        spec_list = "\n".join([f"{s.spec_code}: {s.title}" for s in all_specs])
        
        prompt = f"""
        Given the specification code "{spec_code}", find the most similar specification
        from this list:
        
        {spec_list}
        
        Return ONLY the matching spec code, or "NONE" if no good match exists.
        """
        
        try:
            message = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            result = message.content[0].text.strip()
            
            if result != "NONE":
                # Get the matched spec
                matched = db.query(SpecificationLibrary).filter(
                    SpecificationLibrary.spec_code == result
                ).first()
                
                if matched:
                    return {
                        "code": matched.spec_code,
                        "title": matched.title,
                        "description": matched.description,
                        "requirements": matched.requirements,
                        "material_grades": matched.material_grades,
                        "source": matched.source,
                        "matched_from": spec_code
                    }
        
        except Exception as e:
            logger.error(f"Spec matching failed: {str(e)}")
        
        return None
    
    def _normalize_spec_code(self, code: str) -> str:
        """
        Normalize specification code format
        """
        # Remove extra spaces, convert to uppercase
        code = code.strip().upper()
        
        # Common normalizations
        code = code.replace(" ", "-")
        
        return code
```

### Step 6.5: Estimation Engine

**File: `backend/app/services/estimation_engine.py`**
```python
from typing import Dict, List
from decimal import Decimal
import logging
from sqlalchemy.orm import Session

from app.models.project import BidItem
from app.models.estimation import MaterialTakeoff, Estimate
from app.ai.bid_correlator import BidCorrelator
from app.services.takeoff_calculator import TakeoffCalculator

logger = logging.getLogger(__name__)

class EstimationEngine:
    """
    Main estimation engine that combines all components
    """
    
    def __init__(self):
        self.bid_correlator = BidCorrelator()
        self.takeoff_calculator = TakeoffCalculator()
    
    async def generate_estimate(
        self,
        project_id: str,
        db: Session,
        user_id: str
    ) -> Dict:
        """
        Generate complete project estimate
        """
        result = {
            "success": False,
            "estimate": None,
            "breakdown": {},
            "errors": []
        }
        
        try:
            # Get all bid items for project
            bid_items = db.query(BidItem).filter(
                BidItem.project_id == project_id
            ).all()
            
            if not bid_items:
                raise ValueError("No bid items found for project")
            
            # Initialize cost components
            total_materials = Decimal("0")
            total_labor = Decimal("0")
            total_equipment = Decimal("0")
            total_subs = Decimal("0")
            
            # Process each bid item
            for bid_item in bid_items:
                # Get material takeoffs
                takeoffs = db.query(MaterialTakeoff).filter(
                    MaterialTakeoff.bid_item_id == bid_item.id
                ).all()
                
                # Calculate material costs (from quotes)
                item_material_cost = await self._calculate_material_cost(
                    takeoffs, db
                )
                total_materials += item_material_cost
                
                # Predict labor hours
                labor_prediction = await self._predict_labor_cost(
                    bid_item, db
                )
                total_labor += labor_prediction["cost"]
                
                # Calculate equipment costs
                equipment_cost = await self._calculate_equipment_cost(
                    bid_item, labor_prediction["hours"], db
                )
                total_equipment += equipment_cost
            
            # Get company overhead and profit config
            from app.models.company import OverheadConfig
            overhead_config = db.query(OverheadConfig).filter(
                OverheadConfig.company_id == bid_items[0].project.company_id
            ).first()
            
            # Calculate overhead
            overhead = await self._calculate_overhead(
                overhead_config,
                total_labor + total_materials + total_equipment
            )
            
            # Calculate profit
            subtotal = total_materials + total_labor + total_equipment + total_subs + overhead
            profit = await self._calculate_profit(
                overhead_config,
                subtotal
            )
            
            # Create estimate record
            total_cost = subtotal + profit
            
            estimate = Estimate(
                project_id=project_id,
                materials_cost=total_materials,
                labor_cost=total_labor,
                equipment_cost=total_equipment,
                subcontractor_cost=total_subs,
                overhead=overhead,
                profit=profit,
                total_cost=total_cost,
                confidence_score=Decimal("0.85"),  # Calculate based on data quality
                created_by=user_id
            )
            
            db.add(estimate)
            db.commit()
            db.refresh(estimate)
            
            result["success"] = True
            result["estimate"] = estimate
            result["breakdown"] = {
                "materials": float(total_materials),
                "labor": float(total_labor),
                "equipment": float(total_equipment),
                "subcontractors": float(total_subs),
                "overhead": float(overhead),
                "profit": float(profit),
                "total": float(total_cost)
            }
            
        except Exception as e:
            logger.error(f"Estimate generation failed: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    async def _calculate_material_cost(
        self,
        takeoffs: List[MaterialTakeoff],
        db: Session
    ) -> Decimal:
        """
        Calculate total material cost from takeoffs and quotes
        """
        from app.models.estimation import Quote
        
        total = Decimal("0")
        
        for takeoff in takeoffs:
            # Get accepted quote for this takeoff
            quote = db.query(Quote).filter(
                Quote.material_takeoff_id == takeoff.id,
                Quote.status == "accepted"
            ).first()
            
            if quote:
                total += quote.total_price
        
        return total
    
    async def _predict_labor_cost(
        self,
        bid_item: BidItem,
        db: Session
    ) -> Dict:
        """
        Predict labor hours and cost
        """
        from app.models.company import LaborRate
        from app.models.project import Project
        
        # Get historical projects
        project = db.query(Project).filter(
            Project.id == bid_item.project_id
        ).first()
        
        # Find similar bid items from history
        # (simplified - would use bid_correlator here)
        
        # For now, use a simple heuristic
        estimated_hours = float(bid_item.quantity_bid or 0) * 0.5  # Example
        
        # Get average labor rate
        labor_rates = db.query(LaborRate).filter(
            LaborRate.company_id == project.company_id
        ).all()
        
        if labor_rates:
            avg_rate = sum(float(lr.hourly_rate) for lr in labor_rates) / len(labor_rates)
        else:
            avg_rate = 50.0  # Default
        
        cost = Decimal(str(estimated_hours * avg_rate))
        
        return {
            "hours": estimated_hours,
            "cost": cost
        }
    
    async def _calculate_equipment_cost(
        self,
        bid_item: BidItem,
        labor_hours: float,
        db: Session
    ) -> Decimal:
        """
        Calculate equipment costs
        """
        # Simplified - would match equipment to bid item type
        # and calculate based on hours
        return Decimal("0")
    
    async def _calculate_overhead(
        self,
        overhead_config,
        direct_costs: Decimal
    ) -> Decimal:
        """
        Calculate overhead as percentage of direct costs
        """
        if not overhead_config:
            return direct_costs * Decimal("0.15")  # Default 15%
        
        # Use configured overhead
        return direct_costs * Decimal("0.15")
    
    async def _calculate_profit(
        self,
        overhead_config,
        subtotal: Decimal
    ) -> Decimal:
        """
        Calculate profit margin
        """
        if not overhead_config:
            return subtotal * Decimal("0.10")  # Default 10%
        
        # Use configured profit margin
        margin = overhead_config.profit_margin_min or Decimal("0.10")
        return subtotal * margin
```

---

## PHASE 7: Testing & Quality Assurance (Week 9-10)

### Step 7.1: Backend Tests

**File: `backend/app/tests/test_auth.py`**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost/test_db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    Base.metadata.drop_all(bind=test_engine)

def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user(client):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "company_name": "Test Company"
        }
    )
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

### Step 7.2: Integration Tests

**File: `backend/app/tests/test_estimation_flow.py`**
```python
import pytest
from fastapi.testclient import TestClient
import tempfile
import os

def test_complete_estimation_workflow(client, auth_headers):
    """
    Test complete flow: create project -> upload plan -> generate estimate
    """
    # Create project
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "Test Highway Project",
            "job_number": "HWY-001",
            "location": "Lafayette, LA",
            "project_type": "roads"
        },
        headers=auth_headers
    )
    assert project_response.status_code == 200
    project = project_response.json()
    
    # Upload plan (mock PDF)
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b"Mock PDF content")
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, 'rb') as f:
            upload_response = client.post(
                f"/api/v1/projects/{project['id']}/plans",
                files={"file": ("test.pdf", f, "application/pdf")},
                headers=auth_headers
            )
        assert upload_response.status_code == 200
    finally:
        os.unlink(tmp_path)
    
    # Generate estimate
    estimate_response = client.post(
        f"/api/v1/estimates/generate/{project['id']}",
        headers=auth_headers
    )
    assert estimate_response.status_code == 200
    estimate = estimate_response.json()
    assert "total_cost" in estimate
```

---

## PHASE 8: Deployment (Week 11)

### Step 8.1: Docker Configuration

**File: `backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app

# Run migrations and start server
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**File: `frontend/Dockerfile`**
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Step 8.2: GitHub Actions CI/CD

**File: `.github/workflows/backend-ci.yml`**
```yaml
name: Backend CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:15-3.4
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        # Add deployment commands here
        echo "Deploy to AWS/GCP"
```

---

## FINAL DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] S3 buckets created
- [ ] API keys secured
- [ ] SSL certificates obtained

### Deployment Steps
1. Deploy database (PostgreSQL with PostGIS)
2. Deploy backend (Docker container)
3. Deploy frontend (Vercel/Netlify)
4. Configure DNS
5. Set up monitoring
6. Configure backups

### Post-Deployment
- [ ] Smoke tests
- [ ] Performance monitoring
- [ ] Error tracking (Sentry)
- [ ] User acceptance testing
- [ ] Documentation complete

---

## MAINTENANCE & SCALING

### Monitoring
- Set up DataDog/New Relic dashboards
- Configure alerts for errors
- Track API performance
- Monitor database queries

### Scaling Considerations
- Database read replicas
- Redis caching layer
- CDN for static assets
- Load balancer for backend
- Celery workers for background tasks

### Regular Maintenance
- Weekly database backups
- Monthly dependency updates
- Quarterly security audits
- AI model updates as new versions release

---

## SPECIFICATION LIBRARY SEEDING

You'll need to populate the specifications_library table with common standards:

**File: `backend/scripts/seed_specifications.py`**
```python
import json
from app.database import SessionLocal
from app.models.specification import SpecificationLibrary

def seed_specifications():
    db = SessionLocal()
    
    # ASTM Standards
    astm_specs = [
        {
            "spec_code": "ASTM-C150",
            "category": "Cement",
            "title": "Standard Specification for Portland Cement",
            "description": "This specification covers eight types of portland cement",
            "source": "ASTM"
        },
        # Add more...
    ]
    
    # AASHTO Standards
    aashto_specs = [
        {
            "spec_code": "AASHTO-M180",
            "category": "Aggregates",
            "title": "Standard Specification for Coarse Aggregate",
            "description": "Requirements for coarse aggregate for construction",
            "source": "AASHTO"
        },
        # Add more...
    ]
    
    all_specs = astm_specs + aashto_specs
    
    for spec_data in all_specs:
        spec = SpecificationLibrary(**spec_data)
        db.add(spec)
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_specifications()
```

---

## SUCCESS METRICS

Track these KPIs:
1. **Accuracy**: Plan parsing accuracy > 95%
2. **Speed**: Plan processing < 2 minutes per sheet
3. **Adoption**: User onboarding completion rate
4. **Satisfaction**: User feedback scores
5. **Reliability**: System uptime > 99.5%

---

This completes the comprehensive implementation guide. The system is designed to be built incrementally, tested thoroughly, and scaled as needed.
