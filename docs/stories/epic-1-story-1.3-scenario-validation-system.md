# Story 1.3: Scenario Validation System

**Epic**: Epic 1 - What If Scenario Foundation  
**Story ID**: 1.3
**Priority**: P2 - Medium  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Implement backend validation system to ensure scenario quality, prevent nonsensical scenarios, and validate base_story authenticity using **Gemini 2.5 Flash via FastAPI** for AI-powered validation.

## Dependencies

**Blocks**:

- Epic 3 stories (scenario discovery needs quality scenarios)

**Requires**:

- Story 1.1: Scenario Data Model & API
- Story 1.2: Scenario UI components (generate validation test cases)

## Acceptance Criteria

### Client-Side Validation (Story 1.2 Integration)

- [ ] **Scenario Title**: Required, max 100 characters
- [ ] **Character Changes**: If filled, min 10 characters required
- [ ] **Event Alterations**: If filled, min 10 characters required
- [ ] **Setting Modifications**: If filled, min 10 characters required
- [ ] **At Least One Type**: User must fill at least 1 of 3 scenario types
- [ ] **Real-time validation**: Character counters with color coding
  - Green (valid): ≥10 characters
  - Red (invalid): 1-9 characters
  - Gray (empty): 0 characters
- [ ] **Submit button state**: Disabled until all validation passes

### Backend Validation

- [ ] `ScenarioValidator` service class with validation methods
- [ ] **Server-side min length validation**: Each filled type must have ≥10 characters
- [ ] **Server-side "at least one" validation**: At least 1 scenario type must be filled
- [ ] **Gemini 2.5 Flash AI validation** via FastAPI:
  - Story authenticity check (character/event/setting exists in base story)
  - Logical consistency validation (scenario makes sense in story context)
  - Creativity score (0.0-1.0 based on novelty and interest)
  - Token budget: 2,000 tokens per validation (1,500 input + 500 output)
  - Cost: ~$0.00015 per validation (Gemini API)
- [ ] **Redis cache** for validation results (5-minute TTL):
  - Cache key: `validation:{base_story}:{hash(all_filled_types)}`
  - Reduces API costs for duplicate validation attempts
- [ ] Base story validation: exists in predefined list of popular stories (Harry Potter, Game of Thrones, LOTR, etc.)
- [ ] Profanity filter: reject scenarios containing inappropriate content
- [ ] Duplicate detection: prevent identical scenarios (same book + filled types content)
- [ ] **API Gateway Pattern**: Spring Boot → FastAPI → Gemini 2.5 Flash
- [ ] **Retry logic**: 3 attempts with exponential backoff (1s, 2s, 4s) for Gemini API failures
- [ ] Validation errors return 400 Bad Request with specific error messages
- [ ] Unit tests for all validation rules >90% coverage

## Technical Notes

**Architecture: API Gateway Pattern (Pattern B)**

```
Frontend → Spring Boot (8080) → FastAPI (8000) → Gemini 2.5 Flash API
                                        ↓
                                   Redis Cache (5-min TTL)
```

**Spring Boot ScenarioValidator Service** (Updated for Unified Modal):

```java
@Service
public class ScenarioValidator {

    private static final Set<String> SUPPORTED_BOOKS = Set.of(
        "Harry Potter", "Game of Thrones", "Lord of the Rings",
        "Star Wars", "Marvel Universe", "Percy Jackson",
        "The Hunger Games", "Twilight", "Divergent"
    );

    private static final Set<String> PROFANITY_LIST = Set.of(
        // Loaded from config file
    );

    private static final int MIN_SCENARIO_LENGTH = 10;

    @Autowired
    private WebClient fastApiClient;  // Pattern B: Spring Boot → FastAPI

    @Value("${fastapi.base-url}")
    private String fastApiUrl;  // http://ai-service:8000

    public ValidationResult validateScenario(CreateScenarioRequest request) {
        List<String> errors = new ArrayList<>();

        // 1. Basic validation (fast, no AI needed)
        if (!SUPPORTED_BOOKS.contains(request.getBookTitle())) {
            errors.add("Book '" + request.getBookTitle() +
                      "' is not currently supported. Supported: " +
                      String.join(", ", SUPPORTED_BOOKS));
        }

        // 2. Scenario title validation
        if (request.getScenarioTitle() == null || request.getScenarioTitle().trim().isEmpty()) {
            errors.add("Scenario title is required");
        } else if (request.getScenarioTitle().length() > 100) {
            errors.add("Scenario title must be 100 characters or less");
        }

        // 3. "At least one type" validation (CRITICAL)
        String charChanges = request.getCharacterChanges();
        String eventAlters = request.getEventAlterations();
        String settingMods = request.getSettingModifications();

        boolean hasCharChanges = charChanges != null && charChanges.trim().length() >= MIN_SCENARIO_LENGTH;
        boolean hasEventAlters = eventAlters != null && eventAlters.trim().length() >= MIN_SCENARIO_LENGTH;
        boolean hasSettingMods = settingMods != null && settingMods.trim().length() >= MIN_SCENARIO_LENGTH;

        if (!hasCharChanges && !hasEventAlters && !hasSettingMods) {
            errors.add("At least one scenario type must have minimum " + MIN_SCENARIO_LENGTH + " characters");
        }

        // 4. Min length validation for FILLED fields
        if (charChanges != null && !charChanges.trim().isEmpty() && charChanges.trim().length() < MIN_SCENARIO_LENGTH) {
            errors.add("Character Changes must be at least " + MIN_SCENARIO_LENGTH + " characters if provided");
        }

        if (eventAlters != null && !eventAlters.trim().isEmpty() && eventAlters.trim().length() < MIN_SCENARIO_LENGTH) {
            errors.add("Event Alterations must be at least " + MIN_SCENARIO_LENGTH + " characters if provided");
        }

        if (settingMods != null && !settingMods.trim().isEmpty() && settingMods.trim().length() < MIN_SCENARIO_LENGTH) {
            errors.add("Setting Modifications must be at least " + MIN_SCENARIO_LENGTH + " characters if provided");
        }

        // 5. Profanity check (fast)
        if (containsProfanity(request)) {
            errors.add("Scenario contains inappropriate content");
        }

        // 6. Duplicate check (fast)
        if (isDuplicate(request)) {
            errors.add("A similar scenario already exists");
        }

        // If basic validation fails, skip AI validation (save API costs)
        if (!errors.isEmpty()) {
            return ValidationResult.invalid(errors);
        }

        // 7. AI validation via FastAPI (Gemini 2.5 Flash)
        try {
            AIValidationResponse aiValidation = callFastApiValidation(request);

            if (!aiValidation.isValid()) {
                errors.addAll(aiValidation.getErrors());
            }

            return errors.isEmpty()
                ? ValidationResult.valid(aiValidation)
                : ValidationResult.invalid(errors);
        } catch (Exception e) {
            // AI validation failure - log but don't block (fallback to basic validation)
            log.error("AI validation failed: {}", e.getMessage());
            return ValidationResult.valid(); // Graceful degradation
        }
    }

    private AIValidationResponse callFastApiValidation(CreateScenarioRequest request) {
        // Pattern B: Spring Boot proxies to FastAPI (internal network)
        Map<String, String> filledTypes = new HashMap<>();

        if (request.getCharacterChanges() != null && request.getCharacterChanges().length() >= MIN_SCENARIO_LENGTH) {
            filledTypes.put("character_changes", request.getCharacterChanges());
        }

        if (request.getEventAlterations() != null && request.getEventAlterations().length() >= MIN_SCENARIO_LENGTH) {
            filledTypes.put("event_alterations", request.getEventAlterations());
        }

        if (request.getSettingModifications() != null && request.getSettingModifications().length() >= MIN_SCENARIO_LENGTH) {
            filledTypes.put("setting_modifications", request.getSettingModifications());
        }

        return fastApiClient.post()
            .uri("/api/validate-scenario")
            .bodyValue(Map.of(
                "book_title", request.getBookTitle(),
                "scenario_title", request.getScenarioTitle(),
                "filled_types", filledTypes
            ))
            .retrieve()
            .bodyToMono(AIValidationResponse.class)
            .timeout(Duration.ofSeconds(10))  // Gemini API can be slow
            .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)))  // 3 retries: 1s, 2s, 4s
            .block();
    }

    private boolean containsProfanity(CreateScenarioRequest request) {
        String allText = request.getScenarioTitle() + " " +
                        request.getCharacterChanges() + " " +
                        request.getEventAlterations() + " " +
                        request.getSettingModifications();
        return PROFANITY_LIST.stream()
            .anyMatch(word -> allText.toLowerCase().contains(word));
    }

    private boolean isDuplicate(CreateScenarioRequest request) {
        // Check for duplicate based on book + scenario content hash
        return scenarioRepository.existsByBookIdAndContentHash(
            request.getBookId(),
            generateContentHash(request)
        );
    }

    private String generateContentHash(CreateScenarioRequest request) {
        String content = request.getScenarioTitle() + "|" +
                        request.getCharacterChanges() + "|" +
                        request.getEventAlterations() + "|" +
                        request.getSettingModifications();
        return DigestUtils.md5Hex(content);
    }
}
```

**FastAPI AI Validation Endpoint** (ai-backend/app/api/validation.py):

````python
from fastapi import APIRouter, HTTPException
import google.generativeai as genai
import redis.asyncio as redis
import hashlib
import json
from tenacity import retry, stop_after_attempt, wait_exponential

router = APIRouter()

# Redis cache client (5-minute TTL)
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

# Gemini 2.5 Flash configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@router.post("/api/validate-scenario")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4)  # 1s, 2s, 4s
)
async def validate_scenario(request: dict):
    """
    AI-powered scenario validation using Gemini 2.5 Flash

    Token budget: 2,000 tokens (1,500 input + 500 output)
    Cost: ~$0.00015 per validation
    Cache: 5-minute TTL in Redis
    """
    base_story = request['base_story']
    scenario_type = request['scenario_type']
    parameters = request['parameters']

    # Generate cache key
    cache_key = f"validation:{base_story}:{scenario_type}:{_hash_params(parameters)}"

    # Check Redis cache (5-minute TTL)
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Build validation prompt for Gemini
    prompt = _build_validation_prompt(base_story, scenario_type, parameters)

    try:
        # Call Gemini 2.5 Flash API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = await model.generate_content_async(
            prompt,
            generation_config={
                'temperature': 0.2,  # Low temperature for consistent validation
                'max_output_tokens': 500,
                'top_p': 0.95
            }
        )

        # Parse Gemini response
        result = _parse_validation_response(response.text)

        # Cache result in Redis (5-minute TTL = 300 seconds)
        await redis_client.setex(cache_key, 300, json.dumps(result))

        return result

    except Exception as e:
        logger.error(f"Gemini API validation error: {e}")
        raise HTTPException(status_code=500, detail="AI validation failed")

def _build_validation_prompt(book_title: str, scenario_title: str, filled_types: dict) -> str:
    """Build Gemini validation prompt for unified modal (optimized for 1,500 input tokens)"""

    filled_content = []

    if 'character_changes' in filled_types:
        filled_content.append(f"Character Changes:\n{filled_types['character_changes']}")

    if 'event_alterations' in filled_types:
        filled_content.append(f"Event Alterations:\n{filled_types['event_alterations']}")

    if 'setting_modifications' in filled_types:
        filled_content.append(f"Setting Modifications:\n{filled_types['setting_modifications']}")

    filled_text = "\n\n".join(filled_content)

    return f"""
Validate this "What If" scenario for {book_title}:

Scenario Title: {scenario_title}

{filled_text}

Validation Tasks:
1. Are the described changes plausible within the {book_title} universe? (Yes/No)
2. If characters are mentioned, do they exist in {book_title}? (Yes/No)
3. If events are mentioned, do they exist in {book_title}? (Yes/No)
4. Are the proposed changes logically consistent with the story world? (Yes/No)
5. Creativity score (0.0-1.0): How interesting/novel is this scenario?

Respond in JSON:
{{
  "is_valid": true/false,
  "errors": ["error message if invalid"],
  "plausible_in_universe": true/false,
  "logically_consistent": true/false,
  "creativity_score": 0.0-1.0,
  "reasoning": "Brief explanation"
}}
"""

def _parse_validation_response(response_text: str) -> dict:
    """Parse Gemini JSON response"""
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        return {
            "is_valid": data.get("is_valid", True),
            "errors": data.get("errors", []),
            "creativity_score": data.get("creativity_score", 0.5),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        # Fallback to valid (graceful degradation)
        return {
            "is_valid": True,
            "errors": [],
            "creativity_score": 0.5,
            "reasoning": "AI parsing failed, using fallback"
        }

def _hash_params(parameters: dict) -> str:
    """Generate hash for cache key"""
    param_str = json.dumps(parameters, sort_keys=True)
    return hashlib.md5(param_str.encode()).hexdigest()
````

**Controller Integration** (Updated Request Model):

```java
// Request DTO
@Data
public class CreateScenarioRequest {
    @NotNull
    private String bookId;

    @NotBlank
    @Size(max = 100)
    private String scenarioTitle;

    // At least one of these must have ≥10 characters (validated in service layer)
    private String characterChanges;
    private String eventAlterations;
    private String settingModifications;

    // Derived from Book entity
    private String bookTitle;  // Populated by controller from bookId lookup
}

// Controller
@PostMapping("/scenarios")
public ResponseEntity<?> createScenario(@Valid @RequestBody CreateScenarioRequest request) {
    // Lookup book title from bookId
    Book book = bookRepository.findById(request.getBookId())
        .orElseThrow(() -> new ResourceNotFoundException("Book not found"));
    request.setBookTitle(book.getTitle());

    // Validate scenario
    ValidationResult validation = scenarioValidator.validateScenario(request);

    if (!validation.isValid()) {
        return ResponseEntity.badRequest()
            .body(Map.of("errors", validation.getErrors()));
    }

    // Create scenario
    Scenario scenario = scenarioService.createScenario(request);

    return ResponseEntity.ok(scenario);
}
```

**Cost Analysis**:

- **Token budget per validation**: ~2,000 tokens (1,500 input + 500 output)
- **Cost per validation**: ~$0.00015 (Gemini 2.5 Flash pricing)
- **Monthly cost estimate** (1,000 users, 10 scenarios each):
  - Total validations: 10,000
  - Without cache: $1.50/month
  - With 80% cache hit rate: $0.30/month
- **Cache effectiveness**: 5-minute TTL catches duplicate attempts, A/B testing variations

## QA Checklist

### Functional Testing

- [ ] Unsupported base story returns 400 with clear error message
- [ ] Profanity in scenario rejected with generic error (no profanity echo)
- [ ] Duplicate scenario prevented
- [ ] Valid scenario passes all validations
- [ ] Each scenario type validation enforced correctly
- [ ] **Gemini AI validation** returns accurate character/event existence checks
- [ ] **Creativity score** from Gemini is 0.0-1.0 range
- [ ] **Redis cache** prevents duplicate Gemini API calls (5-minute window)
- [ ] **Retry logic** recovers from transient Gemini API failures (3 attempts)
- [ ] **Graceful degradation**: If Gemini API fails after retries, basic validation still works

### Validation Rule Testing (Updated for Unified Modal)

- [ ] **Scenario title required** - Empty title rejected
- [ ] **Scenario title max length** - Titles > 100 chars rejected
- [ ] **Min 10 chars per type** - Filled types < 10 chars rejected
- [ ] **At least one type** - Scenario with all types < 10 chars rejected
- [ ] **Empty fields allowed** - Empty Character Changes accepted if other types filled
- [ ] **Combination validation** - Scenario with only Event Alterations (≥10 chars) passes
- [ ] Unsupported book rejected

### AI Creativity Score Testing

- [ ] **Gemini creativity score** is 0.0-1.0 range
- [ ] **Gemini creativity score** reflects scenario novelty (tested on 10+ sample scenarios)
- [ ] Multiple scenario types (e.g., char + event) get higher creativity scores
- [ ] Simple single-type scenarios get lower creativity scores

### Edge Cases

- [ ] Null parameters handled gracefully
- [ ] Empty JSONB parameters rejected
- [ ] Case-insensitive base story matching ("harry potter" === "Harry Potter")
- [ ] Special characters in parameters validated

### Performance

- [ ] **Basic validation** (no AI) executes < 50ms
- [ ] **AI validation** (Gemini API call) executes < 3 seconds
- [ ] **Cached AI validation** (Redis hit) executes < 100ms
- [ ] Duplicate check uses database index (< 100ms)
- [ ] Profanity filter optimized (no regex catastrophic backtracking)
- [ ] **Pattern B latency**: Frontend → Spring Boot → FastAPI → Gemini < 5 seconds total
- [ ] **Cache hit rate** > 70% during peak usage (5-minute window effective)

## Estimated Effort

8 hours
