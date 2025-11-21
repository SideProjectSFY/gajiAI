# Story 3.2: Book Detail Page

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.2
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Build the book detail page that displays comprehensive book information and all scenarios created for that book. This page serves as the **hub** for scenario creation and discovery within a book context, implementing the book-centric architecture.

## Dependencies

**Blocks**:

- Story 1.2: Unified Scenario Creation Modal (triggered from this page)
- Story 3.1: Scenario Browse UI (scenario cards displayed here)

**Requires**:

- Story 3.0: Book Browse Page (users navigate from browse to detail)
- Story 0.4: Vue.js Frontend Project Setup
- Backend API: GET /api/v1/books/{id}

## Acceptance Criteria

### Page Structure

- [ ] **URL**: `/books/{bookId}`
- [ ] **Route name**: `BookDetail`
- [ ] **Breadcrumb**: `← Back to Books` (navigates to /books)
- [ ] **Layout**: Header + Statistics + Primary CTA + Scenario List

### Book Header Section

- [ ] Book cover image (if available, else placeholder)
- [ ] Book title (H1)
- [ ] Author name (subtitle)
- [ ] Genre badge(s)
- [ ] Publication year (if available)
- [ ] Short description/synopsis (max 300 chars, expandable)

### Statistics Section

Display aggregate metrics:

- [ ] **Total scenarios**: `45 scenarios created`
- [ ] **Total conversations**: `230 conversations across all scenarios`
- [ ] Visual indicator (icon + count)
- [ ] Update in real-time when new scenario created

### Primary CTA

- [ ] **`[+ Create Scenario]` button**
- [ ] Prominent placement (below statistics, above scenario list)
- [ ] Opens Scenario Creation Modal (Story 1.2)
- [ ] Passes `bookId` and `bookTitle` as props to modal

### Scenario List Section

- [ ] **Section title**: "Scenarios (45)"
- [ ] **Filter dropdown**: "All Types", "Character Changes", "Event Alterations", "Setting Modifications"
- [ ] **Sort dropdown**:
  - "Most Conversations" (default) - `conversation_count DESC`
  - "Most Forks" - `fork_count DESC`
  - "Newest" - `created_at DESC`
  - "Most Liked" - `like_count DESC`
- [ ] Scenario cards in grid layout:
  - Desktop: 2 columns
  - Mobile: 1 column
- [ ] Each card displays:
  - Scenario title
  - Scenario type badge
  - Preview text (first 100 chars of description)
  - Stats: 💬 conversations, 🍴 forks, ❤️ likes
  - Creator info (avatar + username)
- [ ] Click card → Navigate to Scenario Detail page
- [ ] Infinite scroll or pagination (load 20 scenarios per batch)

### API Integration

**GET /api/v1/books/{id}**:

```json
{
  "id": "uuid",
  "title": "Harry Potter Series",
  "author": "J.K. Rowling",
  "genre": "Fantasy",
  "publication_year": 1997,
  "description": "The story follows Harry Potter...",
  "cover_image_url": "https://...",
  "statistics": {
    "scenario_count": 45,
    "conversation_count": 230
  },
  "created_at": "2025-01-15T..."
}
```

**GET /api/v1/books/{bookId}/scenarios**:

```json
{
  "scenarios": [
    {
      "id": "uuid",
      "scenario_title": "Hermione in Slytherin",
      "scenario_types": ["character_changes"],
      "preview_text": "What if Hermione was sorted into Slytherin...",
      "conversation_count": 12,
      "fork_count": 5,
      "like_count": 8,
      "creator": {
        "id": "uuid",
        "username": "potter_fan_23",
        "avatar_url": "https://..."
      },
      "created_at": "2025-01-10T..."
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "has_next": true
  }
}
```

### Empty States

- [ ] **No scenarios yet**: "No scenarios created yet. Be the first!" with `[+ Create Scenario]` button
- [ ] **Filtered no results**: "No scenarios match the selected type."

### Mobile Responsive

- [ ] Single column scenario list on < 768px
- [ ] Book cover scales appropriately
- [ ] Statistics stack vertically on mobile
- [ ] Filter/Sort dropdowns full width on mobile

## Technical Implementation

### Component Structure

```vue
<template>
  <div class="book-detail-page">
    <!-- Breadcrumb -->
    <Breadcrumb :home="breadcrumbHome" :model="breadcrumbItems" />

    <!-- Book Header -->
    <div class="book-header">
      <div class="book-cover">
        <img
          v-if="book.cover_image_url"
          :src="book.cover_image_url"
          :alt="book.title"
        />
        <div v-else class="cover-placeholder">
          <i class="pi pi-book"></i>
        </div>
      </div>

      <div class="book-info">
        <h1 class="book-title">{{ book.title }}</h1>
        <p class="book-author">by {{ book.author }}</p>

        <div class="genre-badges">
          <span class="genre-badge">{{ book.genre }}</span>
          <span v-if="book.publication_year" class="year-badge">
            {{ book.publication_year }}
          </span>
        </div>

        <p class="book-description" :class="{ expanded: descriptionExpanded }">
          {{ book.description }}
        </p>
        <button
          v-if="book.description.length > 300"
          @click="descriptionExpanded = !descriptionExpanded"
          class="expand-btn"
        >
          {{ descriptionExpanded ? "Show Less" : "Read More" }}
        </button>
      </div>
    </div>

    <!-- Statistics -->
    <div class="statistics-section">
      <div class="stat-card">
        <i class="pi pi-file-edit"></i>
        <div class="stat-content">
          <span class="stat-value">{{ book.statistics.scenario_count }}</span>
          <span class="stat-label">Scenarios Created</span>
        </div>
      </div>

      <div class="stat-card">
        <i class="pi pi-comments"></i>
        <div class="stat-content">
          <span class="stat-value">{{
            book.statistics.conversation_count
          }}</span>
          <span class="stat-label">Total Conversations</span>
        </div>
      </div>
    </div>

    <!-- Primary CTA -->
    <div class="cta-section">
      <Button
        label="+ Create Scenario"
        severity="primary"
        size="large"
        icon="pi pi-plus"
        @click="showCreateScenarioModal = true"
      />
    </div>

    <!-- Scenario List -->
    <div class="scenario-list-section">
      <div class="section-header">
        <h2>Scenarios ({{ scenarios.length }})</h2>

        <div class="controls">
          <Dropdown
            v-model="filterType"
            :options="filterOptions"
            placeholder="All Types"
            @change="handleFilter"
          />

          <Dropdown
            v-model="sortOption"
            :options="sortOptions"
            placeholder="Sort by"
            @change="handleSort"
          />
        </div>
      </div>

      <!-- Scenario Grid -->
      <div class="scenario-grid">
        <ScenarioCard
          v-for="scenario in scenarios"
          :key="scenario.id"
          :scenario="scenario"
          @click="navigateToScenario(scenario.id)"
        />

        <!-- Loading Skeletons -->
        <SkeletonCard v-if="isLoading" v-for="i in 4" :key="`skeleton-${i}`" />
      </div>

      <!-- Empty State -->
      <div v-if="scenarios.length === 0 && !isLoading" class="empty-state">
        <i class="pi pi-inbox" style="font-size: 3rem; color: #ccc;"></i>
        <p>{{ emptyStateMessage }}</p>
        <Button
          label="+ Create First Scenario"
          severity="primary"
          @click="showCreateScenarioModal = true"
        />
      </div>

      <!-- Load More Trigger -->
      <div ref="loadMoreTrigger" class="load-more-trigger"></div>
    </div>

    <!-- Scenario Creation Modal -->
    <ScenarioCreationModal
      v-if="showCreateScenarioModal"
      :bookId="bookId"
      :bookTitle="book.title"
      @close="showCreateScenarioModal = false"
      @created="handleScenarioCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useIntersectionObserver } from "@vueuse/core";
import Breadcrumb from "primevue/breadcrumb";
import Button from "primevue/button";
import Dropdown from "primevue/dropdown";
import ScenarioCard from "@/components/ScenarioCard.vue";
import SkeletonCard from "@/components/SkeletonCard.vue";
import ScenarioCreationModal from "@/components/ScenarioCreationModal.vue";
import api from "@/services/api";

const route = useRoute();
const router = useRouter();

const bookId = ref(route.params.id as string);
const book = ref<Book | null>(null);
const scenarios = ref<Scenario[]>([]);
const isLoading = ref(false);
const hasMore = ref(true);
const page = ref(1);

const descriptionExpanded = ref(false);
const showCreateScenarioModal = ref(false);

const filterType = ref("all");
const sortOption = ref("most_conversations");

const breadcrumbHome = { icon: "pi pi-home", to: "/" };
const breadcrumbItems = [
  { label: "Books", to: "/books" },
  { label: computed(() => book.value?.title || "Loading...") },
];

const filterOptions = [
  { label: "All Types", value: "all" },
  { label: "Character Changes", value: "character_changes" },
  { label: "Event Alterations", value: "event_alterations" },
  { label: "Setting Modifications", value: "setting_modifications" },
];

const sortOptions = [
  { label: "Most Conversations", value: "most_conversations" },
  { label: "Most Forks", value: "most_forks" },
  { label: "Newest", value: "newest" },
  { label: "Most Liked", value: "most_liked" },
];

const emptyStateMessage = computed(() => {
  if (filterType.value !== "all") {
    return "No scenarios match the selected type.";
  }
  return "No scenarios created yet. Be the first!";
});

const fetchBook = async () => {
  try {
    const response = await api.get(`/api/v1/books/${bookId.value}`);
    book.value = response.data;
  } catch (error) {
    console.error("Failed to fetch book:", error);
    router.push("/books"); // Redirect if book not found
  }
};

const fetchScenarios = async (reset = false) => {
  if (isLoading.value || (!hasMore.value && !reset)) return;

  isLoading.value = true;

  try {
    const params = {
      type: filterType.value !== "all" ? filterType.value : undefined,
      sort: sortOption.value,
      page: reset ? 1 : page.value,
      limit: 20,
    };

    const response = await api.get(`/api/v1/books/${bookId.value}/scenarios`, {
      params,
    });

    if (reset) {
      scenarios.value = response.data.scenarios;
      page.value = 1;
    } else {
      scenarios.value.push(...response.data.scenarios);
    }

    hasMore.value = response.data.pagination.has_next;
    page.value++;
  } catch (error) {
    console.error("Failed to fetch scenarios:", error);
  } finally {
    isLoading.value = false;
  }
};

const handleFilter = () => {
  fetchScenarios(true);
};

const handleSort = () => {
  fetchScenarios(true);
};

const navigateToScenario = (scenarioId: string) => {
  router.push(`/books/${bookId.value}/scenarios/${scenarioId}`);
};

const handleScenarioCreated = (scenarioId: string) => {
  showCreateScenarioModal.value = false;

  // Refresh book statistics
  fetchBook();

  // Refresh scenario list
  fetchScenarios(true);

  // Navigate to new scenario detail page
  router.push(`/books/${bookId.value}/scenarios/${scenarioId}`);
};

// Infinite scroll setup
const loadMoreTrigger = ref<HTMLElement | null>(null);
useIntersectionObserver(
  loadMoreTrigger,
  ([{ isIntersecting }]) => {
    if (isIntersecting && hasMore.value && !isLoading.value) {
      fetchScenarios();
    }
  },
  { threshold: 0.5 }
);

onMounted(async () => {
  await fetchBook();
  await fetchScenarios(true);
});
</script>

<style scoped>
.book-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.book-header {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.book-cover {
  width: 200px;
  height: 300px;
  background: #f3f4f6;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.book-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  font-size: 4rem;
  color: #d1d5db;
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.book-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  color: #111827;
}

.book-author {
  font-size: 18px;
  color: #6b7280;
  margin: 0;
}

.genre-badges {
  display: flex;
  gap: 0.5rem;
}

.genre-badge,
.year-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #e0e7ff;
  color: #4f46e5;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.year-badge {
  background: #f3f4f6;
  color: #6b7280;
}

.book-description {
  font-size: 16px;
  line-height: 1.6;
  color: #374151;
  max-height: 80px;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.book-description.expanded {
  max-height: none;
}

.expand-btn {
  background: none;
  border: none;
  color: #4f46e5;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.statistics-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-card i {
  font-size: 2rem;
  color: #4f46e5;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

.cta-section {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
}

.scenario-list-section {
  margin-top: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.controls {
  display: flex;
  gap: 0.75rem;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.load-more-trigger {
  height: 50px;
  margin-top: 2rem;
}

@media (max-width: 767px) {
  .book-header {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .book-cover {
    width: 150px;
    height: 225px;
    margin: 0 auto;
  }

  .statistics-section {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .controls {
    width: 100%;
    flex-direction: column;
  }

  .scenario-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

## QA Checklist

### Functional Testing

- [ ] Book detail page loads with book information
- [ ] Statistics show correct scenario and conversation counts
- [ ] `[+ Create Scenario]` button opens modal
- [ ] Scenario list displays all scenarios for book
- [ ] Filter by type updates scenario list
- [ ] Sort option changes scenario order
- [ ] Click scenario card navigates to Scenario Detail page
- [ ] Breadcrumb `← Back to Books` navigates to /books

### Scenario Creation Testing

- [ ] Modal opens when `[+ Create Scenario]` clicked
- [ ] Modal receives correct `bookId` and `bookTitle` props
- [ ] Successfully created scenario refreshes statistics
- [ ] Successfully created scenario appears in list
- [ ] After creation, user navigated to new scenario detail page

### Filter & Sort Testing

- [ ] "All Types" shows all scenarios
- [ ] "Character Changes" shows only character scenarios
- [ ] "Event Alterations" shows only event scenarios
- [ ] "Setting Modifications" shows only setting scenarios
- [ ] Sort "Most Conversations" orders correctly
- [ ] Sort "Most Forks" orders correctly
- [ ] Sort "Newest" orders correctly
- [ ] Sort "Most Liked" orders correctly

### Empty State Testing

- [ ] Empty state appears when no scenarios
- [ ] Empty state button opens create modal
- [ ] Filtered empty state shows appropriate message
- [ ] Empty state disappears when scenarios loaded

### Mobile Responsive Testing

- [ ] Single column layout on < 768px
- [ ] Book cover centered on mobile
- [ ] Statistics stack vertically
- [ ] Filter/Sort controls stack vertically
- [ ] Scenario cards single column on mobile

### Performance Testing

- [ ] Initial page load < 1 second
- [ ] Scenario list loads progressively (infinite scroll)
- [ ] Filter/Sort triggers smooth transitions
- [ ] No lag when opening create modal

## Estimated Effort

10 hours

---

**Story Owner**: Frontend Lead

**Key Feature**: Central hub for book-specific scenario discovery and creation
