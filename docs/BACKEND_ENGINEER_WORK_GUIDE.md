# Gaji Platform: Backend Engineer Work Guide 💾

**Last Updated**: 2025-11-19  
**Version**: 1.0  
**Engineer**: Backend Engineer (Java/Spring Boot)

---

## 📋 Overview

이 문서는 **Backend Engineer** 전용 작업 가이드입니다. Spring Boot REST API, PostgreSQL, MyBatis, Docker 설정 등 백엔드 전체 로직을 담당합니다.

**담당 영역**:

- Spring Boot Application (:8080)
- PostgreSQL Database (13개 metadata tables)
- MyBatis SQL Mapper
- Flyway Database Migrations
- Spring Security (JWT)
- WebClient (FastAPI proxy)

**핵심 목표**:

- API 응답 시간 <500ms
- DB 쿼리 <100ms
- Circuit Breaker uptime >95%

---

## 🎯 Role & Responsibilities

### 주요 책임

1. **REST API 개발**: Spring Boot 기반 RESTful API
2. **Database 설계**: PostgreSQL 13개 테이블 (Flyway 마이그레이션)
3. **Business Logic**: 시나리오, 대화, 검색, 인증 로직
4. **AI Service Proxy**: FastAPI WebClient 프록시
5. **Security**: Spring Security + JWT 인증

### 기술 스택

- **Language**: Java 17+
- **Framework**: Spring Boot 3.2+, Spring Web, Spring Security
- **Database**: PostgreSQL 15
- **ORM**: MyBatis 3.5+ (SQL mapper)
- **Migration**: Flyway 9+
- **Build**: Gradle 8+
- **Client**: WebClient (FastAPI 호출), RestClient
- **Resilience**: Resilience4j (Circuit Breaker, Retry)

---

## 📅 Day-by-Day Work Schedule

### Day 1-2: Spring Boot & PostgreSQL Setup (11h)

#### Day 1: Spring Boot 기초 인프라 (6h)

**Story 0.1: Spring Boot Backend Setup**

**09:00-12:00 (3h): 프로젝트 초기 설정**

```bash
# 1. Spring Initializr 설정 (1h)
# https://start.spring.io/
# - Project: Gradle - Kotlin (or Groovy)
# - Language: Java
# - Spring Boot: 3.2.1
# - Packaging: Jar
# - Java: 17

# Dependencies 선택:
# - Spring Web
# - Spring Data JDBC
# - PostgreSQL Driver
# - Flyway Migration
# - Validation
# - Lombok

# 2. 프로젝트 구조 생성 (1h)
mkdir -p backend/src/main/java/com/gaji/{controller,service,repository,domain,dto,config,exception}
cd backend
./gradlew clean build

# 3. application.yml 설정 (1h)
```

**application.yml 기본 설정**:

```yaml
spring:
  application:
    name: gaji-backend

  datasource:
    url: jdbc:postgresql://localhost:5432/gaji
    username: gaji_user
    password: gaji_password
    driver-class-name: org.postgresql.Driver

  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true

  web:
    cors:
      allowed-origins: http://localhost:3000
      allowed-methods: GET,POST,PUT,DELETE,PATCH
      allowed-headers: "*"

server:
  port: 8080

# AI Service
ai-service:
  base-url: http://localhost:8000
  timeout: 30s
```

**13:00-15:00 (2h): Spring Boot 기본 구조**

```java
// config/WebConfig.java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("http://localhost:3000")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH")
                .allowedHeaders("*")
                .allowCredentials(true);
    }
}

// controller/HealthController.java
@RestController
@RequestMapping("/api/health")
public class HealthController {

    @GetMapping
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of(
            "status", "healthy",
            "service", "spring-boot-backend",
            "timestamp", LocalDateTime.now().toString()
        ));
    }
}
```

**16:00-18:00 (2h): WebClient 설정 (FastAPI Proxy)**

```java
// config/WebClientConfig.java
@Configuration
public class WebClientConfig {

    @Value("${ai-service.base-url}")
    private String aiServiceBaseUrl;

    @Bean
    public WebClient aiServiceWebClient() {
        return WebClient.builder()
                .baseUrl(aiServiceBaseUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .build();
    }
}

// service/AIServiceClient.java
@Service
@RequiredArgsConstructor
public class AIServiceClient {

    private final WebClient aiServiceWebClient;

    public Mono<String> healthCheck() {
        return aiServiceWebClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(String.class);
    }
}
```

**체크포인트 (Day 1)**:

- [ ] `./gradlew bootRun` 실행 성공 (:8080)
- [ ] `GET /api/health` 응답: `{"status": "healthy"}`
- [ ] WebClient 기본 설정 완료

**의존성**: ❌ 없음 (독립적 작업)

---

#### Day 2: PostgreSQL & Flyway (5h)

**Story 0.3: PostgreSQL Database & Flyway Migrations**

**09:00-12:00 (3h): Database 설계 & Flyway Migration**

**Flyway Migration 파일 생성**:

```sql
-- src/main/resources/db/migration/V1__init_schema.sql

-- 1. novels 테이블 (소설 메타데이터)
CREATE TABLE novels (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    published_year INT,
    genre VARCHAR(100),
    description TEXT,
    cover_image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. scenarios 테이블 (시나리오)
CREATE TABLE scenarios (
    id BIGSERIAL PRIMARY KEY,
    novel_id BIGINT NOT NULL REFERENCES novels(id),
    user_id BIGINT, -- Epic 6에서 추가 예정
    title VARCHAR(255) NOT NULL,
    description TEXT,
    scenario_type VARCHAR(50) NOT NULL, -- CHARACTER_CHANGE, EVENT_ALTERATION, SETTING_MODIFICATION

    -- Type별 필드 (JSONB 사용)
    scenario_data JSONB NOT NULL,

    -- Meta
    quality_score INT DEFAULT 0,
    is_public BOOLEAN DEFAULT false,
    view_count INT DEFAULT 0,
    fork_count INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scenarios_novel_id ON scenarios(novel_id);
CREATE INDEX idx_scenarios_type ON scenarios(scenario_type);

-- 3. conversations 테이블 (대화)
CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    scenario_id BIGINT NOT NULL REFERENCES scenarios(id),
    user_id BIGINT, -- Epic 6

    parent_conversation_id BIGINT REFERENCES conversations(id), -- Fork 지원

    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active', -- active, archived, forked

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_scenario_id ON conversations(scenario_id);

-- 4. messages 테이블 (메시지)
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id),

    role VARCHAR(20) NOT NULL, -- user, assistant
    content TEXT NOT NULL,

    -- AI 메타데이터
    token_count INT,
    generation_time_ms INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- 5. scenario_validations 테이블 (검증 결과)
CREATE TABLE scenario_validations (
    id BIGSERIAL PRIMARY KEY,
    scenario_id BIGINT NOT NULL REFERENCES scenarios(id),

    quality_score INT NOT NULL,
    issues JSONB,
    suggestions JSONB,

    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**추가 테이블 (Day 2 오후)**:

```sql
-- V2__add_discovery_tables.sql

-- 6. books 테이블 (도서 메타데이터)
CREATE TABLE books (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    cover_image_url VARCHAR(500),
    description TEXT,
    rating DECIMAL(3,2) DEFAULT 0.0,
    scenario_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. tags 테이블 (태그)
CREATE TABLE tags (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    tag_type VARCHAR(50) NOT NULL, -- genre, theme, character_type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. scenario_tags 테이블 (시나리오-태그 매핑)
CREATE TABLE scenario_tags (
    scenario_id BIGINT NOT NULL REFERENCES scenarios(id),
    tag_id BIGINT NOT NULL REFERENCES tags(id),
    PRIMARY KEY (scenario_id, tag_id)
);
```

**13:00-14:00 (1h): Flyway 실행 & 검증**

```bash
# Flyway 마이그레이션 실행
./gradlew flywayMigrate

# 테이블 확인
psql -U gaji_user -d gaji -c "\dt"

# 예상 출력:
#  novels
#  scenarios
#  conversations
#  messages
#  scenario_validations
#  books
#  tags
#  scenario_tags
#  flyway_schema_history
```

**14:00-15:00 (1h): MyBatis 설정**

```java
// config/MyBatisConfig.java
@Configuration
@MapperScan("com.gaji.repository")
public class MyBatisConfig {
    // MyBatis 자동 설정 활용
}

// domain/Novel.java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Novel {
    private Long id;
    private String title;
    private String author;
    private Integer publishedYear;
    private String genre;
    private String description;
    private String coverImageUrl;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

// repository/NovelMapper.java
@Mapper
public interface NovelMapper {

    @Select("SELECT * FROM novels WHERE id = #{id}")
    Optional<Novel> findById(Long id);

    @Select("SELECT * FROM novels ORDER BY created_at DESC LIMIT #{limit}")
    List<Novel> findAll(int limit);

    @Insert("INSERT INTO novels (title, author, published_year, genre, description) " +
            "VALUES (#{title}, #{author}, #{publishedYear}, #{genre}, #{description})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Novel novel);
}
```

**체크포인트 (Day 2)**:

- [ ] Flyway 마이그레이션 성공 (8개 테이블 생성)
- [ ] MyBatis Mapper 테스트 통과 (Novel CRUD)
- [ ] PostgreSQL 연결 확인

**의존성**:

- ✅ Story 0.1 (Spring Boot 설정) 완료 필요

---

### Day 2-3: Docker & Health Check (6.5h)

#### Day 2 오후: Docker Configuration (2.5h)

**Story 0.5: Docker Configuration (협업)**

**16:00-18:30 (2.5h): Spring Boot Dockerfile 작성**

```dockerfile
# backend/Dockerfile
FROM gradle:8.5-jdk17 AS builder
WORKDIR /app
COPY build.gradle settings.gradle ./
COPY src ./src
RUN gradle build --no-daemon -x test

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

**docker-compose.yml 통합 (AI, Backend 협업)**:

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gaji
      POSTGRES_USER: gaji_user
      POSTGRES_PASSWORD: gaji_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  vectordb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - ai-service
    environment:
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/gaji
      - AI_SERVICE_BASE_URL=http://ai-service:8000

  ai-service:
    build: ./ai-backend
    ports:
      - "8000:8000"
    depends_on:
      - vectordb
      - redis
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}

volumes:
  postgres_data:
```

**체크포인트 (Day 2 오후)**:

- [ ] `docker-compose up backend` 실행 성공
- [ ] PostgreSQL, Redis 서비스 healthy

**의존성**:

- ⚠️ AI Engineer와 협업 (docker-compose.yml 통합)

---

#### Day 3: Inter-Service Health Check (4h)

**Story 0.6: Inter-Service Health Check**

**09:00-13:00 (4h): Health Check 엔드포인트 구현**

```java
// dto/HealthCheckResponse.java
@Data
@Builder
public class HealthCheckResponse {
    private String service;
    private String status;
    private Map<String, String> dependencies;
    private LocalDateTime timestamp;
}

// service/HealthCheckService.java
@Service
@RequiredArgsConstructor
public class HealthCheckService {

    private final DataSource dataSource;
    private final AIServiceClient aiServiceClient;

    public HealthCheckResponse checkHealth() {
        Map<String, String> dependencies = new HashMap<>();

        // 1. PostgreSQL 체크
        try {
            try (Connection conn = dataSource.getConnection()) {
                dependencies.put("postgresql", "healthy");
            }
        } catch (SQLException e) {
            dependencies.put("postgresql", "unhealthy: " + e.getMessage());
        }

        // 2. AI Service 체크
        try {
            aiServiceClient.healthCheck().block(Duration.ofSeconds(5));
            dependencies.put("ai-service", "healthy");
        } catch (Exception e) {
            dependencies.put("ai-service", "unhealthy: " + e.getMessage());
        }

        // 3. 전체 상태 판정
        boolean allHealthy = dependencies.values().stream()
                .allMatch(status -> status.equals("healthy"));

        return HealthCheckResponse.builder()
                .service("spring-boot-backend")
                .status(allHealthy ? "healthy" : "degraded")
                .dependencies(dependencies)
                .timestamp(LocalDateTime.now())
                .build();
    }
}

// controller/HealthController.java (업데이트)
@RestController
@RequestMapping("/api/health")
@RequiredArgsConstructor
public class HealthController {

    private final HealthCheckService healthCheckService;

    @GetMapping
    public ResponseEntity<HealthCheckResponse> healthCheck() {
        HealthCheckResponse response = healthCheckService.checkHealth();

        HttpStatus status = response.getStatus().equals("healthy")
            ? HttpStatus.OK
            : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(status).body(response);
    }
}
```

**통합 테스트**:

```java
// test/integration/HealthCheckIntegrationTest.java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class HealthCheckIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    public void testHealthCheck() {
        ResponseEntity<HealthCheckResponse> response =
            restTemplate.getForEntity("/api/health", HealthCheckResponse.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody().getService()).isEqualTo("spring-boot-backend");
        assertThat(response.getBody().getDependencies()).containsKey("postgresql");
        assertThat(response.getBody().getDependencies()).containsKey("ai-service");
    }
}
```

**체크포인트 (Day 3)**:

- [ ] Health Check API 동작 (`GET /api/health`)
- [ ] PostgreSQL, AI Service 상태 확인 성공
- [ ] 통합 테스트 통과

**의존성**:

- ✅ Story 0.1, 0.3 (Spring Boot, PostgreSQL) 완료 필요
- ⚠️ AI Engineer Story 0.2 (FastAPI) 완료 필요

---

### Day 4: VectorDB Import 지원 (대기, 2h)

**Story 0.7 지원: VectorDB Import 완료 후 PostgreSQL 메타데이터 생성**

**16:00-18:00 (2h): Novel 메타데이터 API**

```java
// dto/NovelCreateRequest.java
@Data
public class NovelCreateRequest {
    @NotBlank
    private String title;

    @NotBlank
    private String author;

    private Integer publishedYear;
    private String genre;
    private String description;
}

// service/NovelService.java
@Service
@RequiredArgsConstructor
public class NovelService {

    private final NovelMapper novelMapper;

    @Transactional
    public Novel createNovel(NovelCreateRequest request) {
        Novel novel = Novel.builder()
                .title(request.getTitle())
                .author(request.getAuthor())
                .publishedYear(request.getPublishedYear())
                .genre(request.getGenre())
                .description(request.getDescription())
                .build();

        novelMapper.insert(novel);
        return novel;
    }

    public List<Novel> getAllNovels() {
        return novelMapper.findAll(100);
    }
}

// controller/NovelController.java
@RestController
@RequestMapping("/api/novels")
@RequiredArgsConstructor
public class NovelController {

    private final NovelService novelService;

    @PostMapping
    public ResponseEntity<Novel> createNovel(@Valid @RequestBody NovelCreateRequest request) {
        Novel novel = novelService.createNovel(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(novel);
    }

    @GetMapping
    public ResponseEntity<List<Novel>> getAllNovels() {
        return ResponseEntity.ok(novelService.getAllNovels());
    }
}
```

**체크포인트 (Day 4)**:

- [ ] Novel CRUD API 동작
- [ ] AI Engineer VectorDB import 완료 후 메타데이터 생성 확인

**의존성**:

- ⚠️ AI Engineer Story 0.7 (VectorDB Import) 완료 대기

---

### Day 5-6: Epic 1 - Scenario System (10h)

#### Day 5: Scenario CRUD API (8h)

**Story 1.1: Scenario Data Model & CRUD API**

**09:00-12:00 (3h): Domain & Mapper**

```java
// domain/Scenario.java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Scenario {
    private Long id;
    private Long novelId;
    private Long userId;
    private String title;
    private String description;
    private ScenarioType scenarioType;

    @JsonRawValue
    private String scenarioData; // JSONB

    private Integer qualityScore;
    private Boolean isPublic;
    private Integer viewCount;
    private Integer forkCount;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

// domain/ScenarioType.java
public enum ScenarioType {
    CHARACTER_CHANGE,
    EVENT_ALTERATION,
    SETTING_MODIFICATION
}

// dto/ScenarioCreateRequest.java
@Data
public class ScenarioCreateRequest {
    @NotNull
    private Long novelId;

    @NotBlank
    private String title;

    private String description;

    @NotNull
    private ScenarioType scenarioType;

    @NotNull
    private Map<String, Object> scenarioData;
}
```

**MyBatis Mapper**:

```java
// repository/ScenarioMapper.java
@Mapper
public interface ScenarioMapper {

    @Select("SELECT * FROM scenarios WHERE id = #{id}")
    @Results({
        @Result(property = "scenarioData", column = "scenario_data",
                typeHandler = JsonTypeHandler.class)
    })
    Optional<Scenario> findById(Long id);

    @Select("SELECT * FROM scenarios WHERE novel_id = #{novelId} ORDER BY created_at DESC")
    List<Scenario> findByNovelId(Long novelId);

    @Insert("INSERT INTO scenarios (novel_id, title, description, scenario_type, scenario_data) " +
            "VALUES (#{novelId}, #{title}, #{description}, #{scenarioType}, #{scenarioData}::jsonb)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Scenario scenario);

    @Update("UPDATE scenarios SET quality_score = #{qualityScore}, " +
            "updated_at = CURRENT_TIMESTAMP WHERE id = #{id}")
    void updateQualityScore(Long id, Integer qualityScore);
}

// config/JsonTypeHandler.java
@MappedTypes(String.class)
public class JsonTypeHandler extends BaseTypeHandler<String> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, String parameter, JdbcType jdbcType) throws SQLException {
        PGobject jsonObject = new PGobject();
        jsonObject.setType("jsonb");
        jsonObject.setValue(parameter);
        ps.setObject(i, jsonObject);
    }

    @Override
    public String getNullableResult(ResultSet rs, String columnName) throws SQLException {
        return rs.getString(columnName);
    }
    // ... (다른 메서드 생략)
}
```

**13:00-18:00 (5h): Service & Controller**

```java
// service/ScenarioService.java
@Service
@RequiredArgsConstructor
public class ScenarioService {

    private final ScenarioMapper scenarioMapper;
    private final ObjectMapper objectMapper;

    @Transactional
    public Scenario createScenario(ScenarioCreateRequest request) {
        try {
            String scenarioDataJson = objectMapper.writeValueAsString(request.getScenarioData());

            Scenario scenario = Scenario.builder()
                    .novelId(request.getNovelId())
                    .title(request.getTitle())
                    .description(request.getDescription())
                    .scenarioType(request.getScenarioType())
                    .scenarioData(scenarioDataJson)
                    .build();

            scenarioMapper.insert(scenario);
            return scenario;

        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Invalid scenario data", e);
        }
    }

    public Scenario getScenario(Long id) {
        return scenarioMapper.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Scenario not found: " + id));
    }

    public List<Scenario> getScenariosByNovel(Long novelId) {
        return scenarioMapper.findByNovelId(novelId);
    }
}

// controller/ScenarioController.java
@RestController
@RequestMapping("/api/scenarios")
@RequiredArgsConstructor
public class ScenarioController {

    private final ScenarioService scenarioService;

    @PostMapping
    public ResponseEntity<Scenario> createScenario(@Valid @RequestBody ScenarioCreateRequest request) {
        Scenario scenario = scenarioService.createScenario(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(scenario);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Scenario> getScenario(@PathVariable Long id) {
        Scenario scenario = scenarioService.getScenario(id);
        return ResponseEntity.ok(scenario);
    }

    @GetMapping
    public ResponseEntity<List<Scenario>> getScenariosByNovel(@RequestParam Long novelId) {
        List<Scenario> scenarios = scenarioService.getScenariosByNovel(novelId);
        return ResponseEntity.ok(scenarios);
    }
}
```

**체크포인트 (Day 5)**:

- [ ] Scenario CRUD API 동작 (POST, GET)
- [ ] JSONB 저장 및 조회 성공
- [ ] Frontend에서 API 호출 가능

**의존성**: ❌ 없음 (독립적 작업)

---

#### Day 6: Validation Proxy (2h)

**Story 1.3 지원: AI Validation API Proxy**

**09:00-11:00 (2h): Validation Proxy**

```java
// service/ScenarioValidationService.java
@Service
@RequiredArgsConstructor
public class ScenarioValidationService {

    private final WebClient aiServiceWebClient;
    private final ScenarioMapper scenarioMapper;

    public Mono<ValidationResult> validateScenario(Long scenarioId) {
        Scenario scenario = scenarioMapper.findById(scenarioId)
                .orElseThrow(() -> new ResourceNotFoundException("Scenario not found"));

        // AI Service 호출
        return aiServiceWebClient.post()
                .uri("/api/scenarios/validate")
                .bodyValue(Map.of(
                    "id", scenario.getId(),
                    "scenario_type", scenario.getScenarioType(),
                    "scenario_data", scenario.getScenarioData()
                ))
                .retrieve()
                .bodyToMono(ValidationResult.class)
                .doOnNext(result -> {
                    // 품질 점수 업데이트
                    scenarioMapper.updateQualityScore(scenarioId, result.getQualityScore());
                });
    }
}

// dto/ValidationResult.java
@Data
public class ValidationResult {
    private Integer qualityScore;
    private List<String> issues;
    private List<String> suggestions;
}

// controller/ScenarioController.java (추가)
@PostMapping("/{id}/validate")
public Mono<ResponseEntity<ValidationResult>> validateScenario(@PathVariable Long id) {
    return scenarioValidationService.validateScenario(id)
            .map(ResponseEntity::ok);
}
```

**체크포인트 (Day 6)**:

- [ ] Validation Proxy 동작 확인
- [ ] 품질 점수 업데이트 확인

**의존성**:

- ⚠️ AI Engineer Story 1.3 (Validation) 완료 필요

---

### Day 7: 대기 & 준비 (8h)

**Epic 4 설계 & 계획**

- Conversation 데이터 모델 검토
- Fork 로직 설계

---

### Day 8-10: Epic 4 - Conversation System (20h)

#### Day 8: Conversation CRUD API (8h)

**Story 4.1: Conversation Data Model & CRUD API**

**09:00-13:00 (4h): Domain & Mapper**

```java
// domain/Conversation.java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Conversation {
    private Long id;
    private Long scenarioId;
    private Long userId;
    private Long parentConversationId; // Fork 지원
    private String title;
    private ConversationStatus status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}

// domain/Message.java
@Data
@Builder
public class Message {
    private Long id;
    private Long conversationId;
    private MessageRole role;
    private String content;
    private Integer tokenCount;
    private Integer generationTimeMs;
    private LocalDateTime createdAt;
}

// repository/ConversationMapper.java
@Mapper
public interface ConversationMapper {

    @Insert("INSERT INTO conversations (scenario_id, title, status) " +
            "VALUES (#{scenarioId}, #{title}, #{status})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Conversation conversation);

    @Select("SELECT * FROM conversations WHERE id = #{id}")
    Optional<Conversation> findById(Long id);

    @Select("SELECT * FROM conversations WHERE scenario_id = #{scenarioId} ORDER BY created_at DESC")
    List<Conversation> findByScenarioId(Long scenarioId);
}

// repository/MessageMapper.java
@Mapper
public interface MessageMapper {

    @Insert("INSERT INTO messages (conversation_id, role, content, token_count) " +
            "VALUES (#{conversationId}, #{role}, #{content}, #{tokenCount})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Message message);

    @Select("SELECT * FROM messages WHERE conversation_id = #{conversationId} ORDER BY created_at ASC")
    List<Message> findByConversationId(Long conversationId);
}
```

**14:00-18:00 (4h): Service & Controller**

```java
// service/ConversationService.java
@Service
@RequiredArgsConstructor
public class ConversationService {

    private final ConversationMapper conversationMapper;
    private final MessageMapper messageMapper;

    @Transactional
    public Conversation createConversation(Long scenarioId, String title) {
        Conversation conversation = Conversation.builder()
                .scenarioId(scenarioId)
                .title(title)
                .status(ConversationStatus.ACTIVE)
                .build();

        conversationMapper.insert(conversation);
        return conversation;
    }

    public Conversation getConversation(Long id) {
        return conversationMapper.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Conversation not found"));
    }

    @Transactional
    public Message addMessage(Long conversationId, MessageRole role, String content) {
        Message message = Message.builder()
                .conversationId(conversationId)
                .role(role)
                .content(content)
                .tokenCount(content.length() / 4) // Approximate
                .build();

        messageMapper.insert(message);
        return message;
    }

    public List<Message> getMessages(Long conversationId) {
        return messageMapper.findByConversationId(conversationId);
    }
}

// controller/ConversationController.java
@RestController
@RequestMapping("/api/conversations")
@RequiredArgsConstructor
public class ConversationController {

    private final ConversationService conversationService;

    @PostMapping
    public ResponseEntity<Conversation> createConversation(
            @RequestParam Long scenarioId,
            @RequestParam(required = false) String title) {
        Conversation conversation = conversationService.createConversation(scenarioId, title);
        return ResponseEntity.status(HttpStatus.CREATED).body(conversation);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Conversation> getConversation(@PathVariable Long id) {
        return ResponseEntity.ok(conversationService.getConversation(id));
    }

    @GetMapping("/{id}/messages")
    public ResponseEntity<List<Message>> getMessages(@PathVariable Long id) {
        return ResponseEntity.ok(conversationService.getMessages(id));
    }
}
```

**체크포인트 (Day 8)**:

- [ ] Conversation CRUD API 동작
- [ ] Message 저장 및 조회 성공

**의존성**: ❌ 없음 (독립적 작업)

---

#### Day 9: Streaming Proxy (4h)

**Story 4.2 지원: AI Streaming Proxy**

**09:00-13:00 (4h): Streaming Proxy**

```java
// service/ChatService.java
@Service
@RequiredArgsConstructor
public class ChatService {

    private final WebClient aiServiceWebClient;
    private final ConversationService conversationService;

    public Mono<String> sendMessage(Long conversationId, String userMessage) {
        // 1. User 메시지 저장
        conversationService.addMessage(conversationId, MessageRole.USER, userMessage);

        // 2. AI Service 호출 (Long Polling task_id 반환)
        return aiServiceWebClient.post()
                .uri("/api/chat/stream")
                .bodyValue(Map.of(
                    "conversation_id", conversationId,
                    "message", userMessage
                ))
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, String>>() {})
                .map(response -> response.get("task_id"));
    }

    public Mono<TaskStatusResponse> pollTask(String taskId) {
        return aiServiceWebClient.get()
                .uri("/api/tasks/{taskId}", taskId)
                .retrieve()
                .bodyToMono(TaskStatusResponse.class)
                .doOnNext(response -> {
                    // Task 완료 시 Assistant 메시지 저장
                    if ("completed".equals(response.getStatus())) {
                        Long conversationId = response.getConversationId();
                        conversationService.addMessage(conversationId, MessageRole.ASSISTANT, response.getResponse());
                    }
                });
    }
}

// dto/TaskStatusResponse.java
@Data
public class TaskStatusResponse {
    private String status; // pending, processing, completed, failed
    private Long conversationId;
    private String response;
}

// controller/ChatController.java
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping("/send")
    public Mono<ResponseEntity<Map<String, String>>> sendMessage(
            @RequestParam Long conversationId,
            @RequestBody Map<String, String> request) {
        String message = request.get("message");
        return chatService.sendMessage(conversationId, message)
                .map(taskId -> ResponseEntity.ok(Map.of("task_id", taskId)));
    }

    @GetMapping("/tasks/{taskId}")
    public Mono<ResponseEntity<TaskStatusResponse>> pollTask(@PathVariable String taskId) {
        return chatService.pollTask(taskId)
                .map(ResponseEntity::ok);
    }
}
```

**체크포인트 (Day 9)**:

- [ ] Streaming Proxy 동작 확인
- [ ] Long Polling task_id 반환
- [ ] Assistant 메시지 저장 확인

**의존성**:

- ⚠️ AI Engineer Story 4.2 (Streaming) 완료 필요

---

#### Day 10: Fork Logic (8h)

**Story 4.3 지원: Conversation Fork Backend Logic**

**09:00-17:00 (8h): Fork Logic 구현**

```java
// service/ConversationForkService.java
@Service
@RequiredArgsConstructor
public class ConversationForkService {

    private final ConversationMapper conversationMapper;
    private final MessageMapper messageMapper;

    @Transactional
    public Conversation forkConversation(Long parentId, Long fromMessageId) {
        // 1. Parent conversation 조회
        Conversation parent = conversationMapper.findById(parentId)
                .orElseThrow(() -> new ResourceNotFoundException("Parent conversation not found"));

        // 2. Fork 생성
        Conversation fork = Conversation.builder()
                .scenarioId(parent.getScenarioId())
                .parentConversationId(parentId)
                .title(parent.getTitle() + " (Fork)")
                .status(ConversationStatus.ACTIVE)
                .build();

        conversationMapper.insert(fork);

        // 3. fromMessageId까지 메시지 복사
        List<Message> messages = messageMapper.findByConversationId(parentId);
        for (Message msg : messages) {
            if (msg.getId() > fromMessageId) break;

            Message copied = Message.builder()
                    .conversationId(fork.getId())
                    .role(msg.getRole())
                    .content(msg.getContent())
                    .tokenCount(msg.getTokenCount())
                    .build();

            messageMapper.insert(copied);
        }

        return fork;
    }
}

// controller/ConversationController.java (추가)
@PostMapping("/{id}/fork")
public ResponseEntity<Conversation> forkConversation(
        @PathVariable Long id,
        @RequestParam Long fromMessageId) {
    Conversation fork = conversationForkService.forkConversation(id, fromMessageId);
    return ResponseEntity.status(HttpStatus.CREATED).body(fork);
}
```

**체크포인트 (Day 10)**:

- [ ] Fork API 동작 (`POST /api/conversations/{id}/fork`)
- [ ] 메시지 복사 성공 확인
- [ ] Frontend Fork UI 연동 가능

**의존성**: ❌ 없음 (독립적 작업)

---

### Day 11-13: Epic 3, 5, 6 - Discovery, Tree, Auth (38h)

#### Day 11-12: Epic 3 - Discovery APIs (20h)

**Story 3.1: Book Browse API (6h)**

**Day 11, 09:00-15:00 (6h)**:

```java
// service/BookService.java
@Service
@RequiredArgsConstructor
public class BookService {

    private final BookMapper bookMapper;

    public List<Book> getAllBooks(int page, int size) {
        int offset = page * size;
        return bookMapper.findAll(size, offset);
    }

    public List<Book> getPopularBooks() {
        return bookMapper.findPopular(20);
    }
}

// controller/BookController.java
@RestController
@RequestMapping("/api/books")
@RequiredArgsConstructor
public class BookController {

    private final BookService bookService;

    @GetMapping
    public ResponseEntity<List<Book>> getBooks(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(bookService.getAllBooks(page, size));
    }

    @GetMapping("/popular")
    public ResponseEntity<List<Book>> getPopularBooks() {
        return ResponseEntity.ok(bookService.getPopularBooks());
    }
}
```

**Story 3.2: Book Detail API (4h)**

**Day 11, 16:00-20:00 (4h) (야간 작업)**:

```java
// dto/BookDetailResponse.java
@Data
@Builder
public class BookDetailResponse {
    private Book book;
    private List<Scenario> scenarios;
    private List<Tag> tags;
}

// service/BookService.java (추가)
public BookDetailResponse getBookDetail(Long bookId) {
    Book book = bookMapper.findById(bookId)
            .orElseThrow(() -> new ResourceNotFoundException("Book not found"));

    List<Scenario> scenarios = scenarioMapper.findByBookId(bookId);
    List<Tag> tags = tagMapper.findByBookId(bookId);

    return BookDetailResponse.builder()
            .book(book)
            .scenarios(scenarios)
            .tags(tags)
            .build();
}
```

**Story 3.3: Scenario Browse & Filtering (6h)**

**Day 12, 09:00-15:00 (6h)**:

```java
// dto/ScenarioFilterRequest.java
@Data
public class ScenarioFilterRequest {
    private Long bookId;
    private ScenarioType scenarioType;
    private List<Long> tagIds;
    private String sortBy; // popular, recent, rating
}

// repository/ScenarioMapper.java (추가)
@SelectProvider(type = ScenarioSqlProvider.class, method = "findWithFilters")
List<Scenario> findWithFilters(ScenarioFilterRequest filter);

// service/ScenarioService.java (추가)
public List<Scenario> searchScenarios(ScenarioFilterRequest filter) {
    return scenarioMapper.findWithFilters(filter);
}
```

**Story 3.4: Scenario Forking Backend (4h)**

**Day 12, 16:00-20:00 (4h) (야간 작업)**:

```java
// service/ScenarioForkService.java
@Service
@RequiredArgsConstructor
public class ScenarioForkService {

    private final ScenarioMapper scenarioMapper;

    @Transactional
    public Scenario forkScenario(Long originalId, Long userId) {
        Scenario original = scenarioMapper.findById(originalId)
                .orElseThrow(() -> new ResourceNotFoundException("Scenario not found"));

        // Fork 생성
        Scenario fork = Scenario.builder()
                .novelId(original.getNovelId())
                .userId(userId)
                .title(original.getTitle() + " (Fork)")
                .description(original.getDescription())
                .scenarioType(original.getScenarioType())
                .scenarioData(original.getScenarioData())
                .build();

        scenarioMapper.insert(fork);

        // Fork count 증가
        scenarioMapper.incrementForkCount(originalId);

        return fork;
    }
}
```

**체크포인트 (Day 11-12)**:

- [ ] Epic 3 모든 API 완성 (Browse, Detail, Filter, Fork)
- [ ] Frontend Discovery UI 연동 가능

---

#### Day 13: Epic 5 - Tree API & Epic 6 - Auth (18h)

**Story 5.1: Tree Data API (4h)**

**09:00-13:00 (4h)**:

```java
// dto/TreeNodeResponse.java
@Data
@Builder
public class TreeNodeResponse {
    private String root;
    private List<TreeNode> nodes;
    private List<TreeEdge> edges;
}

// service/ConversationTreeService.java
@Service
@RequiredArgsConstructor
public class ConversationTreeService {

    private final MessageMapper messageMapper;

    public TreeNodeResponse buildTree(Long conversationId) {
        List<Message> messages = messageMapper.findByConversationId(conversationId);

        List<TreeNode> nodes = messages.stream()
                .map(msg -> TreeNode.builder()
                        .id(msg.getId().toString())
                        .content(msg.getContent())
                        .role(msg.getRole().name())
                        .timestamp(msg.getCreatedAt().toString())
                        .build())
                .collect(Collectors.toList());

        List<TreeEdge> edges = new ArrayList<>();
        for (int i = 1; i < messages.size(); i++) {
            edges.add(TreeEdge.builder()
                    .from(messages.get(i-1).getId().toString())
                    .to(messages.get(i).getId().toString())
                    .build());
        }

        return TreeNodeResponse.builder()
                .root(conversationId.toString())
                .nodes(nodes)
                .edges(edges)
                .build();
    }
}

// controller/ConversationController.java (추가)
@GetMapping("/{id}/tree")
public ResponseEntity<TreeNodeResponse> getConversationTree(@PathVariable Long id) {
    return ResponseEntity.ok(conversationTreeService.buildTree(id));
}
```

**Story 6.1-6.3: Spring Security + JWT (14h)**

**14:00-21:00 (7h), Day 14 09:00-16:00 (7h) 총 14h**:

```java
// domain/User.java
@Data
@Builder
public class User {
    private Long id;
    private String email;
    private String password; // BCrypt hashed
    private String displayName;
    private String provider; // LOCAL, GOOGLE, KAKAO
    private String providerId;
    private LocalDateTime createdAt;
}

// config/SecurityConfig.java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**", "/api/health").permitAll()
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}

// service/JwtService.java
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration}")
    private Long expiration;

    public String generateToken(User user) {
        return Jwts.builder()
                .setSubject(user.getEmail())
                .claim("userId", user.getId())
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + expiration))
                .signWith(SignatureAlgorithm.HS512, secret)
                .compact();
    }

    public String extractEmail(String token) {
        return Jwts.parser()
                .setSigningKey(secret)
                .parseClaimsJws(token)
                .getBody()
                .getSubject();
    }
}

// controller/AuthController.java
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;
    private final JwtService jwtService;

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@RequestBody RegisterRequest request) {
        User user = userService.register(request);
        String token = jwtService.generateToken(user);
        return ResponseEntity.ok(new AuthResponse(token, user));
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
        User user = userService.authenticate(request.getEmail(), request.getPassword());
        String token = jwtService.generateToken(user);
        return ResponseEntity.ok(new AuthResponse(token, user));
    }
}
```

**체크포인트 (Day 13)**:

- [ ] Tree API 동작 (JSON 노드 생성)
- [ ] JWT 인증 기본 동작 (Register, Login)

---

### Day 14: 최종 검증 & 문서화 (8h)

**09:00-13:00 (4h): 성능 검증**

- API 응답 시간 측정 (p50, p95, p99)
- DB 쿼리 성능 확인
- Circuit Breaker 테스트

**14:00-18:00 (4h): 문서화 & 배포 준비**

- Swagger API 문서 완성 (`/swagger-ui.html`)
- Database ERD 문서
- ENV 변수 설정 가이드
- Docker 배포 가이드

**체크포인트 (Day 14)**:

- [ ] 성능 목표 달성: API <500ms, DB <100ms
- [ ] API 문서 완성 (Swagger)
- [ ] 프로덕션 배포 준비 완료

---

## 🚦 Daily Integration Checkpoints

### 매일 오후 6시: Backend API 통합 테스트

**Day 1-3**:

- [ ] Spring Boot :8080 실행 확인
- [ ] PostgreSQL 연결 확인 (Health Check)
- [ ] AI Service 연결 확인 (WebClient)

**Day 4-5**:

- [ ] Novel API 동작
- [ ] Scenario CRUD API 동작
- [ ] Frontend에서 API 호출 가능

**Day 6-10**:

- [ ] Validation Proxy 동작
- [ ] Conversation CRUD API 동작
- [ ] Streaming Proxy 동작 (task_id 반환)
- [ ] Fork Logic 동작

**Day 11-13**:

- [ ] Epic 3 모든 API 동작 (Browse, Detail, Filter, Fork)
- [ ] Tree API 동작
- [ ] JWT 인증 동작

**Day 14**:

- [ ] 전체 성능 목표 달성 확인
- [ ] API 문서 완성

---

## 🔧 Troubleshooting Guide

### 이슈 1: WebClient Timeout

**원인**: AI Service 응답 지연
**해결**:

```java
@Bean
public WebClient aiServiceWebClient() {
    return WebClient.builder()
            .baseUrl(aiServiceBaseUrl)
            .clientConnector(new ReactorClientHttpConnector(
                HttpClient.create().responseTimeout(Duration.ofSeconds(30))
            ))
            .build();
}
```

### 이슈 2: Flyway Migration 실패

**원인**: 이전 마이그레이션 파일 변경
**해결**:

```bash
# Flyway repair
./gradlew flywayRepair

# 또는 초기화
DROP DATABASE gaji;
CREATE DATABASE gaji;
./gradlew flywayMigrate
```

### 이슈 3: CORS 에러

**원인**: Frontend 요청 차단
**해결**:

```java
// WebConfig.java
@Override
public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000", "http://localhost:5173")
            .allowedMethods("*")
            .allowedHeaders("*")
            .allowCredentials(true);
}
```

### 이슈 4: JSONB 타입 에러

**원인**: PostgreSQL JSONB 타입 처리 실패
**해결**:

```java
// JsonTypeHandler.java 사용
// MyBatis에서 JSONB → String 변환 처리
```

---

## 📈 Success Metrics (KPIs)

### 성능 목표

- **API 응답 시간**: <500ms (p95)
- **DB 쿼리 시간**: <100ms (p95)
- **Circuit Breaker Uptime**: >95%
- **Error Rate**: <0.5%

### 품질 목표

- **API 테스트 커버리지**: >80%
- **Database 트랜잭션 성공률**: >99.5%
- **WebClient 연결 성공률**: >98%

### 테스트 커버리지

- **Unit Tests**: >80%
- **Integration Tests**: 주요 API 플로우
- **E2E Tests**: Frontend 연동 테스트

---

## 📚 Documentation Checklist

### API 문서 (Swagger)

- [ ] `/api/health` - Health check
- [ ] `/api/novels/**` - Novel CRUD
- [ ] `/api/scenarios/**` - Scenario CRUD + Validation
- [ ] `/api/conversations/**` - Conversation CRUD + Fork
- [ ] `/api/chat/**` - Streaming Proxy
- [ ] `/api/books/**` - Book Browse + Detail
- [ ] `/api/auth/**` - Register, Login, OAuth

### Database 문서

- [ ] ERD 다이어그램
- [ ] 13개 테이블 스키마 설명
- [ ] Flyway 마이그레이션 가이드

### Deployment 가이드

- [ ] Docker 빌드 & 실행 가이드
- [ ] ENV 변수 설정 가이드
- [ ] PostgreSQL 초기 설정

---

**Document Owner**: Backend Engineer  
**Last Updated**: 2025-11-19  
**Next Review**: Day 10 (Epic 4 완성 후)
