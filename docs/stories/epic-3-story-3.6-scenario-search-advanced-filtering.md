# Story 3.6: Scenario Search & Advanced Filtering

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.6
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 9 hours

## Description

Implement full-text search and advanced filtering for scenarios using PostgreSQL trigram similarity and GIN indexes. Supports keyword search, tag filtering, creator filtering, and date range queries with relevance ranking.

## Dependencies

**Blocks**:

- None (enhances discovery experience)

**Requires**:

- Story 3.1: Scenario Browse UI (integrates search into browse page)
- Story 1.1: Scenario Data Model (scenarios table with GIN indexes)

## Acceptance Criteria

- [ ] Search input with debounced query (300ms delay)
- [ ] Full-text search on scenario base_story, parameters (JSONB), and tags
- [ ] PostgreSQL `pg_trgm` extension for similarity search
- [ ] GIN index on base_story and parameters for fast search
- [ ] Advanced filters: scenario_type, creator, date range, minimum quality score
- [ ] Combined filter logic: search + filters applied together
- [ ] Relevance ranking using `ts_rank()` for text search results
- [ ] Search results paginated (20 per page)
- [ ] Search query highlighted in results
- [ ] Empty state: "No scenarios match your search"
- [ ] Search analytics: Log search queries and zero-result searches
- [ ] Unit tests >80% coverage

## Technical Notes

**PostgreSQL Full-Text Search Setup**:

```sql
-- Migration: V8__add_search_indexes.sql
-- Enable pg_trgm extension for similarity search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add tsvector column for full-text search
ALTER TABLE scenarios
ADD COLUMN search_vector tsvector;

-- Generate search_vector from base_story + parameters
UPDATE scenarios
SET search_vector =
  to_tsvector('english', coalesce(base_story, '')) ||
  to_tsvector('english', coalesce(parameters::text, ''));

-- Create GIN index for fast full-text search
CREATE INDEX idx_scenarios_search_vector ON scenarios USING GIN(search_vector);

-- Create GIN index for JSONB parameters (tag search)
CREATE INDEX idx_scenarios_parameters ON scenarios USING GIN(parameters);

-- Trigger to auto-update search_vector on insert/update
CREATE OR REPLACE FUNCTION scenarios_search_vector_trigger()
RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    to_tsvector('english', coalesce(NEW.base_story, '')) ||
    to_tsvector('english', coalesce(NEW.parameters::text, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER scenarios_search_vector_update
BEFORE INSERT OR UPDATE ON scenarios
FOR EACH ROW
EXECUTE FUNCTION scenarios_search_vector_trigger();
```

**Backend Search API**:

```java
@RestController
@RequestMapping("/api/scenarios")
public class ScenarioController {

    @Autowired
    private ScenarioRepository scenarioRepository;

    @Autowired
    private SearchAnalyticsService searchAnalyticsService;

    @GetMapping("/search")
    public ResponseEntity<Page<ScenarioDTO>> searchScenarios(
        @RequestParam(required = false) String query,
        @RequestParam(required = false) String scenarioType,
        @RequestParam(required = false) UUID creatorId,
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
        @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
        @RequestParam(required = false, defaultValue = "0.0") Double minQualityScore,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size,
        @RequestParam(defaultValue = "relevance") String sortBy
    ) {
        // Log search query for analytics
        searchAnalyticsService.logSearch(query, scenarioType, creatorId);

        Pageable pageable = PageRequest.of(page, size);
        Page<Scenario> results;

        if (query != null && !query.isBlank()) {
            // Full-text search with filters
            results = scenarioRepository.searchWithFilters(
                query.trim(),
                scenarioType,
                creatorId,
                startDate,
                endDate,
                minQualityScore,
                pageable
            );
        } else {
            // Filter-only search (no text query)
            results = scenarioRepository.filterScenarios(
                scenarioType,
                creatorId,
                startDate,
                endDate,
                minQualityScore,
                pageable
            );
        }

        // Log zero-result searches for improvement
        if (results.isEmpty() && query != null) {
            searchAnalyticsService.logZeroResults(query);
        }

        return ResponseEntity.ok(results.map(this::toDTO));
    }
}
```

**Repository with Custom Query (MyBatis Mapper)**:

```java
@Mapper
public interface ScenarioMapper {

    @Select("""
        SELECT s.*,
               ts_rank(s.search_vector, to_tsquery('english', :query)) AS rank
        FROM scenarios s
        WHERE s.search_vector @@ to_tsquery('english', :query)
          AND (:scenarioType IS NULL OR s.scenario_type = :scenarioType)
          AND (:creatorId IS NULL OR s.created_by = :creatorId)
          AND (:startDate IS NULL OR s.created_at >= :startDate)
          AND (:endDate IS NULL OR s.created_at <= :endDate)
          AND s.quality_score >= :minQualityScore
        ORDER BY
          CASE WHEN :#{#pageable.sort} = 'relevance' THEN rank ELSE 0 END DESC,
          CASE WHEN :#{#pageable.sort} = 'newest' THEN s.created_at ELSE NULL END DESC,
          CASE WHEN :#{#pageable.sort} = 'popular' THEN s.fork_count + s.conversation_count ELSE 0 END DESC
        """,
        countQuery = """
        SELECT COUNT(*)
        FROM scenarios s
        WHERE s.search_vector @@ to_tsquery('english', :query)
          AND (:scenarioType IS NULL OR s.scenario_type = :scenarioType)
          AND (:creatorId IS NULL OR s.created_by = :creatorId)
          AND (:startDate IS NULL OR s.created_at >= :startDate)
          AND (:endDate IS NULL OR s.created_at <= :endDate)
          AND s.quality_score >= :minQualityScore
        """,
        """)
    List<Scenario> searchWithFilters(
        @Param("query") String query,
        @Param("scenarioType") String scenarioType,
        @Param("creatorId") UUID creatorId,
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate,
        @Param("minQualityScore") Double minQualityScore,
        @Param("offset") int offset,
        @Param("limit") int limit
    );

    @Select("""
        SELECT * FROM scenarios s
        WHERE (:scenarioType IS NULL OR s.scenario_type = :scenarioType)
          AND (:creatorId IS NULL OR s.created_by = :creatorId)
          AND (:startDate IS NULL OR s.createdAt >= :startDate)
          AND (:endDate IS NULL OR s.createdAt <= :endDate)
          AND s.qualityScore >= :minQualityScore
        ORDER BY
          CASE WHEN :sortBy = 'newest' THEN s.createdAt END DESC,
          CASE WHEN :sortBy = 'popular' THEN s.forkCount + s.conversationCount END DESC
        """)
    Page<Scenario> filterScenarios(
        @Param("scenarioType") String scenarioType,
        @Param("creatorId") UUID creatorId,
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate,
        @Param("minQualityScore") Double minQualityScore,
        Pageable pageable
    );
}
```

**Frontend Search Component**:

```vue
<template>
  <div class="scenario-search">
    <!-- Search Input -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        @input="debouncedSearch"
        type="text"
        placeholder="Search scenarios by keywords, characters, events..."
        class="search-input"
      />
      <button @click="toggleFilters" class="filter-toggle-btn">
        <FilterIcon /> {{ filtersVisible ? "Hide" : "Show" }} Filters
      </button>
    </div>

    <!-- Advanced Filters -->
    <transition name="slide-down">
      <div v-if="filtersVisible" class="advanced-filters">
        <div class="filter-group">
          <label>Scenario Type</label>
          <select v-model="filters.scenarioType">
            <option value="">All Types</option>
            <option value="CHARACTER_CHANGE">Character Change</option>
            <option value="EVENT_ALTERATION">Event Alteration</option>
            <option value="SETTING_MODIFICATION">Setting Modification</option>
          </select>
        </div>

        <div class="filter-group">
          <label>Creator</label>
          <input
            v-model="filters.creatorName"
            type="text"
            placeholder="Search by creator username"
          />
        </div>

        <div class="filter-group">
          <label>Date Range</label>
          <div class="date-inputs">
            <input v-model="filters.startDate" type="date" />
            <span>to</span>
            <input v-model="filters.endDate" type="date" />
          </div>
        </div>

        <div class="filter-group">
          <label>Minimum Quality Score</label>
          <input
            v-model.number="filters.minQualityScore"
            type="number"
            min="0"
            max="10"
            step="0.5"
          />
        </div>

        <div class="filter-actions">
          <button @click="applyFilters" class="btn-primary">
            Apply Filters
          </button>
          <button @click="resetFilters" class="btn-secondary">Reset</button>
        </div>
      </div>
    </transition>

    <!-- Search Results -->
    <div class="search-results">
      <div v-if="isSearching" class="loading-state">
        <Spinner /> Searching...
      </div>

      <div v-else-if="results.length === 0" class="empty-state">
        <EmptyIcon />
        <p>No scenarios match your search</p>
        <p class="hint">Try different keywords or adjust your filters</p>
      </div>

      <div v-else class="results-list">
        <div class="results-header">
          <p>{{ totalResults }} scenarios found</p>
          <select v-model="sortBy" @change="handleSortChange">
            <option value="relevance">Most Relevant</option>
            <option value="newest">Newest First</option>
            <option value="popular">Most Popular</option>
          </select>
        </div>

        <ScenarioCard
          v-for="scenario in results"
          :key="scenario.id"
          :scenario="scenario"
          :highlightQuery="searchQuery"
        />

        <Pagination
          :currentPage="currentPage"
          :totalPages="totalPages"
          @page-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { debounce } from "lodash";
import api from "@/services/api";

const searchQuery = ref("");
const filtersVisible = ref(false);
const isSearching = ref(false);
const results = ref([]);
const totalResults = ref(0);
const currentPage = ref(0);
const totalPages = ref(0);
const sortBy = ref("relevance");

const filters = reactive({
  scenarioType: "",
  creatorName: "",
  startDate: "",
  endDate: "",
  minQualityScore: 0,
});

const debouncedSearch = debounce(async () => {
  await performSearch();
}, 300);

const performSearch = async () => {
  isSearching.value = true;

  try {
    const params = {
      query: searchQuery.value || undefined,
      scenarioType: filters.scenarioType || undefined,
      creatorName: filters.creatorName || undefined,
      startDate: filters.startDate || undefined,
      endDate: filters.endDate || undefined,
      minQualityScore: filters.minQualityScore,
      page: currentPage.value,
      size: 20,
      sortBy: sortBy.value,
    };

    const response = await api.get("/scenarios/search", { params });

    results.value = response.data.content;
    totalResults.value = response.data.totalElements;
    totalPages.value = response.data.totalPages;
  } catch (error) {
    console.error("Search failed:", error);
    showError("Search failed. Please try again.");
  } finally {
    isSearching.value = false;
  }
};

const applyFilters = () => {
  currentPage.value = 0;
  performSearch();
};

const resetFilters = () => {
  filters.scenarioType = "";
  filters.creatorName = "";
  filters.startDate = "";
  filters.endDate = "";
  filters.minQualityScore = 0;
  applyFilters();
};

const toggleFilters = () => {
  filtersVisible.value = !filtersVisible.value;
};

const handleSortChange = () => {
  currentPage.value = 0;
  performSearch();
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  performSearch();
};
</script>
```

## QA Checklist

### Functional Testing

- [ ] Search input debounces queries (300ms delay)
- [ ] Full-text search returns relevant results
- [ ] Advanced filters apply correctly (scenario_type, creator, date range)
- [ ] Combined search + filters work together
- [ ] Pagination works with search results
- [ ] Sort by relevance/newest/popular functions correctly
- [ ] Zero-result searches logged to analytics

### Search Quality Testing

- [ ] Search handles typos gracefully (pg_trgm similarity)
- [ ] Search ranking prioritizes exact matches
- [ ] JSONB parameter search works (e.g., "Hermione Slytherin")
- [ ] Tag search finds scenarios with matching tags
- [ ] Empty query + filters returns filtered results
- [ ] Special characters in query handled safely

### Performance

- [ ] Search query executes < 200ms (with GIN indexes)
- [ ] Pagination loads next page < 150ms
- [ ] Search vector auto-updates on scenario create/update
- [ ] No N+1 query issues in results

### Edge Cases

- [ ] Very long search query (>500 chars) rejected
- [ ] SQL injection attempts blocked
- [ ] Invalid date ranges handled gracefully
- [ ] Concurrent searches don't interfere

### Analytics & Monitoring

- [ ] Search queries logged with timestamp
- [ ] Zero-result searches tracked for improvement
- [ ] Popular search terms dashboard available
- [ ] Search performance metrics collected

## Estimated Effort

9 hours
