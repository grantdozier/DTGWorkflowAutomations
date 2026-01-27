# System Architecture Analysis - Production Readiness Assessment

**Date:** January 27, 2026  
**Purpose:** Document current system state, data flow, gaps, and roadmap to production

---

## Executive Summary

The current system is a **functional demo** but requires significant work to become production-ready for Stine. The primary blocker is **incomplete material catalog data** (79 items vs. 5,000+ needed).

**Good news:** The system is **already designed for multi-tenancy (SaaS)**. All data is isolated by `company_id`.

---

## 0. Multi-Tenant Architecture (SaaS Design)

### Data Isolation Model

The system uses **company-based tenant isolation**. Each company (Stine, another lumber yard, etc.) has completely separate data.

```
┌─────────────────────────────────────────────────────────────────┐
│  MULTI-TENANT DATA MODEL                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Company A (Stine)              Company B (Other Client)        │
│  ┌─────────────────┐            ┌─────────────────┐             │
│  │ Users           │            │ Users           │             │
│  │ Projects        │            │ Projects        │             │
│  │ Materials (79)  │            │ Materials (0)   │             │
│  │ Vendors         │            │ Vendors         │             │
│  │ Quotes          │            │ Quotes          │             │
│  │ Takeoffs        │            │ Takeoffs        │             │
│  └─────────────────┘            └─────────────────┘             │
│                                                                 │
│  ════════════════════════════════════════════════════════════   │
│  COMPLETE DATA ISOLATION - No cross-company visibility          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tenant Isolation by Table

| Table | Isolation Method | Status |
|-------|------------------|--------|
| `companies` | Is the tenant root | ✅ Isolated |
| `users` | `company_id` FK | ✅ Isolated |
| `projects` | `company_id` FK | ✅ Isolated |
| `project_documents` | Via `project_id` → `company_id` | ✅ Isolated |
| `takeoff_items` | Via `project_id` → `company_id` | ✅ Isolated |
| `materials` | `company_id` FK | ✅ Isolated |
| `vendors` | `company_id` FK | ✅ Isolated |
| `estimates` | Via `project_id` → `company_id` | ✅ Isolated |
| `generated_quotes` | Via `project_id` → `company_id` | ✅ Isolated |
| `generated_quote_line_items` | Via `generated_quote_id` | ✅ Isolated |
| `historical_projects` | `company_id` FK | ✅ Isolated |
| `historical_estimates` | `company_id` FK | ✅ Isolated |
| `company_rates` | `company_id` FK | ✅ Isolated |
| `quote_requests` | Via `project_id` → `company_id` | ✅ Isolated |
| `bid_items` | **Shared reference table** | ⚠️ Global (intentional) |

### How Isolation Works

1. **User Login** → User belongs to a `company_id`
2. **API Requests** → `current_user.company_id` filters all queries
3. **Data Access** → Only company's own data is visible

```python
# Example: Projects endpoint filters by company
projects = db.query(Project).filter(
    Project.company_id == current_user.company_id
).all()
```

### What This Means for New Clients

When onboarding a new client (not Stine):
1. Create new `Company` record
2. Create `User` accounts linked to that company
3. Their `materials`, `projects`, `vendors` are completely separate
4. Stine's 79 materials are **NOT visible** to other companies
5. Each company builds their own catalog

---

## 1. Current Material Data Sources

| Source | Location | Items | Quality |
|--------|----------|-------|---------|
| **Hardcoded Seed Script** | `backend/scripts/seed_stine_materials.py` | **79 materials** | ✅ Good - from real Quote 684107 |
| **Web Scrape JSON** | `backend/stine_catalog.json` | ~750 items | ❌ Poor - mostly junk (gift cards, store locator, etc.) |
| **Database** | PostgreSQL `materials` table | **79 materials** | ✅ Current working set |

### The Problem

**79 materials is NOT enough.** A typical Stine lumber yard has **5,000-15,000 SKUs**. The current 79 materials were manually extracted from ONE quote (Quote 684107). This is a **demo shortcut**.

---

## 2. How Data Is Currently Gathered

```
┌─────────────────────────────────────────────────────────────┐
│  CURRENT FLOW (SHORTCUT)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Quote 684107 PDF ──► Manual extraction ──► seed_stine_     │
│  (1 sample quote)     (hardcoded list)      materials.py    │
│                                                             │
│                              ▼                              │
│                                                             │
│                    79 materials in DB                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

The web scraper (`scrape_stine_catalog.py`) exists but produced garbage data - it scraped navigation links, not actual products.

---

## 3. AI Parsing Pipeline

### Current Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  PLAN PARSING FLOW                                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PDF Upload ──► pdf2image ──► Claude Vision API ──► JSON        │
│                 (convert)      (extract materials)    response   │
│                                                                  │
│                              ▼                                   │
│                                                                  │
│                    TakeoffItem records                           │
│                    (37 items extracted)                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Why Only 37 Items?

The Claude prompt (`backend/app/ai/plan_parser.py` lines 93-162) is **hardcoded with specific Stine naming patterns**:

```python
# From the prompt:
"Pine #2 (2x4-8 Nominal)" for 2x4 8-foot boards
"Stud- Spruce Pine Fir (2x4-116-5/8 Nominal)" for 9-foot studs
```

**Problems:**
1. Claude only extracts what it recognizes from the prompt examples
2. A real house plan has **100-200+ line items**
3. The prompt doesn't cover all material types (electrical, plumbing, HVAC, etc.)
4. No validation that extracted items actually exist in catalog

---

## 4. Matching System

### Current Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  MATCHING FLOW                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TakeoffItem.label ──► Fuzzy Match ──► Material.description      │
│  "Pine #2 (2x4-14)"    (fuzzywuzzy)    "Pine #2 (2x4-14 Nominal)"│
│                                                                  │
│                              ▼                                   │
│                                                                  │
│              Match confidence score (0-100)                      │
│              If > 50: Apply price from catalog                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Problems:**
1. **Threshold too low (50)** - causes false matches
2. **Only 79 materials to match against** - most items won't find a match
3. **No human review** - matches are auto-applied
4. **No learning** - system doesn't improve from corrections

---

## 5. What's Missing for Production

### A. Complete Material Catalog

| Category | Current | Needed | Gap |
|----------|---------|--------|-----|
| Lumber (all sizes) | ~30 items | 200+ | 170+ |
| Hardware (Simpson, etc.) | ~10 items | 500+ | 490+ |
| Roofing | ~8 items | 100+ | 92+ |
| Siding | ~8 items | 100+ | 92+ |
| Electrical | 0 items | 500+ | 500+ |
| Plumbing | 0 items | 300+ | 300+ |
| HVAC | 0 items | 100+ | 100+ |
| Doors/Windows | 0 items | 200+ | 200+ |
| **TOTAL** | **79** | **3,000-5,000+** | **~4,900+** |

### B. Data Acquisition Options

| Method | Effort | Quality | Recommended |
|--------|--------|---------|-------------|
| **Stine provides CSV/Excel export** | Low | ✅ Best | **YES - ask them** |
| **API integration with Stine POS** | Medium | ✅ Best | Yes - if available |
| **Manual entry from price books** | Very High | ✅ Good | Last resort |
| **Web scraping** | Medium | ❌ Poor | No - already failed |

### C. AI Parsing Improvements Needed

| Issue | Current State | Production Need |
|-------|---------------|-----------------|
| Material extraction | Hardcoded patterns | Dynamic, learns from catalog |
| Quantity accuracy | Often wrong | Validate against plan math |
| Coverage | ~37 items | 100-200+ items per plan |
| Categories | Limited | All construction categories |

### D. Matching Improvements Needed

| Issue | Current State | Production Need |
|-------|---------------|-----------------|
| Catalog size | 79 items | 5,000+ items |
| Match review | Auto-apply | Human review queue |
| Unmatched items | Ignored | Flag for manual entry |
| Price updates | Static | Sync with Stine pricing |

---

## 6. Production Roadmap

### Phase 1: Get Real Data (CRITICAL - BLOCKER)

```
1. Request from Stine:
   - Complete product catalog export (CSV/Excel)
   - Fields needed: SKU, Description, Price, Unit, Category
   - Ideally with regular price update feeds

2. If no export available:
   - Get access to their POS system API
   - Or manually enter from price books (last resort)
```

### Phase 2: Improve AI Parsing

```
1. Remove hardcoded patterns from prompt
2. Use catalog as reference for Claude
3. Add validation step: "Does this item exist in catalog?"
4. Implement multi-pass extraction for complex plans
```

### Phase 3: Build Review Workflow

```
1. After parsing: Show extracted items for review
2. After matching: Show matches for approval
3. Unmatched items: Queue for manual catalog lookup
4. Learn from corrections to improve matching
```

### Phase 4: Price Sync

```
1. Regular import of Stine price updates
2. Track price history
3. Alert on significant price changes
```

---

## 7. Immediate Action Items

| Priority | Action | Owner | Status |
|----------|--------|-------|--------|
| **P0** | Contact Stine - Request complete product catalog | Business | ❌ Not Started |
| **P1** | Build CSV/Excel import tool for catalog | Dev | ❌ Not Started |
| **P2** | Remove hardcoded prompt patterns | Dev | ❌ Not Started |
| **P3** | Add match review UI | Dev | ❌ Not Started |

---

## 8. Current File Structure

### Key Backend Files

| File | Purpose |
|------|---------|
| `backend/app/ai/plan_parser.py` | Claude Vision API integration for PDF parsing |
| `backend/app/services/material_matcher.py` | Fuzzy matching takeoffs to catalog |
| `backend/app/services/quote_pdf_generator.py` | PDF quote generation |
| `backend/scripts/seed_stine_materials.py` | Hardcoded 79 materials from Quote 684107 |

### Key Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/components/projects/TakeoffsTab.tsx` | Display/edit extracted materials |
| `frontend/src/components/projects/QuotesTab.tsx` | Quote management and PDF generation |
| `frontend/src/components/projects/DocumentsTab.tsx` | Document upload and parsing |

---

## 9. Database Schema (Relevant Tables)

```sql
-- Materials catalog
materials (
  id, company_id, product_code, description, 
  category, unit_price, unit, is_active
)

-- Extracted takeoff items
takeoff_items (
  id, project_id, label, description, quantity, unit,
  category, matched_material_id, unit_price, confidence_score
)

-- Generated quotes
generated_quotes (
  id, project_id, quote_number, status,
  subtotal, tax_rate, tax_amount, total
)
```

---

## Conclusion

**The #1 blocker is getting Stine's real catalog data.** Everything else is software that can be built, but without accurate product/pricing data, the system cannot work for production use.

The current system demonstrates the workflow but is built on shortcuts that must be replaced with real data and proper validation before going live.
