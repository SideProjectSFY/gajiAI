# Testing Strategy - Gaji Interactive Fiction Platform

**Version**: 1.0  
**Last Updated**: 2025-11-13  
**Project**: Gaji  
**Test Pyramid**: 70% Unit | 20% Integration | 10% E2E

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Pyramid](#test-pyramid)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [CI/CD Integration](#cicd-integration)
9. [Test Data Management](#test-data-management)
10. [Quality Gates](#quality-gates)

---

## Testing Philosophy

### Core Principles

1. **Test What Matters**: Focus on business logic, critical paths, and user-facing features
2. **Fast Feedback**: Unit tests run in < 10s, full suite in < 5 minutes
3. **Reliable Tests**: No flaky tests - deterministic, isolated, repeatable
4. **Maintainable Tests**: Clear names, minimal duplication, easy to debug
5. **Shift Left**: Catch bugs early through comprehensive unit testing

### Testing Goals

- **Code Coverage**: Minimum 80% for backend, 70% for frontend
- **Bug Detection**: 90%+ of bugs caught before production
- **Test Execution Speed**: < 5 minutes for full suite
- **Flakiness**: < 1% flaky test rate
- **Regression Prevention**: All bugs get regression tests

---

## Test Pyramid

```
         ╱───────────╲
        ╱   E2E (10%) ╲     ← 10-15 critical user journeys
       ╱───────────────╲       Playwright, slow, expensive
      ╱                 ╲
     ╱  Integration (20%)╲    ← 50-80 integration tests
    ╱─────────────────────╲      Testcontainers, medium speed
   ╱                       ╲
  ╱    Unit Tests (70%)     ╲  ← 200+ unit tests
 ╱───────────────────────────╲    JUnit, Jest, fast
```

### Pyramid Breakdown

| Level       | Percentage | Count Est. | Tools                          | Speed            | Scope            |
| ----------- | ---------- | ---------- | ------------------------------ | ---------------- | ---------------- |
| E2E         | 10%        | 10-15      | Playwright                     | Slow (2-3 min)   | Full stack       |
| Integration | 20%        | 50-80      | JUnit + Testcontainers, Vitest | Medium (1-2 min) | Multi-component  |
| Unit        | 70%        | 200+       | JUnit, Jest/Vitest             | Fast (< 30s)     | Single component |

---

## Unit Testing

### Backend (Java / Spring Boot)

**Framework**: JUnit 5 + Mockito + AssertJ

**Test Structure**:

```java
@ExtendWith(MockitoExtension.class)
class ScenarioServiceTest {

    @Mock
    private ScenarioRepository scenarioRepository;

    @Mock
    private BaseScenarioRepository baseScenarioRepository;

    @InjectMocks
    private ScenarioService scenarioService;

    @Test
    @DisplayName("Should create scenario with valid parameters")
    void shouldCreateScenarioWithValidParameters() {
        // Given
        BaseScenario baseScenario = new BaseScenario(/* ... */);
        when(baseScenarioRepository.findById(any())).thenReturn(Optional.of(baseScenario));
        when(scenarioRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));

        CreateScenarioRequest request = CreateScenarioRequest.builder()
            .baseScenarioId(baseScenario.getId())
            .scenarioType(ScenarioType.CHARACTER_CHANGE)
            .customParameters(Map.of(
                "character", "Hermione Granger",
                "property", "house",
                "newValue", "Slytherin"
            ))
            .build();

        // When
        Scenario result = scenarioService.createScenario(request, "user-id");

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getScenarioType()).isEqualTo(ScenarioType.CHARACTER_CHANGE);
        assertThat(result.getCustomParameters().get("character")).isEqualTo("Hermione Granger");
        verify(scenarioRepository, times(1)).save(any(Scenario.class));
    }

    @Test
    @DisplayName("Should throw exception when base scenario not found")
    void shouldThrowExceptionWhenBaseScenarioNotFound() {
        // Given
        when(baseScenarioRepository.findById(any())).thenReturn(Optional.empty());

        CreateScenarioRequest request = CreateScenarioRequest.builder()
            .baseScenarioId(UUID.randomUUID())
            .scenarioType(ScenarioType.CHARACTER_CHANGE)
            .build();

        // When & Then
        assertThatThrownBy(() -> scenarioService.createScenario(request, "user-id"))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("Base scenario not found");
    }
}
```

**What to Test**:

- ✅ Service layer business logic
- ✅ DTO validations
- ✅ Exception handling
- ✅ JSONB parameter serialization/deserialization
- ✅ Edge cases (null, empty, boundary values)
- ❌ Database queries (integration tests)
- ❌ HTTP endpoints (integration tests)

**Coverage Target**: 85% line coverage

**Naming Convention**:

- Class: `{ClassName}Test`
- Method: `should{ExpectedBehavior}When{Condition}` or `given{Condition}_when{Action}_then{Result}`

---

### Frontend (Vue.js / TypeScript)

**Framework**: Vitest + Vue Test Utils + Testing Library

**Test Structure**:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createTestingPinia } from "@pinia/testing";
import ScenarioCard from "@/components/ScenarioCard.vue";
import type { Scenario } from "@/types";

describe("ScenarioCard.vue", () => {
  const mockScenario: Scenario = {
    id: "uuid-123",
    baseStory: "harry_potter",
    scenarioType: "CHARACTER_CHANGE",
    title: "Hermione in Slytherin",
    forkCount: 12,
    conversationCount: 45,
    creator: {
      id: "user-1",
      username: "hermione_fan",
      avatarUrl: "https://example.com/avatar.jpg",
    },
    createdAt: "2025-11-13T10:00:00Z",
  };

  it("renders scenario details correctly", () => {
    const wrapper = mount(ScenarioCard, {
      props: { scenario: mockScenario },
      global: {
        plugins: [createTestingPinia()],
      },
    });

    expect(wrapper.text()).toContain("Hermione in Slytherin");
    expect(wrapper.text()).toContain("12 forks");
    expect(wrapper.text()).toContain("45 convos");
    expect(wrapper.text()).toContain("@hermione_fan");
  });

  it("emits click event when card is clicked", async () => {
    const wrapper = mount(ScenarioCard, {
      props: { scenario: mockScenario },
    });

    await wrapper.find(".scenario-card").trigger("click");

    expect(wrapper.emitted("click")).toBeTruthy();
    expect(wrapper.emitted("click")![0]).toEqual([mockScenario]);
  });

  it("shows like button when user is authenticated", () => {
    const wrapper = mount(ScenarioCard, {
      props: { scenario: mockScenario },
      global: {
        plugins: [
          createTestingPinia({
            initialState: {
              auth: { isAuthenticated: true },
            },
          }),
        ],
      },
    });

    expect(wrapper.find('[data-testid="like-button"]').exists()).toBe(true);
  });

  it("does not show like button when user is not authenticated", () => {
    const wrapper = mount(ScenarioCard, {
      props: { scenario: mockScenario },
      global: {
        plugins: [
          createTestingPinia({
            initialState: {
              auth: { isAuthenticated: false },
            },
          }),
        ],
      },
    });

    expect(wrapper.find('[data-testid="like-button"]').exists()).toBe(false);
  });
});
```

**What to Test**:

- ✅ Component rendering with props
- ✅ User interactions (clicks, inputs)
- ✅ Conditional rendering
- ✅ Event emissions
- ✅ Composable logic
- ✅ Pinia store actions/getters
- ❌ API calls (integration tests)
- ❌ Router navigation (E2E tests)

**Coverage Target**: 75% line coverage

**Naming Convention**:

- File: `{ComponentName}.spec.ts` or `{composableName}.spec.ts`
- Describe block: Component/module name
- Test: Descriptive sentence starting with lowercase

---

## Integration Testing

### Backend Integration Tests

**Framework**: JUnit 5 + Testcontainers + RestAssured

**Database Setup** (Testcontainers):

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class ScenarioApiIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withDatabaseName("gaji_test")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ScenarioRepository scenarioRepository;

    private String authToken;

    @BeforeEach
    void setUp() {
        scenarioRepository.deleteAll();
        authToken = authenticateTestUser();
    }

    @Test
    @DisplayName("POST /api/v1/scenarios - Should create scenario and return 201")
    void shouldCreateScenario() {
        // Given
        CreateScenarioRequest request = CreateScenarioRequest.builder()
            .baseScenarioId(UUID.fromString("base-uuid"))
            .scenarioType("CHARACTER_CHANGE")
            .title("Hermione in Slytherin")
            .customParameters(Map.of(
                "character", "Hermione Granger",
                "property", "house",
                "newValue", "Slytherin"
            ))
            .build();

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(authToken);
        HttpEntity<CreateScenarioRequest> entity = new HttpEntity<>(request, headers);

        // When
        ResponseEntity<ScenarioResponse> response = restTemplate.postForEntity(
            "/api/v1/scenarios",
            entity,
            ScenarioResponse.class
        );

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getTitle()).isEqualTo("Hermione in Slytherin");

        // Verify database persistence
        List<Scenario> scenarios = scenarioRepository.findAll();
        assertThat(scenarios).hasSize(1);
        assertThat(scenarios.get(0).getTitle()).isEqualTo("Hermione in Slytherin");
    }

    @Test
    @DisplayName("GET /api/v1/scenarios/{id} - Should return 404 when scenario not found")
    void shouldReturn404WhenScenarioNotFound() {
        // When
        ResponseEntity<String> response = restTemplate.getForEntity(
            "/api/v1/scenarios/" + UUID.randomUUID(),
            String.class
        );

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test
    @DisplayName("POST /api/v1/scenarios - Should return 401 when not authenticated")
    void shouldReturn401WhenNotAuthenticated() {
        // Given
        CreateScenarioRequest request = CreateScenarioRequest.builder()
            .baseScenarioId(UUID.fromString("base-uuid"))
            .scenarioType("CHARACTER_CHANGE")
            .build();

        // When
        ResponseEntity<String> response = restTemplate.postForEntity(
            "/api/v1/scenarios",
            request,
            String.class
        );

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }
}
```

**What to Test**:

- ✅ Full HTTP request/response cycle
- ✅ Database persistence
- ✅ Authentication/authorization
- ✅ Validation errors
- ✅ Database triggers (CASCADE DELETE, counter increments)
- ✅ Transaction rollback on errors
- ✅ JSONB column operations
- ❌ Individual service methods (unit tests)

**Coverage Target**: 80% of API endpoints

---

### Frontend Integration Tests

**Framework**: Vitest + MSW (Mock Service Worker)

**API Mocking**:

```typescript
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { mount } from "@vue/test-utils";
import ScenarioList from "@/components/ScenarioList.vue";

const scenarios = [
  {
    id: "uuid-1",
    title: "Hermione in Slytherin",
    forkCount: 12,
    conversationCount: 45,
    // ...
  },
  {
    id: "uuid-2",
    title: "Draco Redeemed",
    forkCount: 8,
    conversationCount: 23,
    // ...
  },
];

const server = setupServer(
  http.get("/api/v1/scenarios", () => {
    return HttpResponse.json({
      content: scenarios,
      page: {
        number: 0,
        size: 20,
        totalElements: 2,
        totalPages: 1,
      },
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("ScenarioList.vue Integration", () => {
  it("fetches and displays scenarios from API", async () => {
    const wrapper = mount(ScenarioList, {
      global: {
        plugins: [createTestingPinia()],
      },
    });

    // Wait for API call to complete
    await flushPromises();

    expect(wrapper.findAll('[data-testid="scenario-card"]')).toHaveLength(2);
    expect(wrapper.text()).toContain("Hermione in Slytherin");
    expect(wrapper.text()).toContain("Draco Redeemed");
  });

  it("displays error message when API fails", async () => {
    server.use(
      http.get("/api/v1/scenarios", () => {
        return HttpResponse.json(
          { error: "Internal Server Error" },
          { status: 500 }
        );
      })
    );

    const wrapper = mount(ScenarioList);
    await flushPromises();

    expect(wrapper.find('[data-testid="error-message"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Failed to load scenarios");
  });
});
```

**What to Test**:

- ✅ API integration (mocked with MSW)
- ✅ Loading states
- ✅ Error handling
- ✅ Data flow between components
- ✅ Pinia store integration
- ❌ Actual API calls (E2E tests)

---

## End-to-End Testing

### Framework: Playwright

**Configuration** (`playwright.config.ts`):

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "Mobile Safari",
      use: { ...devices["iPhone 13"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
```

### Critical User Journeys (10-15 tests)

#### Journey 1: User Registration and Login

```typescript
import { test, expect } from "@playwright/test";

test.describe("User Authentication", () => {
  test("should register new user and login", async ({ page }) => {
    // Navigate to homepage
    await page.goto("/");

    // Click Sign Up
    await page.click('[data-testid="signup-button"]');

    // Fill registration form
    await page.fill('[name="email"]', "test@example.com");
    await page.fill('[name="username"]', "testuser123");
    await page.fill('[name="password"]', "SecurePass123!");

    // Submit
    await page.click('[data-testid="submit-signup"]');

    // Verify redirect to homepage with authenticated state
    await expect(page).toHaveURL("/");
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-menu"]')).toContainText(
      "testuser123"
    );
  });

  test("should show validation errors for invalid registration", async ({
    page,
  }) => {
    await page.goto("/");
    await page.click('[data-testid="signup-button"]');

    // Submit with invalid email
    await page.fill('[name="email"]', "not-an-email");
    await page.fill('[name="username"]', "ab"); // Too short
    await page.fill('[name="password"]', "123"); // Too weak
    await page.click('[data-testid="submit-signup"]');

    // Verify error messages
    await expect(page.locator("text=Please enter a valid email")).toBeVisible();
    await expect(
      page.locator("text=Username must be at least 3 characters")
    ).toBeVisible();
    await expect(
      page.locator("text=Password must be at least 8 characters")
    ).toBeVisible();
  });
});
```

#### Journey 2: Create Scenario End-to-End

```typescript
test.describe("Scenario Creation", () => {
  test.beforeEach(async ({ page }) => {
    // Login helper
    await loginAsTestUser(page);
  });

  test("should create scenario through wizard", async ({ page }) => {
    // Navigate to create scenario
    await page.click('[data-testid="create-scenario-button"]');

    // Step 1: Select novel
    await page.fill('[data-testid="novel-search"]', "Harry Potter");
    await page.click("text=Harry Potter and the Philosopher's Stone");
    await page.click("text=Next");

    // Step 2: Choose scenario type
    await page.click('[data-testid="scenario-type-character-change"]');
    await page.click("text=Next");

    // Step 3: Fill parameters
    await page.fill('[name="character"]', "Hermione Granger");
    await page.selectOption('[name="property"]', "house");
    await page.fill('[name="originalValue"]', "Gryffindor");
    await page.fill('[name="newValue"]', "Slytherin");
    await page.fill('[name="reasoning"]', "Exploring her ambition and cunning");
    await page.click("text=Next");

    // Step 4: Preview and publish
    await expect(page.locator("text=Hermione Granger")).toBeVisible();
    await expect(page.locator("text=Slytherin")).toBeVisible();
    await page.click('[data-testid="publish-scenario"]');

    // Verify redirect to scenario detail page
    await expect(page).toHaveURL(/\/scenarios\/[a-f0-9-]+/);
    await expect(page.locator("h1")).toContainText("Hermione");
    await expect(page.locator("text=Slytherin")).toBeVisible();
  });
});
```

#### Journey 3: Fork Conversation and Send Message

```typescript
test.describe("Conversation Forking and Messaging", () => {
  test("should fork conversation and send message", async ({ page }) => {
    await loginAsTestUser(page);

    // Navigate to an existing conversation
    await page.goto("/scenarios/test-scenario-id");
    await page.click('[data-testid="conversation-card"]:first-child');

    // Fork conversation
    await page.click('[data-testid="fork-conversation"]');
    await page.fill('[name="title"]', "My Alternative Take");
    await page.click('[data-testid="confirm-fork"]');

    // Verify redirect to forked conversation
    await expect(page).toHaveURL(/\/conversations\/[a-f0-9-]+/);
    await expect(page.locator("h1")).toContainText("My Alternative Take");

    // Verify 6 messages copied
    const messages = page.locator('[data-testid="message"]');
    await expect(messages).toHaveCount(6);

    // Send new message
    await page.fill('[data-testid="message-input"]', "What happens next?");
    await page.click('[data-testid="send-message"]');

    // Verify message appears
    await expect(page.locator("text=What happens next?")).toBeVisible();

    // Verify AI response starts streaming
    await expect(
      page.locator('[data-testid="typing-indicator"]')
    ).toBeVisible();

    // Wait for response to complete
    await expect(page.locator('[data-testid="typing-indicator"]')).toBeHidden({
      timeout: 15000,
    });
    await expect(
      page.locator('[data-testid="message"]:last-child')
    ).toContainText(/\w+/); // Has text
  });
});
```

### All Critical Journeys

| Journey               | Scenarios Covered                      | Priority |
| --------------------- | -------------------------------------- | -------- |
| Authentication        | Register, Login, Logout, Token Refresh | P0       |
| Scenario Creation     | Create via wizard, Validation errors   | P0       |
| Scenario Browsing     | Search, Filter, Pagination             | P1       |
| Scenario Forking      | Fork scenario, View fork tree          | P1       |
| Conversation Creation | Create conversation from scenario      | P0       |
| Message Streaming     | Send message, Receive AI response      | P0       |
| Conversation Forking  | Fork ROOT conversation, Copy messages  | P0       |
| Social - Follow       | Follow user, View followers/following  | P2       |
| Social - Like         | Like conversation, View liked          | P2       |
| Social - Memo         | Save memo, Edit memo, Delete memo      | P2       |
| Profile Management    | View profile, Edit bio, Upload avatar  | P1       |
| Tree Visualization    | View scenario tree, Navigate tree      | P1       |

**Total E2E Tests**: 12-15  
**Execution Time Target**: < 3 minutes (parallel)

---

## Performance Testing

### Load Testing (Future - Post-MVP)

**Framework**: k6

**Scenario 1: API Endpoint Load**

```javascript
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "2m", target: 100 }, // Ramp up to 100 users
    { duration: "5m", target: 100 }, // Stay at 100 users
    { duration: "2m", target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<200"], // 95% of requests must complete within 200ms
    http_req_failed: ["rate<0.01"], // Error rate < 1%
  },
};

export default function () {
  const res = http.get("http://localhost:8080/api/v1/scenarios");

  check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 200ms": (r) => r.timings.duration < 200,
  });

  sleep(1);
}
```

**Performance Benchmarks** (from Stories):

| Epic | Endpoint                        | P95 Target        | Measured |
| ---- | ------------------------------- | ----------------- | -------- |
| 0    | Novel ingestion                 | 30s per 10K words | TBD      |
| 1    | GET /scenarios                  | < 200ms           | TBD      |
| 1    | POST /scenarios                 | < 200ms           | TBD      |
| 2    | Prompt generation               | < 1s              | TBD      |
| 4    | Message streaming (first chunk) | < 1s              | TBD      |
| 5    | Conversation tree (depth 5)     | < 500ms           | TBD      |

### Frontend Performance

**Framework**: Lighthouse CI

**Target Metrics**:

- Performance Score: > 90
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Time to Interactive (TTI): < 3.5s
- Cumulative Layout Shift (CLS): < 0.1

**Lighthouse CI Config** (`.lighthouserc.json`):

```json
{
  "ci": {
    "collect": {
      "url": [
        "http://localhost:5173/",
        "http://localhost:5173/scenarios",
        "http://localhost:5173/scenarios/test-id"
      ],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "categories:accessibility": ["error", { "minScore": 0.9 }],
        "first-contentful-paint": ["error", { "maxNumericValue": 1500 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }]
      }
    }
  }
}
```

---

## Security Testing

### OWASP Top 10 Coverage

| Risk                      | Test Coverage                                 | Tool/Method              |
| ------------------------- | --------------------------------------------- | ------------------------ |
| Broken Access Control     | Integration tests verify authorization        | JUnit + TestRestTemplate |
| Cryptographic Failures    | Unit tests verify BCrypt hashing              | JUnit                    |
| Injection                 | Integration tests with SQL injection attempts | Testcontainers + SQL     |
| Insecure Design           | Architecture review                           | Manual review            |
| Security Misconfiguration | Security headers tested                       | E2E tests check headers  |
| Vulnerable Components     | Dependency scanning                           | Dependabot, Snyk         |
| Authentication Failures   | Integration tests for JWT validation          | JUnit                    |
| Data Integrity Failures   | Integration tests verify data validation      | JUnit                    |
| Logging Failures          | Manual review of logging                      | Code review              |
| SSRF                      | Not applicable (no user-provided URLs)        | N/A                      |

### Security Test Examples

**SQL Injection Prevention**:

```java
@Test
void shouldPreventSqlInjection() {
    String maliciousInput = "'; DROP TABLE scenarios; --";

    CreateScenarioRequest request = CreateScenarioRequest.builder()
        .title(maliciousInput)
        .scenarioType("CHARACTER_CHANGE")
        .build();

    HttpEntity<CreateScenarioRequest> entity = new HttpEntity<>(request, headers);

    ResponseEntity<ScenarioResponse> response = restTemplate.postForEntity(
        "/api/v1/scenarios",
        entity,
        ScenarioResponse.class
    );

    // Should sanitize and save safely
    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);

    // Verify tables still exist
    List<Scenario> scenarios = scenarioRepository.findAll();
    assertThat(scenarios).isNotEmpty();
}
```

**Authentication Header Validation**:

```java
@Test
void shouldRejectExpiredToken() {
    String expiredToken = generateExpiredJWT();

    HttpHeaders headers = new HttpHeaders();
    headers.setBearerAuth(expiredToken);

    HttpEntity<Void> entity = new HttpEntity<>(headers);

    ResponseEntity<String> response = restTemplate.exchange(
        "/api/v1/scenarios",
        HttpMethod.POST,
        entity,
        String.class
    );

    assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
}
```

---

## CI/CD Integration

### GitHub Actions Pipeline

```yaml
name: Test Suite

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: gaji_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: "17"
          distribution: "temurin"

      - name: Run unit tests
        run: ./gradlew test

      - name: Run integration tests
        run: ./gradlew integrationTest

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./build/reports/jacoco/test/jacocoTestReport.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit

      - name: Run integration tests
        run: npm run test:integration

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/coverage-final.json

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Start backend
        run: docker-compose up -d backend ai-service postgres

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

### Test Execution Order

1. **On PR**: Unit → Integration → E2E (if integration passes)
2. **On Merge to Main**: Full suite + performance tests
3. **Nightly**: Full suite + security scans + Lighthouse

---

## Test Data Management

### Test Database Setup

**Strategy**: Fresh database per test class

```java
@BeforeEach
void setUp() {
    scenarioRepository.deleteAll();
    userRepository.deleteAll();
    // Seed minimal test data
    testUser = userRepository.save(new User("test@example.com", "testuser", "hashedpass"));
    testBaseScenario = baseScenarioRepository.save(new BaseScenario(/* ... */));
}
```

### Test Data Builders

```java
public class ScenarioTestDataBuilder {
    private UUID id = UUID.randomUUID();
    private String title = "Test Scenario";
    private ScenarioType scenarioType = ScenarioType.CHARACTER_CHANGE;
    private Map<String, Object> customParameters = new HashMap<>();

    public ScenarioTestDataBuilder withTitle(String title) {
        this.title = title;
        return this;
    }

    public ScenarioTestDataBuilder withScenarioType(ScenarioType scenarioType) {
        this.scenarioType = scenarioType;
        return this;
    }

    public Scenario build() {
        return Scenario.builder()
            .id(id)
            .title(title)
            .scenarioType(scenarioType)
            .customParameters(customParameters)
            .build();
    }
}

// Usage
Scenario scenario = new ScenarioTestDataBuilder()
    .withTitle("Hermione in Slytherin")
    .withScenarioType(ScenarioType.CHARACTER_CHANGE)
    .build();
```

### Frontend Test Fixtures

```typescript
// fixtures/scenarios.ts
export const mockScenarios: Scenario[] = [
  {
    id: "uuid-1",
    baseStory: "harry_potter",
    scenarioType: "CHARACTER_CHANGE",
    title: "Hermione in Slytherin",
    forkCount: 12,
    conversationCount: 45,
    creator: {
      id: "user-1",
      username: "hermione_fan",
      avatarUrl: "https://example.com/avatar.jpg",
    },
    createdAt: "2025-11-13T10:00:00Z",
  },
  // More scenarios...
];

// Usage in tests
import { mockScenarios } from "@/fixtures/scenarios";

server.use(
  http.get("/api/v1/scenarios", () => {
    return HttpResponse.json({ content: mockScenarios });
  })
);
```

---

## Quality Gates

### PR Merge Requirements

**Automated Checks** (must pass):

- ✅ All unit tests pass (100%)
- ✅ All integration tests pass (100%)
- ✅ Code coverage ≥ 80% (backend), ≥ 70% (frontend)
- ✅ No critical security vulnerabilities (Snyk)
- ✅ Linting passes (ESLint, Checkstyle)
- ✅ Build succeeds

**Manual Checks** (recommended):

- 👁️ Code review approved by 1+ developers
- 👁️ E2E tests pass (run manually if touching critical paths)

### Production Deployment Gates

**Pre-Deployment**:

- ✅ All automated PR checks
- ✅ E2E test suite passes (100%)
- ✅ Performance benchmarks met (p95 < targets)
- ✅ Security scan clean (no high/critical vulnerabilities)
- ✅ Smoke tests pass on staging environment

**Post-Deployment**:

- ✅ Health check endpoints return 200 OK
- ✅ Error rate < 1% (first 10 minutes)
- ✅ p95 response time < 500ms (first 10 minutes)

---

## Test Maintenance

### Flaky Test Policy

**Definition**: Test fails intermittently without code changes

**Process**:

1. **Quarantine**: Move to `@Disabled` with `// FLAKY: <reason>` comment
2. **Investigation**: Assign owner to fix within 1 sprint
3. **Fix or Remove**: Either fix root cause or delete test
4. **Prevention**: Add retry logic only as last resort

### Test Hygiene

**Monthly Review**:

- Remove obsolete tests
- Update outdated fixtures
- Refactor duplicated test code
- Check for slow tests (> 5s)

**Naming Standards**:

- Clear, descriptive test names
- Follow `should{Behavior}When{Condition}` pattern
- Group related tests in `@Nested` classes (JUnit) or `describe` blocks (Vitest)

---

## Metrics and Reporting

### Test Metrics Dashboard

**Track Weekly**:

- Test count (unit/integration/e2e)
- Code coverage (backend/frontend)
- Test execution time
- Flaky test count
- Test failure rate

**Tools**:

- Codecov for coverage visualization
- GitHub Actions for CI/CD metrics
- Custom dashboard (Grafana) for production test results (future)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-13  
**Maintained By**: QA Team  
**Feedback**: #gaji-testing on Slack
