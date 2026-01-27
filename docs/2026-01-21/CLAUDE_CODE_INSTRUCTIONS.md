# INSTRUCTIONS FOR CLAUDE CODE

## HOW TO USE THESE FILES

You have been provided with two comprehensive implementation guides:
1. `CONSTRUCTION_ESTIMATOR_IMPLEMENTATION_GUIDE.md` - Part 1 (Phases 0-4)
2. `CONSTRUCTION_ESTIMATOR_PART2.md` - Part 2 (Phases 5-8)

## CRITICAL RULES

1. **BUILD INCREMENTALLY**: Complete ONE phase at a time. Do not move to the next phase until the current phase is fully tested and working.

2. **TEST EVERYTHING**: After each component:
   - Run the code
   - Test the functionality
   - Fix any errors
   - Commit the working code
   - Ask the user for validation before proceeding

3. **CHECKPOINTS**: Each phase has checkpoints. Stop at each checkpoint and verify:
   - All tests pass
   - Features work as expected
   - No errors in console/logs
   - Database is properly updated

## EXECUTION ORDER

### START HERE: Phase 0 - Project Initialization
1. Create directory structure
2. Initialize frontend with Vite + React + TypeScript
3. Initialize backend with FastAPI
4. Set up Docker Compose
5. Create .env file (user needs to add API keys)
6. Start containers and verify all services running
7. **CHECKPOINT**: All containers running, no errors

### Phase 1: Database & Models (Week 1)
1. Create all model files in `backend/app/models/`
2. Set up database configuration
3. Initialize Alembic
4. Create and run migrations
5. Verify tables created in PostgreSQL
6. **CHECKPOINT**: Database schema complete, all tables exist

### Phase 2: Authentication (Week 1)
1. Create security utilities
2. Create Pydantic schemas
3. Create authentication endpoints
4. Create API client in frontend
5. Build Login and Register components
6. Create protected routes
7. Test complete auth flow
8. **CHECKPOINT**: Users can register, login, and access protected routes

### Phase 3: AI Services - Plan Parser (Week 2-3)
1. Create OCR engine with multi-tier fallbacks
2. Create Claude 3.5 Sonnet vision analyzer
3. Create GPT-4 vision analyzer
4. Create main plan parser service
5. Test with sample PDF files
6. **CHECKPOINT**: Plans can be parsed and data extracted accurately

### Phase 4: Module 1 - Onboarding (Week 3-4)
1. Create equipment API endpoints
2. Create labor rates endpoints
3. Create overhead and contacts endpoints
4. Build onboarding wizard frontend
5. Build individual setup components
6. Test complete onboarding flow
7. **CHECKPOINT**: Users can complete onboarding and save company data

### Phase 5: Module 2 - Projects (Week 4-5)
1. Create file storage utility
2. Create project API endpoints
3. Create plan upload endpoint
4. Integrate plan parser as background task
5. Build project management UI
6. Build plan upload UI
7. Test file upload and parsing
8. **CHECKPOINT**: Users can create projects and upload plans

### Phase 6: Module 3 - Estimation (Week 6-8)
1. Create takeoff calculator
2. Create bid correlator (ML model)
3. Create quote management service
4. Create specification matcher
5. Create main estimation engine
6. Build estimation UI components
7. Test complete estimation workflow
8. **CHECKPOINT**: System generates estimates from uploaded plans

### Phase 7: Testing (Week 9-10)
1. Write unit tests for all services
2. Write integration tests
3. Write E2E tests
4. Run full test suite
5. Fix all failing tests
6. Achieve >80% code coverage
7. **CHECKPOINT**: All tests passing

### Phase 8: Deployment (Week 11)
1. Create Dockerfiles
2. Set up CI/CD pipeline
3. Deploy to production
4. Configure monitoring
5. Run smoke tests
6. **CHECKPOINT**: System live in production

## AI MODEL CONFIGURATION

### CRITICAL: Use Latest Vision Models

The system MUST use these specific models for maximum accuracy:

1. **Claude 3.5 Sonnet**: `claude-3-5-sonnet-20241022`
   - Use for: Comprehensive plan analysis, specification extraction
   - API: Anthropic API

2. **GPT-4o**: `gpt-4o` (latest)
   - Use for: Geometric analysis, technical drawings
   - API: OpenAI API

3. **Azure Document Intelligence**: Latest version
   - Use for: Primary OCR (most accurate)
   - Requires: Azure subscription

4. **Google Cloud Vision**: Latest version
   - Use for: Backup OCR
   - Requires: Google Cloud account

5. **Tesseract 5.0+**: Local fallback
   - Use for: When cloud services unavailable

## TESTING STRATEGY

After implementing each component:

1. **Unit Test**: Test the function in isolation
2. **Integration Test**: Test with other components
3. **Manual Test**: Test through UI/API
4. **Fix Issues**: Address any bugs found
5. **Document**: Note any quirks or limitations

## ERROR HANDLING

Always implement proper error handling:
- Try-catch blocks around AI API calls
- Graceful fallbacks when services fail
- User-friendly error messages
- Detailed logging for debugging

## WHAT THE USER NEEDS TO PROVIDE

Before starting, the user needs to set up these API keys in `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional but recommended
AZURE_FORM_RECOGNIZER_ENDPOINT=https://...
AZURE_FORM_RECOGNIZER_KEY=...
GOOGLE_CLOUD_VISION_CREDENTIALS=/path/to/credentials.json

# AWS S3 (or use MinIO for local dev)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_BUCKET_NAME=construction-plans
AWS_REGION=us-east-1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
```

## DEVELOPMENT WORKFLOW

For each phase:

1. **Read the implementation guide** for that phase
2. **Create the files** as specified
3. **Test the code** thoroughly
4. **Fix any issues** that arise
5. **Commit the working code**
6. **Ask user**: "Phase X is complete and tested. Ready to proceed to Phase Y?"
7. **Wait for confirmation** before continuing

## COMMON ISSUES & SOLUTIONS

### Issue: Database connection fails
**Solution**: Verify Docker Compose is running, check DATABASE_URL

### Issue: AI API calls fail
**Solution**: Verify API keys are correct, check rate limits

### Issue: File upload fails
**Solution**: Check S3 credentials, verify bucket exists

### Issue: Frontend can't reach backend
**Solution**: Check CORS settings, verify both servers running

### Issue: PDF parsing returns empty
**Solution**: Check OCR service, verify PDF is not scanned image

## QUALITY STANDARDS

Code must meet these standards:
- ✅ Type hints on all Python functions
- ✅ TypeScript types on all frontend code
- ✅ Error handling on all async operations
- ✅ Logging for debugging
- ✅ Comments on complex logic
- ✅ Tests for critical functions

## FINAL NOTES

This is a complex, production-ready system. Take your time:
- Don't rush through phases
- Test thoroughly at each step
- Ask questions if anything is unclear
- Prioritize code quality over speed

The user wants a working system, not a fast broken system.

---

## QUICK START COMMANDS

To begin Phase 0:

```bash
# 1. Create project directory
mkdir construction-estimator
cd construction-estimator

# 2. Follow Phase 0 instructions in the implementation guide
# 3. Start Docker containers
docker-compose up -d

# 4. Verify all services running
docker-compose ps

# 5. Check logs
docker-compose logs -f

# 6. Once verified, proceed to Phase 1
```

---

## WHEN YOU'RE READY

Say: "I've read the implementation guides. Starting Phase 0: Project Initialization..."

Then proceed step by step through Phase 0, testing each component before moving forward.

Good luck! 🚀
