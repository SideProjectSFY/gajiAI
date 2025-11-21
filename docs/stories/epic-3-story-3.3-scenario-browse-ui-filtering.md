# Story 3.3: Scenario Browse UI & Filtering

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.3
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Create Vue.js scenario browse page with filtering by base_story, scenario_type, and quality_score, plus infinite scroll pagination.

## Dependencies

**Blocks**:

- Story 3.2: Scenario Forking Backend (needs scenarios to fork)
- Story 3.4: Scenario Search (extends browse functionality)

**Requires**:

- Story 0.4: Vue.js Frontend Project Setup
- Story 1.1: Scenario Data Model & API (reads scenarios)
- Story 1.5: Scenario Validation (quality_score available)

## Acceptance Criteria

- [ ] `ScenarioBrowsePage.vue` displays scenario cards in grid layout (3 columns on desktop, 1 on mobile)
- [ ] Each scenario card shows: base_story, scenario_type badge, scenario preview text, quality_score stars, fork_count, creator username
- [ ] Filter sidebar with: base_story multi-select dropdown, scenario_type checkboxes (CHARACTER_CHANGE, EVENT_ALTERATION, SETTING_MODIFICATION), quality_score slider (0-10)
- [ ] Infinite scroll pagination: loads 20 scenarios per page, triggers on scroll to bottom
- [ ] GET /api/scenarios?base_story=X&scenario_type=Y&min_quality=Z&page=N&size=20 endpoint
- [ ] Sort options: Most Popular (fork_count DESC), Highest Quality (quality_score DESC), Newest (created_at DESC)
- [ ] Empty state with CTA: "No scenarios found. Create your first What If scenario!"
- [ ] Scenario card click navigates to `/scenarios/{id}` detail page
- [ ] Loading skeleton while fetching scenarios
- [ ] Unit tests for filter logic >80% coverage

## Technical Notes

**Scenario Browse Component**:

```vue
<template>
  <div class="scenario-browse-page">
    <div class="page-header">
      <h1>Explore What If Scenarios</h1>
      <router-link to="/scenarios/create" class="btn-primary">
        Create New Scenario
      </router-link>
    </div>

    <div class="content-layout">
      <!-- Filter Sidebar -->
      <aside class="filter-sidebar">
        <h3>Filters</h3>

        <div class="filter-group">
          <label>Base Story</label>
          <select v-model="filters.baseStory" @change="applyFilters" multiple>
            <option value="">All Stories</option>
            <option v-for="story in baseStories" :key="story" :value="story">
              {{ story }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label>Scenario Type</label>
          <div class="checkbox-group">
            <label>
              <input
                type="checkbox"
                value="CHARACTER_CHANGE"
                v-model="filters.scenarioTypes"
                @change="applyFilters"
              />
              Character Change
            </label>
            <label>
              <input
                type="checkbox"
                value="EVENT_ALTERATION"
                v-model="filters.scenarioTypes"
                @change="applyFilters"
              />
              Event Alteration
            </label>
            <label>
              <input
                type="checkbox"
                value="SETTING_MODIFICATION"
                v-model="filters.scenarioTypes"
                @change="applyFilters"
              />
              Setting Modification
            </label>
          </div>
        </div>

        <div class="filter-group">
          <label>Minimum Quality Score</label>
          <input
            type="range"
            v-model="filters.minQuality"
            min="0"
            max="10"
            step="0.5"
            @change="applyFilters"
          />
          <span>{{ filters.minQuality }}/10</span>
        </div>

        <div class="filter-group">
          <label>Sort By</label>
          <select v-model="filters.sortBy" @change="applyFilters">
            <option value="popular">Most Popular</option>
            <option value="quality">Highest Quality</option>
            <option value="newest">Newest</option>
          </select>
        </div>

        <button @click="resetFilters" class="btn-secondary">
          Reset Filters
        </button>
      </aside>

      <!-- Scenario Grid -->
      <main class="scenario-grid">
        <div
          v-if="isLoading && scenarios.length === 0"
          class="loading-skeleton"
        >
          <ScenarioCardSkeleton v-for="n in 6" :key="n" />
        </div>

        <div v-else-if="scenarios.length === 0" class="empty-state">
          <p>No scenarios found matching your filters.</p>
          <router-link to="/scenarios/create" class="btn-primary">
            Create Your First Scenario
          </router-link>
        </div>

        <div v-else class="scenario-cards">
          <ScenarioCard
            v-for="scenario in scenarios"
            :key="scenario.id"
            :scenario="scenario"
            @click="navigateToDetail(scenario.id)"
          />
        </div>

        <!-- Infinite Scroll Trigger -->
        <div
          v-if="hasMore && !isLoading"
          v-observe-visibility="loadMore"
          class="load-more-trigger"
        >
          Loading more scenarios...
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";

const router = useRouter();

const scenarios = ref([]);
const isLoading = ref(false);
const hasMore = ref(true);
const currentPage = ref(0);

const filters = ref({
  baseStory: [],
  scenarioTypes: [],
  minQuality: 0,
  sortBy: "popular",
});

const baseStories = ref([
  "Harry Potter",
  "Game of Thrones",
  "Lord of the Rings",
  "Star Wars",
  "Marvel Universe",
  "Percy Jackson",
]);

const applyFilters = async () => {
  currentPage.value = 0;
  scenarios.value = [];
  await loadScenarios();
};

const loadScenarios = async () => {
  if (isLoading.value) return;

  isLoading.value = true;
  try {
    const params = {
      page: currentPage.value,
      size: 20,
      base_story: filters.value.baseStory.join(","),
      scenario_type: filters.value.scenarioTypes.join(","),
      min_quality: filters.value.minQuality,
      sort: filters.value.sortBy,
    };

    const response = await api.get("/scenarios", { params });

    if (currentPage.value === 0) {
      scenarios.value = response.data.content;
    } else {
      scenarios.value.push(...response.data.content);
    }

    hasMore.value = !response.data.last;
    currentPage.value++;
  } catch (error) {
    console.error("Failed to load scenarios:", error);
  } finally {
    isLoading.value = false;
  }
};

const loadMore = (isVisible) => {
  if (isVisible && hasMore.value && !isLoading.value) {
    loadScenarios();
  }
};

const resetFilters = () => {
  filters.value = {
    baseStory: [],
    scenarioTypes: [],
    minQuality: 0,
    sortBy: "popular",
  };
  applyFilters();
};

const navigateToDetail = (scenarioId) => {
  router.push(`/scenarios/${scenarioId}`);
};

onMounted(() => {
  loadScenarios();
});
</script>
```

**ScenarioCard Component**:

```vue
<template>
  <div class="scenario-card" :class="`type-${scenario.scenario_type}`">
    <div class="card-header">
      <span class="base-story">{{ scenario.base_story }}</span>
      <span class="scenario-type-badge">{{ scenarioTypeLabel }}</span>
    </div>

    <div class="card-body">
      <p class="scenario-preview">{{ scenarioPreview }}</p>
    </div>

    <div class="card-footer">
      <div class="quality-score">
        <span class="stars">{{
          "⭐".repeat(Math.round(scenario.quality_score * 5))
        }}</span>
        <span class="score-text">{{ scenario.quality_score.toFixed(1) }}</span>
      </div>
      <div class="stats">
        <span class="fork-count">🍴 {{ scenario.fork_count }} forks</span>
        <span class="creator">by @{{ scenario.creator_username }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps(["scenario"]);

const scenarioTypeLabel = computed(() => {
  const labels = {
    CHARACTER_CHANGE: "Character",
    EVENT_ALTERATION: "Event",
    SETTING_MODIFICATION: "Setting",
  };
  return labels[props.scenario.scenario_type] || props.scenario.scenario_type;
});

const scenarioPreview = computed(() => {
  const { scenario_type, parameters, base_story } = props.scenario;

  if (scenario_type === "CHARACTER_CHANGE") {
    return `What if ${parameters.character} was ${parameters.new_property} instead of ${parameters.original_property}?`;
  } else if (scenario_type === "EVENT_ALTERATION") {
    return `What if ${parameters.event_name} had a different outcome in ${base_story}?`;
  } else {
    return `What if ${base_story} took place in ${parameters.new_setting}?`;
  }
});
</script>
```

## QA Checklist

### Functional Testing

- [ ] Browse page loads 20 scenarios on initial load
- [ ] Filter by base_story shows only matching scenarios
- [ ] Filter by scenario_type shows only selected types
- [ ] Quality score slider filters scenarios correctly
- [ ] Sort by popular/quality/newest works
- [ ] Infinite scroll loads next page on scroll to bottom
- [ ] Reset filters clears all filters and reloads

### UI/UX Testing

- [ ] Scenario cards responsive on mobile/tablet/desktop
- [ ] Loading skeleton appears while fetching
- [ ] Empty state shows when no scenarios match
- [ ] Scenario type badges color-coded (blue/green/purple)
- [ ] Quality score stars display correctly (0-5 stars)

### Performance

- [ ] Initial page load < 1s
- [ ] Filter application < 500ms
- [ ] Infinite scroll smooth without jank
- [ ] Scenario card rendering optimized (virtual scrolling if 100+ scenarios)

### Accessibility

- [ ] Filter controls keyboard navigable
- [ ] Scenario cards have proper focus indicators
- [ ] Screen reader announces filter changes
- [ ] Empty state accessible

## Estimated Effort

8 hours
