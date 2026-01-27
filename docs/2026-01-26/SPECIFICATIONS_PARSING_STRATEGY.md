# Specifications Parsing Strategy

## Overview

Specifications documents require a different parsing approach than construction plans. While plans contain tables, diagrams, and structured bid items, specifications are primarily text-heavy documents with hierarchical organization.

## Differences: Plans vs. Specifications

### Construction Plans
- **Content**: Tables, diagrams, bid item lists, quantities
- **Structure**: Spatial layout, visual elements
- **Extraction Goal**: Extract structured data (item numbers, quantities, units)
- **Best Strategy**: Vision models (Claude/OpenAI) with tiling for detail
- **DPI Needs**: HIGH (300 DPI) for microscopic detail

### Specifications Documents
- **Content**: Dense text, section headers, requirements, standards
- **Structure**: Hierarchical (Division → Section → Subsection)
- **Extraction Goal**: Extract text content, maintain hierarchy, identify key requirements
- **Best Strategy**: Text extraction + LLM for structuring
- **DPI Needs**: MEDIUM (150-200 DPI) - text clarity, not visual detail

## Parsing Strategy for Specifications

### Phase 1: High-Quality Text Extraction

**Approach**: Extract all text while preserving structure

**Methods (in order of preference)**:

1. **PyPDF2/pdfplumber Text Extraction**
   - Extract native text from PDF (if digitally created)
   - Preserves formatting, headers, section numbers
   - Fast and cheap (no API calls)
   - **Best for**: Digital PDFs with selectable text

2. **Google Document AI OCR**
   - Superior OCR quality for scanned specs
   - Handles poor quality scans
   - Preserves layout structure
   - **Best for**: Scanned specification books

3. **Tesseract OCR (Fallback)**
   - Free, always available
   - Lower quality but acceptable for text
   - **Best for**: When no other options available

### Phase 2: Intelligent Structuring with LLM

**Goal**: Convert raw text into structured, searchable format

**Process**:
```
Raw Text → LLM Analysis → Structured Output
```

**LLM Prompt Structure**:
```
Analyze this construction specification document and extract:

1. **Document Structure**:
   - Division number and title
   - Section numbers and titles
   - Hierarchical organization

2. **Key Requirements**:
   - Material specifications (type, grade, standards)
   - Quality requirements
   - Installation procedures
   - Referenced standards (ASTM, AASHTO, ACI, etc.)

3. **Specification Codes**:
   - All referenced standards with context
   - Compliance requirements

4. **Materials List**:
   - Materials mentioned
   - Required properties/characteristics
   - Applicable sections

Return structured JSON format...
```

### Phase 3: Database Storage

**Schema Design**:

```sql
-- Specifications table
CREATE TABLE specifications (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    document_id UUID REFERENCES project_documents(id),
    division_number VARCHAR(10),
    division_title TEXT,
    section_number VARCHAR(20),
    section_title TEXT,
    content_text TEXT,
    parsed_data JSONB,  -- Structured extraction
    created_at TIMESTAMP DEFAULT NOW()
);

-- Specification requirements (for intelligent use)
CREATE TABLE specification_requirements (
    id UUID PRIMARY KEY,
    specification_id UUID REFERENCES specifications(id),
    requirement_type VARCHAR(50),  -- material, quality, installation, reference
    description TEXT,
    standard_code VARCHAR(100),  -- ASTM C150, AASHTO M31, etc.
    applicable_to VARCHAR(100),  -- Which bid items this applies to
    context_text TEXT,  -- Surrounding context
    created_at TIMESTAMP DEFAULT NOW()
);

-- Links specifications to bid items
CREATE TABLE bid_item_specifications (
    id UUID PRIMARY KEY,
    bid_item_id UUID REFERENCES bid_items(id),
    specification_id UUID REFERENCES specifications(id),
    requirement_id UUID REFERENCES specification_requirements(id),
    relevance_score FLOAT,  -- How relevant (0.0-1.0)
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Implementation Plan

### Step 1: Add Specifications Document Type

**File**: `backend/app/models/project.py`

```python
# Update DocumentType enum
class DocumentType(str, Enum):
    PLAN = "plan"
    SPEC = "spec"  # ALREADY EXISTS
    ADDENDUM = "addendum"
    PHOTO = "photo"
```

**Already done** - spec type exists.

### Step 2: Create Specifications Parser

**File**: `backend/app/ai/spec_parser.py` (NEW)

```python
class SpecificationParser:
    """Parse specification documents - text-focused approach"""

    async def parse_specification(self, pdf_path: Path, max_pages: int = 50):
        """
        Parse specification document

        Steps:
        1. Extract text (try native PDF text first)
        2. If no text, use OCR
        3. Send to LLM for structuring
        4. Return structured specification data
        """
        pass

    def extract_text(self, pdf_path: Path):
        """Extract text using best available method"""
        # Try PyPDF2/pdfplumber first
        # Fall back to OCR if needed
        pass

    async def structure_with_llm(self, text: str):
        """Use LLM to structure specification text"""
        # Send to Claude/GPT-4 with spec-specific prompt
        # Extract divisions, sections, requirements, standards
        pass
```

### Step 3: Add API Endpoint

**File**: `backend/app/api/v1/endpoints/ai.py`

```python
@router.post("/projects/{project_id}/documents/{document_id}/parse-spec")
async def parse_specification_document(
    project_id: str,
    document_id: str,
    max_pages: int = 50,  # Specs can be longer
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse a specification document

    Returns:
    - Division/section structure
    - Extracted requirements
    - Referenced standards
    - Material specifications
    """
    pass
```

### Step 4: Frontend Upload Separation

**File**: `frontend/src/components/projects/DocumentsTab.tsx`

**Current**: Single upload section for all documents

**Updated**: Separate sections:

```tsx
<Tabs>
  <Tab label="Construction Plans">
    {/* Upload for plans - uses vision models with tiling */}
    <PlanUploadSection />
  </Tab>

  <Tab label="Specifications">
    {/* Upload for specs - uses text extraction + LLM */}
    <SpecificationUploadSection />
  </Tab>

  <Tab label="Addenda">
    {/* Upload for addenda */}
    <AddendaUploadSection />
  </Tab>
</Tabs>
```

### Step 5: Intelligent Specification Linking

**Goal**: Automatically link specifications to relevant bid items

**Approach**:
```python
async def link_specifications_to_items(project_id: UUID):
    """
    After parsing both plans and specs, link them intelligently

    Algorithm:
    1. For each bid item, extract key terms (concrete, steel, excavation, etc.)
    2. For each specification, extract applicable materials/work types
    3. Use LLM to score relevance between items and specs
    4. Create links with relevance scores
    """
    pass
```

**Example**:
```
Bid Item: "Item 203 - Portland Cement Concrete Pavement"
↓
Linked Specifications:
- Division 32 Section 13 10: Concrete Pavement (relevance: 0.95)
- Division 03 Section 31 00: Structural Concrete (relevance: 0.80)
- Spec: ASTM C150 Portland Cement (relevance: 0.90)
```

## Prompts for Specification Parsing

### Main Structure Extraction Prompt

```
You are analyzing a construction specification document. Extract and structure the information.

The document follows CSI MasterFormat organization with divisions and sections.

Extract:

1. **Document Metadata**:
   - Division number (e.g., "Division 03")
   - Division title (e.g., "Concrete")
   - Section number (e.g., "03 31 00")
   - Section title (e.g., "Structural Concrete")

2. **Section Content**:
   - PART 1 - GENERAL (administrative, references, submittals)
   - PART 2 - PRODUCTS (materials, equipment, mixes)
   - PART 3 - EXECUTION (installation, quality control)

3. **Referenced Standards** (extract ALL):
   Format: {
     "code": "ASTM C150",
     "title": "Standard Specification for Portland Cement",
     "context": "Cement shall conform to ASTM C150 Type I or Type II"
   }

4. **Material Requirements**:
   For each material mentioned:
   - Material name
   - Required properties (strength, grade, type)
   - Applicable standards
   - Quality requirements

5. **Key Requirements**:
   - Installation procedures
   - Quality control measures
   - Testing requirements
   - Acceptance criteria

Return as structured JSON...
```

### Specification Linking Prompt

```
Given a bid item and a specification section, determine relevance.

Bid Item:
{bid_item_description}

Specification Section:
{spec_section_content}

Analyze:
1. Does this specification apply to this bid item?
2. How relevant is it (0.0 = not relevant, 1.0 = directly applicable)?
3. What specific requirements from the spec apply?

Return:
{
  "relevance_score": 0.95,
  "applies": true,
  "applicable_requirements": [
    "Concrete strength: 4000 psi minimum",
    "Air entrainment: 5-8%",
    "Cement: ASTM C150 Type II"
  ],
  "reasoning": "This spec directly governs concrete pavement construction"
}
```

## Usage in Takeoffs

Once specifications are parsed and linked:

### 1. Auto-Populate Specification References

```python
# When creating a bid item estimate
bid_item = {
    "item_number": "203",
    "description": "Portland Cement Concrete Pavement",
    "quantity": 1500,
    "unit": "SY",
    "specifications": [
        {
            "section": "32 13 10",
            "title": "Concrete Pavement",
            "key_requirements": [
                "Concrete: 4000 psi, air-entrained",
                "Cement: ASTM C150 Type II",
                "Thickness: 8 inches"
            ]
        }
    ]
}
```

### 2. Specification Compliance Checker

```python
# Check if estimate meets specification requirements
def check_compliance(bid_item, specifications):
    """
    Compare estimated materials/methods against spec requirements
    Flag any potential non-compliance
    """
    pass
```

### 3. Material Cost Lookup

```python
# Use spec requirements to get accurate material costs
spec_requirement = "Concrete: 4000 psi, Type II cement, air-entrained"
material_cost = pricing_database.lookup(spec_requirement)
```

## File Organization

```
backend/app/ai/
├── plan_parser.py              [EXISTING] Plans with vision models
├── spec_parser.py              [NEW] Specifications with text extraction
├── parsing/
│   ├── strategies/
│   │   ├── spec_text_extraction.py     [NEW] PDF text extraction
│   │   ├── spec_llm_structuring.py     [NEW] LLM structuring
│   │   └── spec_linking.py             [NEW] Link specs to items
│   └── utils/
│       └── text_extraction.py          [NEW] PyPDF2/pdfplumber utilities

backend/app/api/v1/endpoints/
├── ai.py                       [UPDATE] Add spec parsing endpoint
└── specifications.py           [NEW] Spec management endpoints

backend/app/models/
├── specification.py            [NEW] Specification models
└── bid_item_specification.py   [NEW] Linking models

frontend/src/components/projects/
├── DocumentsTab.tsx            [UPDATE] Separate plans and specs
├── SpecificationUpload.tsx     [NEW] Spec upload component
└── SpecificationViewer.tsx     [NEW] View parsed specs
```

## Benefits

1. **Accurate Takeoffs**: Know exact material requirements from specs
2. **Compliance Checking**: Ensure estimates meet specification standards
3. **Searchable Specifications**: Find requirements quickly
4. **Intelligent Linking**: Auto-associate specs with bid items
5. **Cost Accuracy**: Get correct materials for accurate pricing
6. **Bid Defensibility**: Reference exact spec sections in bids

## Next Steps

1. Create `spec_parser.py` with text extraction
2. Add specification models to database
3. Implement LLM structuring prompts
4. Add specification parsing endpoint
5. Update frontend with separate upload sections
6. Implement specification linking algorithm
7. Add specification viewer in UI

---

**Status**: Strategy Defined, Ready for Implementation
**Complexity**: Medium (simpler than plan parsing - text-focused)
**Timeline**: ~2-3 days to implement core functionality
**Dependencies**: Existing parsing infrastructure, LLM APIs
