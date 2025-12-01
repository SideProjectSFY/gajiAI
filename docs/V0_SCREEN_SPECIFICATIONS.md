# V0 Screen Design Specifications

**Project**: Gaji - Interactive Fiction Platform  
**Last Updated**: 2025-11-13  
**Framework**: Vue 3 + TypeScript + PandaCSS + PrimeVue  
**Target**: v0.dev / Lovable.ai Screen Generation

---

## Table of Contents

1. [Design System](#design-system)
2. [Domain 1: Scenario Creation](#domain-1-scenario-creation)
3. [Domain 2: Scenario Discovery](#domain-2-scenario-discovery)
4. [Domain 3: Conversation](#domain-3-conversation)
5. [Domain 4: Tree Visualization](#domain-4-tree-visualization)
6. [Domain 5: User Profile & Social](#domain-5-user-profile--social)
7. [Common Components](#common-components)
8. [Responsive Design](#responsive-design)
9. [Accessibility](#accessibility)

---

## Design System

### Color Palette

```typescript
// PandaCSS theme configuration
const colors = {
  primary: {
    50: "#e8f5f0",
    100: "#c1e6d9",
    500: "#1F7D51", // Main brand color (forest green)
    600: "#1a6a45",
    900: "#0b3121",
  },
  secondary: {
    500: "#DEAD5C", // Accent color (gold)
    600: "#c8924d",
  },
  neutral: {
    50: "#fafafa",
    100: "#f5f5f5",
    200: "#e5e5e5",
    700: "#404040",
    900: "#171717",
  },
  success: "#10b981",
  warning: "#f59e0b",
  error: "#ef4444",
};
```

### Typography

```typescript
const typography = {
  fontFamily: {
    sans: "Inter, system-ui, sans-serif",
    mono: "JetBrains Mono, monospace",
  },
  fontSize: {
    xs: "0.75rem", // 12px
    sm: "0.875rem", // 14px
    base: "1rem", // 16px
    lg: "1.125rem", // 18px
    xl: "1.25rem", // 20px
    "2xl": "1.5rem", // 24px
    "3xl": "1.875rem", // 30px
  },
};
```

### Spacing

```typescript
const spacing = {
  1: "0.25rem", // 4px
  2: "0.5rem", // 8px
  3: "0.75rem", // 12px
  4: "1rem", // 16px
  6: "1.5rem", // 24px
  8: "2rem", // 32px
  12: "3rem", // 48px
  16: "4rem", // 64px
};
```

### Component Variants

**Buttons**:

- Primary: Filled background, white text
- Secondary: Outlined, transparent background
- Ghost: No border, hover background
- Sizes: sm (32px), md (40px), lg (48px)

**Inputs**:

- Default: Border with focus ring
- Error: Red border
- Success: Green border
- Sizes: sm, md, lg

---

## Domain 1: Scenario Creation

**Story References**: Epic 1.2, 1.3, 1.4 - Character/Event/Setting Wizards

### 1.1 Scenario Creation Wizard

**Route**: `/scenarios/create`

**Layout**: Multi-step wizard (Stepper component)

#### Step 1: Select Base Story

**Components**:

- `RadioButtonGroup` (PrimeVue)
- `Card` with book cover images

**Screen Structure**:

```vue
<template>
  <div class="scenario-wizard">
    <Stepper :activeStep="0" :steps="wizardSteps" />

    <Card class="wizard-content">
      <h2>Select Your Base Story</h2>
      <p>Choose the fictional universe for your What If scenario</p>

      <div class="story-grid">
        <StoryCard
          v-for="story in baseStories"
          :key="story.id"
          :title="story.title"
          :cover="story.coverUrl"
          :selected="selectedStory === story.id"
          @click="selectStory(story.id)"
        />
      </div>

      <Button
        label="Next: Choose Scenario Type"
        :disabled="!selectedStory"
        @click="nextStep"
      />
    </Card>
  </div>
</template>
```

**Data**:

```typescript
interface BaseStory {
  id: string;
  title: string;
  coverUrl: string;
  description: string;
}

const baseStories: BaseStory[] = [
  {
    id: "harry_potter",
    title: "Harry Potter",
    coverUrl: "/images/covers/harry-potter.jpg",
    description: "The wizarding world of Hogwarts",
  },
  // ... more stories
];
```

**Styling** (PandaCSS):

```css
.story-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-4);
  padding: var(--spacing-6);
}
```

---

#### Step 2: Choose Scenario Type

**Components**:

- `TabView` (PrimeVue) with 3 tabs
- Icon + description for each type

**Screen Structure**:

```vue
<template>
  <Card class="wizard-content">
    <h2>What If Scenario Type</h2>

    <TabView v-model:activeIndex="activeTab">
      <TabPanel header="Character Change">
        <div class="scenario-type-card">
          <i class="pi pi-user" />
          <h3>Character Property Change</h3>
          <p>Alter a character's house, personality, skills, or backstory</p>
          <Button label="Select" @click="selectType('CHARACTER_CHANGE')" />
        </div>
      </TabPanel>

      <TabPanel header="Event Alteration">
        <div class="scenario-type-card">
          <i class="pi pi-calendar" />
          <h3>Event Alteration</h3>
          <p>Change the outcome of key events in the story</p>
          <Button label="Select" @click="selectType('EVENT_ALTERATION')" />
        </div>
      </TabPanel>

      <TabPanel header="Setting Modification">
        <div class="scenario-type-card">
          <i class="pi pi-map" />
          <h3>Setting Modification</h3>
          <p>Modify the world, era, magic system, or technology</p>
          <Button label="Select" @click="selectType('SETTING_MODIFICATION')" />
        </div>
      </TabPanel>
    </TabView>
  </Card>
</template>
```

---

#### Step 3A: Character Change Form (if CHARACTER_CHANGE selected)

**Components**:

- `AutoComplete` for character search
- `Dropdown` for property selection
- `InputText` for original/new values
- `Textarea` for ripple effects
- `Preview` pane (right sidebar, sticky)

**Screen Structure**:

```vue
<template>
  <div class="wizard-content-with-preview">
    <Card class="form-section">
      <h2>Character Property Change</h2>

      <div class="form-group">
        <label>Character</label>
        <AutoComplete
          v-model="character"
          :suggestions="characterSuggestions"
          @complete="searchCharacters"
          placeholder="e.g., Hermione Granger"
        />
      </div>

      <div class="form-group">
        <label>Property to Change</label>
        <Dropdown
          v-model="property"
          :options="propertyOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select property"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Original Value</label>
          <InputText v-model="originalValue" placeholder="e.g., Gryffindor" />
        </div>

        <div class="form-group">
          <label>New Value</label>
          <InputText v-model="newValue" placeholder="e.g., Slytherin" />
        </div>
      </div>

      <div class="form-group">
        <label>When does this change occur?</label>
        <InputText
          v-model="changePoint"
          placeholder="e.g., Sorting Hat ceremony"
        />
      </div>

      <div class="form-group">
        <label>Ripple Effects (Optional)</label>
        <Chips
          v-model="rippleEffects"
          placeholder="Press Enter to add effect"
        />
      </div>

      <Button label="Create Scenario" @click="submitScenario" />
    </Card>

    <Card class="preview-section sticky">
      <h3>Preview</h3>
      <ScenarioPreview :data="formData" />
    </Card>
  </div>
</template>
```

**Data**:

```typescript
interface CharacterChangeForm {
  character: string;
  property: "house" | "personality" | "skill" | "backstory";
  originalValue: string;
  newValue: string;
  changePoint?: string;
  rippleEffects?: string[];
}

const propertyOptions = [
  { label: "House", value: "house" },
  { label: "Personality", value: "personality" },
  { label: "Skill/Ability", value: "skill" },
  { label: "Backstory", value: "backstory" },
];
```

**Styling**:

```css
.wizard-content-with-preview {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-6);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.preview-section.sticky {
  position: sticky;
  top: var(--spacing-4);
  height: fit-content;
}
```

---

#### Step 3B: Event Alteration Form (if EVENT_ALTERATION selected)

**Screen Structure**:

```vue
<template>
  <div class="wizard-content-with-preview">
    <Card class="form-section">
      <h2>Event Alteration</h2>

      <div class="form-group">
        <label>Event Name</label>
        <AutoComplete
          v-model="event"
          :suggestions="eventSuggestions"
          @complete="searchEvents"
          placeholder="e.g., Battle of Hogwarts"
        />
      </div>

      <div class="form-group">
        <label>Timeline Point</label>
        <InputText
          v-model="timelinePoint"
          placeholder="e.g., Year 7, May 2nd"
        />
      </div>

      <div class="form-group">
        <label>Alteration Type</label>
        <Dropdown
          v-model="alterationType"
          :options="alterationTypeOptions"
          optionLabel="label"
          optionValue="value"
        />
      </div>

      <div class="form-group">
        <label>Original Outcome</label>
        <Textarea
          v-model="originalOutcome"
          rows="3"
          placeholder="Describe what originally happened"
        />
      </div>

      <div class="form-group">
        <label>New Outcome</label>
        <Textarea
          v-model="newOutcome"
          rows="3"
          placeholder="Describe the altered outcome"
        />
      </div>

      <div class="form-group">
        <label>Affected Characters</label>
        <MultiSelect
          v-model="affectedCharacters"
          :options="characterOptions"
          placeholder="Select characters"
          display="chip"
        />
      </div>

      <Button label="Create Scenario" @click="submitScenario" />
    </Card>

    <Card class="preview-section sticky">
      <h3>Preview</h3>
      <ScenarioPreview :data="formData" />
    </Card>
  </div>
</template>
```

**Data**:

```typescript
const alterationTypeOptions = [
  { label: "Prevent Event", value: "prevent" },
  { label: "Accelerate Event", value: "accelerate" },
  { label: "Relocate Event", value: "relocate" },
  { label: "Change Outcome", value: "outcome_change" },
];
```

---

#### Step 3C: Setting Modification Form

**Screen Structure**:

```vue
<template>
  <div class="wizard-content-with-preview">
    <Card class="form-section">
      <h2>Setting Modification</h2>

      <div class="form-group">
        <label>Setting Element</label>
        <Dropdown
          v-model="settingElement"
          :options="settingElementOptions"
          optionLabel="label"
          optionValue="value"
        />
      </div>

      <div class="form-group">
        <label>Modification Scope</label>
        <SelectButton
          v-model="scope"
          :options="scopeOptions"
          optionLabel="label"
          optionValue="value"
        />
      </div>

      <div class="form-group">
        <label>Change Description</label>
        <Textarea
          v-model="changeDescription"
          rows="5"
          placeholder="Describe how the setting is modified"
        />
      </div>

      <div class="form-group">
        <label>Impact Level</label>
        <Slider
          v-model="impactLevel"
          :min="1"
          :max="3"
          :step="1"
          :marks="{ 1: 'Minor', 2: 'Moderate', 3: 'Major' }"
        />
      </div>

      <Button label="Create Scenario" @click="submitScenario" />
    </Card>

    <Card class="preview-section sticky">
      <h3>Preview</h3>
      <ScenarioPreview :data="formData" />
    </Card>
  </div>
</template>
```

**Data**:

```typescript
const settingElementOptions = [
  { label: "Location", value: "location" },
  { label: "Historical Era", value: "era" },
  { label: "Magic System", value: "magic_system" },
  { label: "Technology Level", value: "technology" },
];

const scopeOptions = [
  { label: "Global", value: "global" },
  { label: "Regional", value: "regional" },
  { label: "Local", value: "local" },
];
```

---

### 1.2 Scenario Preview Component

**Reusable component** shown in sticky sidebar during creation.

```vue
<template>
  <div class="scenario-preview">
    <div class="preview-header">
      <Tag :value="scenarioType" severity="info" />
      <span class="base-story">{{ baseStory }}</span>
    </div>

    <div class="preview-content">
      <h4>{{ generateTitle() }}</h4>
      <p class="preview-description">{{ generateDescription() }}</p>

      <div v-if="rippleEffects?.length" class="ripple-effects">
        <h5>Potential Effects:</h5>
        <ul>
          <li v-for="effect in rippleEffects" :key="effect">{{ effect }}</li>
        </ul>
      </div>
    </div>

    <div class="preview-footer">
      <i class="pi pi-info-circle" />
      <span>AI will generate conversations based on this scenario</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const generateTitle = () => {
  if (props.data.scenarioType === "CHARACTER_CHANGE") {
    return `${props.data.character} in ${props.data.newValue}`;
  }
  // ... other types
};
</script>
```

---

## Domain 2: Scenario Discovery

**Story References**: Epic 3.1, 3.4 - Browse UI, Search UI

### 2.1 Browse Scenarios Page

**Route**: `/scenarios/browse`

**Layout**: Filter sidebar + Scenario grid

**Screen Structure**:

```vue
<template>
  <div class="browse-page">
    <aside class="filter-sidebar">
      <Card>
        <h3>Filters</h3>

        <div class="filter-group">
          <label>Base Story</label>
          <Dropdown
            v-model="filters.baseStory"
            :options="baseStoryOptions"
            placeholder="All Stories"
            showClear
          />
        </div>

        <div class="filter-group">
          <label>Scenario Type</label>
          <MultiSelect
            v-model="filters.scenarioTypes"
            :options="scenarioTypeOptions"
            placeholder="All Types"
            display="chip"
          />
        </div>

        <div class="filter-group">
          <label>Min Quality Score</label>
          <Slider v-model="filters.minQuality" :min="0" :max="1" :step="0.1" />
          <span class="quality-value">{{ filters.minQuality.toFixed(1) }}</span>
        </div>

        <div class="filter-group">
          <Checkbox
            v-model="filters.hasForks"
            :binary="true"
            label="Has Forks Only"
          />
        </div>

        <Button label="Apply Filters" @click="applyFilters" class="w-full" />
        <Button
          label="Clear"
          severity="secondary"
          @click="clearFilters"
          class="w-full mt-2"
        />
      </Card>
    </aside>

    <main class="scenario-grid-area">
      <div class="grid-header">
        <h2>Scenarios ({{ totalCount }})</h2>
        <Dropdown
          v-model="sortBy"
          :options="sortOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Sort by"
        />
      </div>

      <DataView
        :value="scenarios"
        :layout="viewMode"
        :paginator="true"
        :rows="20"
        :totalRecords="totalCount"
        @page="onPage"
      >
        <template #list="slotProps">
          <ScenarioListItem :scenario="slotProps.data" />
        </template>

        <template #grid="slotProps">
          <ScenarioCard :scenario="slotProps.data" />
        </template>
      </DataView>
    </main>
  </div>
</template>
```

**Data**:

```typescript
interface BrowseFilters {
  baseStory?: string;
  scenarioTypes: string[];
  minQuality: number;
  hasForks: boolean;
}

const sortOptions = [
  { label: "Most Recent", value: "created_at,desc" },
  { label: "Highest Quality", value: "quality_score,desc" },
  { label: "Most Forked", value: "fork_count,desc" },
  { label: "Most Conversations", value: "conversation_count,desc" },
];
```

**Styling**:

```css
.browse-page {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--spacing-6);
  padding: var(--spacing-6);
}

.filter-sidebar {
  position: sticky;
  top: var(--spacing-4);
  height: fit-content;
}

.scenario-grid-area {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}
```

---

### 2.2 Scenario Card Component

**Reusable component** for grid/list display.

```vue
<template>
  <Card class="scenario-card" @click="goToScenario">
    <div class="card-header">
      <Tag :value="scenario.scenarioType" />
      <span class="quality-badge">
        <i class="pi pi-star-fill" />
        {{ scenario.qualityScore.toFixed(2) }}
      </span>
    </div>

    <h3 class="scenario-title">{{ scenario.title }}</h3>
    <p class="scenario-description">
      {{ truncate(scenario.description, 150) }}
    </p>

    <div class="scenario-meta">
      <span class="base-story">
        <i class="pi pi-book" />
        {{ scenario.baseStory }}
      </span>
      <span class="fork-count">
        <i class="pi pi-share-alt" />
        {{ scenario.forkCount }} forks
      </span>
    </div>

    <div class="card-footer">
      <Avatar
        :image="scenario.creator.avatarUrl"
        :label="scenario.creator.username[0]"
        size="small"
      />
      <span class="creator-name">{{ scenario.creator.username }}</span>
      <span class="created-date">{{ formatDate(scenario.createdAt) }}</span>
    </div>
  </Card>
</template>
```

---

### 2.3 Search Page

**Route**: `/scenarios/search`

**Screen Structure**:

```vue
<template>
  <div class="search-page">
    <div class="search-header">
      <InputGroup class="search-input-group">
        <InputText
          v-model="searchQuery"
          placeholder="Search scenarios..."
          @input="debouncedSearch"
        />
        <Button icon="pi pi-search" @click="search" />
      </InputGroup>

      <Button
        icon="pi pi-filter"
        label="Advanced Filters"
        @click="toggleAdvancedFilters"
        severity="secondary"
      />
    </div>

    <div v-if="showAdvancedFilters" class="advanced-filters">
      <Card>
        <h3>Advanced Search</h3>
        <!-- Same filters as browse page -->
      </Card>
    </div>

    <div v-if="searchResults.length" class="search-results">
      <p>{{ searchResults.length }} results found</p>

      <DataView :value="searchResults" layout="list">
        <template #list="slotProps">
          <SearchResultItem :result="slotProps.data" :query="searchQuery" />
        </template>
      </DataView>
    </div>

    <div v-else-if="hasSearched" class="no-results">
      <i class="pi pi-search" />
      <p>No scenarios found matching your search</p>
      <Button label="Clear Search" @click="clearSearch" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";

const debouncedSearch = useDebounceFn(() => {
  search();
}, 300);
</script>
```

---

## Domain 3: Conversation

**Story References**: Epic 4.2, 4.3 - Chat Interface, Forking UI

### 3.1 Conversation Page

**Route**: `/conversations/:id`

**Layout**: Chat interface with message list + input + fork button

**Screen Structure**:

```vue
<template>
  <div class="conversation-page">
    <header class="conversation-header">
      <div class="header-left">
        <Button icon="pi pi-arrow-left" text @click="goBack" />
        <div class="conversation-info">
          <h2>{{ conversation.title }}</h2>
          <p class="scenario-link" @click="goToScenario">
            {{ conversation.scenario.baseStory }} -
            {{ conversation.scenario.title }}
          </p>
        </div>
      </div>

      <div class="header-right">
        <Button
          icon="pi pi-share-alt"
          label="Fork"
          @click="showForkModal = true"
          :disabled="!canFork"
        />
        <Button
          icon="pi pi-heart"
          :severity="isLiked ? 'danger' : 'secondary'"
          @click="toggleLike"
        />
        <Dropdown icon="pi pi-ellipsis-v" :options="conversationActions" />
      </div>
    </header>

    <main class="message-area" ref="messageContainer">
      <div
        v-for="message in messages"
        :key="message.id"
        class="message-wrapper"
      >
        <MessageBubble :message="message" :isUser="message.role === 'user'" />
      </div>

      <div v-if="isStreaming" class="streaming-indicator">
        <ProgressSpinner style="width: 20px; height: 20px" />
        <span>AI is typing...</span>
      </div>
    </main>

    <footer class="message-input-area">
      <InputGroup class="message-input-group">
        <Textarea
          v-model="messageInput"
          placeholder="Type your message..."
          :autoResize="true"
          :maxRows="5"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <Button
          icon="pi pi-send"
          @click="sendMessage"
          :disabled="!messageInput.trim() || isStreaming"
        />
      </InputGroup>

      <p class="input-hint">Press Enter to send, Shift+Enter for new line</p>
    </footer>

    <ForkConversationModal
      v-if="showForkModal"
      :conversation="conversation"
      @close="showForkModal = false"
      @forked="handleForked"
    />
  </div>
</template>
```

**Data**:

```typescript
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

const canFork = computed(() => {
  // Only ROOT conversations can be forked
  return conversation.value.parentConversationId === null;
});
```

**Styling**:

```css
.conversation-page {
  display: grid;
  grid-template-rows: auto 1fr auto;
  height: 100vh;
}

.message-area {
  overflow-y: auto;
  padding: var(--spacing-4);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.message-input-area {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-neutral-200);
}
```

---

### 3.2 Message Bubble Component

```vue
<template>
  <div
    :class="[
      'message-bubble',
      { 'user-message': isUser, 'assistant-message': !isUser },
    ]"
  >
    <Avatar v-if="!isUser" image="/ai-avatar.png" shape="circle" />

    <div class="message-content">
      <div class="message-text" v-html="renderedContent" />
      <span class="message-timestamp">{{ formatTime(message.createdAt) }}</span>
    </div>

    <Avatar
      v-if="isUser"
      :image="currentUser.avatarUrl"
      :label="currentUser.username[0]"
      shape="circle"
    />
  </div>
</template>

<script setup lang="ts">
import { marked } from "marked";

const renderedContent = computed(() => {
  return marked.parse(props.message.content);
});
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: var(--spacing-3);
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  background: var(--color-primary-500);
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.assistant-message .message-content {
  background: var(--color-neutral-100);
  color: var(--color-neutral-900);
  border-radius: 18px 18px 18px 4px;
}

.message-content {
  padding: var(--spacing-3) var(--spacing-4);
  max-width: 70%;
}

.message-timestamp {
  font-size: var(--font-xs);
  color: var(--color-neutral-500);
  margin-top: var(--spacing-1);
  display: block;
}
</style>
```

---

### 3.3 Fork Conversation Modal

```vue
<template>
  <Dialog
    v-model:visible="visible"
    header="Fork Conversation"
    :modal="true"
    :style="{ width: '500px' }"
  >
    <div class="fork-modal-content">
      <p>
        Create an alternative exploration of this scenario. The first
        {{ copyCount }} messages will be copied to your new conversation.
      </p>

      <div class="form-group">
        <label>New Conversation Title</label>
        <InputText
          v-model="forkTitle"
          placeholder="e.g., Alternative: Hermione Befriends Draco"
        />
      </div>

      <div class="info-box">
        <i class="pi pi-info-circle" />
        <div>
          <strong>Messages to copy:</strong> {{ copyCount }} most recent
          messages<br />
          <strong>Note:</strong> Forked conversations cannot be forked again
          (max depth = 1)
        </div>
      </div>
    </div>

    <template #footer>
      <Button label="Cancel" severity="secondary" @click="close" />
      <Button label="Create Fork" @click="createFork" :loading="isCreating" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
const copyCount = computed(() => {
  return Math.min(6, props.conversation.messages.length);
});

const createFork = async () => {
  isCreating.value = true;
  try {
    const response = await api.post(
      `/conversations/${props.conversation.id}/fork`,
      {
        title: forkTitle.value,
      }
    );
    emit("forked", response.data);
    close();
  } finally {
    isCreating.value = false;
  }
};
</script>
```

---

## Domain 4: Tree Visualization

**Story References**: Epic 5.2, 5.3 - D3.js Tree, Navigation

### 4.1 Conversation Tree Page

**Route**: `/conversations/:id/tree`

**Layout**: SVG canvas with D3.js tree + navigation controls + breadcrumb

**Screen Structure**:

```vue
<template>
  <div class="tree-visualization-page">
    <header class="tree-header">
      <Breadcrumb :model="breadcrumbItems" />

      <div class="tree-controls">
        <ButtonGroup>
          <Button icon="pi pi-plus" @click="zoomIn" tooltip="Zoom In" />
          <Button icon="pi pi-minus" @click="zoomOut" tooltip="Zoom Out" />
          <Button
            icon="pi pi-refresh"
            @click="resetView"
            tooltip="Reset View"
          />
        </ButtonGroup>

        <ToggleButton
          v-model="compactMode"
          onIcon="pi pi-th-large"
          offIcon="pi pi-list"
          onLabel="Compact"
          offLabel="Expanded"
        />
      </div>
    </header>

    <main class="tree-canvas-area">
      <svg ref="svgCanvas" class="tree-svg">
        <!-- D3.js renders tree here -->
      </svg>

      <div v-if="selectedNode" class="node-details-panel">
        <Card>
          <h3>{{ selectedNode.title }}</h3>
          <p>{{ selectedNode.messageCount }} messages</p>
          <p>{{ selectedNode.likeCount }} likes</p>
          <Button label="Open Conversation" @click="openConversation" />
        </Card>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import * as d3 from "d3";

onMounted(() => {
  renderTree();
});

const renderTree = () => {
  const svg = d3.select(svgCanvas.value);
  const width = svgCanvas.value.clientWidth;
  const height = svgCanvas.value.clientHeight;

  // Tree layout
  const treeLayout = d3.tree().size([height - 100, width - 200]);

  // Hierarchy
  const root = d3.hierarchy(treeData.value);
  const treeNodes = treeLayout(root);

  // Links (edges)
  svg
    .selectAll(".link")
    .data(treeNodes.links())
    .join("path")
    .attr("class", "link")
    .attr(
      "d",
      d3
        .linkHorizontal()
        .x((d) => d.y)
        .y((d) => d.x)
    )
    .attr("stroke", "#cbd5e1")
    .attr("stroke-width", 2)
    .attr("fill", "none");

  // Nodes (circles)
  const node = svg
    .selectAll(".node")
    .data(treeNodes.descendants())
    .join("g")
    .attr("class", "node")
    .attr("transform", (d) => `translate(${d.y},${d.x})`)
    .on("click", handleNodeClick);

  node
    .append("circle")
    .attr("r", 20)
    .attr("fill", (d) => (d.data.isRoot ? "#1F7D51" : "#c1e6d9"))
    .attr("stroke", "#1a6a45")
    .attr("stroke-width", 2);

  node
    .append("text")
    .attr("dy", "0.35em")
    .attr("x", (d) => (d.children ? -25 : 25))
    .attr("text-anchor", (d) => (d.children ? "end" : "start"))
    .text((d) => d.data.title)
    .attr("font-size", "12px");
};
</script>

<style scoped>
.tree-canvas-area {
  position: relative;
  height: calc(100vh - 120px);
  overflow: hidden;
}

.tree-svg {
  width: 100%;
  height: 100%;
}

.node-details-panel {
  position: absolute;
  top: var(--spacing-4);
  right: var(--spacing-4);
  width: 300px;
}
</style>
```

**Data**:

```typescript
interface TreeNode {
  id: string;
  title: string;
  messageCount: number;
  likeCount: number;
  isRoot: boolean;
  children?: TreeNode[];
}
```

---

### 4.2 Tree Navigation Controls

**Component for zoom/pan/focus**:

```vue
<template>
  <div class="tree-nav-controls">
    <ButtonGroup vertical>
      <Button icon="pi pi-search-plus" @click="zoomIn" />
      <Button icon="pi pi-search-minus" @click="zoomOut" />
      <Button icon="pi pi-arrows-alt" @click="fitToScreen" />
      <Button icon="pi pi-times" @click="resetZoom" />
    </ButtonGroup>

    <div class="minimap">
      <svg class="minimap-svg" ref="minimapSvg">
        <!-- Small overview of entire tree -->
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
const zoomIn = () => {
  zoom.value *= 1.2;
  applyZoom();
};

const zoomOut = () => {
  zoom.value /= 1.2;
  applyZoom();
};

const fitToScreen = () => {
  // Calculate bounding box and fit
  const bounds = getTreeBounds();
  zoom.value = calculateFitZoom(bounds);
  pan.value = calculateFitPan(bounds);
  applyZoom();
};
</script>
```

---

## Domain 5: User Profile & Social

**Story References**: Epic 6.2, 6.3, 6.5, 6.7, 6.9 - Auth, Profile, Follow, Like, Memo

### 5.1 Login/Register Page

**Route**: `/auth/login`, `/auth/register`

**Screen Structure**:

```vue
<template>
  <div class="auth-page">
    <Card class="auth-card">
      <template #title>
        <img src="/logo.svg" alt="Gaji" class="logo" />
        <h2>{{ isLogin ? "Welcome Back" : "Create Account" }}</h2>
      </template>

      <template #content>
        <form @submit.prevent="handleSubmit">
          <div v-if="!isLogin" class="form-group">
            <label>Username</label>
            <InputText
              v-model="form.username"
              placeholder="hermione_fan"
              :invalid="errors.username"
            />
            <small v-if="errors.username" class="error">{{
              errors.username
            }}</small>
          </div>

          <div class="form-group">
            <label>Email</label>
            <InputText
              v-model="form.email"
              type="email"
              placeholder="user@example.com"
              :invalid="errors.email"
            />
            <small v-if="errors.email" class="error">{{ errors.email }}</small>
          </div>

          <div class="form-group">
            <label>Password</label>
            <Password
              v-model="form.password"
              :feedback="!isLogin"
              toggleMask
              :invalid="errors.password"
            />
            <small v-if="errors.password" class="error">{{
              errors.password
            }}</small>
          </div>

          <Button
            :label="isLogin ? 'Log In' : 'Sign Up'"
            type="submit"
            :loading="isSubmitting"
            class="w-full"
          />
        </form>

        <Divider />

        <p class="switch-mode">
          {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
          <a @click="toggleMode">{{ isLogin ? "Sign Up" : "Log In" }}</a>
        </p>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  width: 100%;
  max-width: 400px;
  margin: var(--spacing-4);
}

.logo {
  width: 60px;
  height: 60px;
  margin: 0 auto var(--spacing-4);
  display: block;
}
</style>
```

---

### 5.2 User Profile Page

**Route**: `/users/:username`

**Screen Structure**:

```vue
<template>
  <div class="profile-page">
    <header class="profile-header">
      <div
        class="cover-photo"
        :style="{ backgroundImage: `url(${user.coverUrl})` }"
      />

      <div class="profile-info">
        <Avatar
          :image="user.avatarUrl"
          :label="user.username[0]"
          size="xlarge"
          shape="circle"
          class="profile-avatar"
        />

        <div class="user-details">
          <h1>{{ user.username }}</h1>
          <p class="bio">{{ user.bio }}</p>

          <div class="user-stats">
            <div class="stat">
              <strong>{{ user.followerCount }}</strong>
              <span>Followers</span>
            </div>
            <div class="stat">
              <strong>{{ user.followingCount }}</strong>
              <span>Following</span>
            </div>
            <div class="stat">
              <strong>{{ user.scenarioCount }}</strong>
              <span>Scenarios</span>
            </div>
            <div class="stat">
              <strong>{{ user.conversationCount }}</strong>
              <span>Conversations</span>
            </div>
          </div>

          <div class="profile-actions">
            <Button
              v-if="!isOwnProfile"
              :label="isFollowing ? 'Unfollow' : 'Follow'"
              :severity="isFollowing ? 'secondary' : 'primary'"
              @click="toggleFollow"
            />
            <Button
              v-else
              label="Edit Profile"
              icon="pi pi-pencil"
              @click="showEditModal = true"
            />
          </div>
        </div>
      </div>
    </header>

    <main class="profile-content">
      <TabView v-model:activeIndex="activeTab">
        <TabPanel header="Scenarios">
          <DataView :value="userScenarios" layout="grid">
            <template #grid="slotProps">
              <ScenarioCard :scenario="slotProps.data" />
            </template>
          </DataView>
        </TabPanel>

        <TabPanel header="Conversations">
          <DataView :value="userConversations" layout="list">
            <template #list="slotProps">
              <ConversationListItem :conversation="slotProps.data" />
            </template>
          </DataView>
        </TabPanel>

        <TabPanel v-if="isOwnProfile" header="Liked">
          <DataView :value="likedConversations" layout="list">
            <template #list="slotProps">
              <ConversationListItem :conversation="slotProps.data" />
            </template>
          </DataView>
        </TabPanel>
      </TabView>
    </main>

    <EditProfileModal
      v-if="showEditModal"
      :user="user"
      @close="showEditModal = false"
      @updated="handleProfileUpdated"
    />
  </div>
</template>
```

**Styling**:

```css
.profile-header {
  position: relative;
}

.cover-photo {
  height: 200px;
  background-size: cover;
  background-position: center;
  background-color: var(--color-neutral-200);
}

.profile-info {
  position: relative;
  padding: var(--spacing-6);
  display: flex;
  gap: var(--spacing-6);
}

.profile-avatar {
  margin-top: -60px;
  border: 4px solid white;
}

.user-stats {
  display: flex;
  gap: var(--spacing-6);
  margin: var(--spacing-4) 0;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-1);
}
```

---

### 5.3 Follow Button Component

```vue
<template>
  <Button
    :label="isFollowing ? 'Unfollow' : 'Follow'"
    :severity="isFollowing ? 'secondary' : 'primary'"
    :icon="isFollowing ? 'pi pi-user-minus' : 'pi pi-user-plus'"
    @click="toggleFollow"
    :loading="isLoading"
  />
</template>

<script setup lang="ts">
const toggleFollow = async () => {
  isLoading.value = true;
  try {
    if (isFollowing.value) {
      await api.delete(`/users/${props.userId}/unfollow`);
      isFollowing.value = false;
    } else {
      await api.post(`/users/${props.userId}/follow`);
      isFollowing.value = true;
    }
  } finally {
    isLoading.value = false;
  }
};
</script>
```

---

### 5.4 Conversation Memo Panel

**Sidebar component** for personal memos.

```vue
<template>
  <aside class="memo-panel">
    <Card>
      <template #title>
        <h3>Personal Memo</h3>
        <Tag value="Private" severity="info" />
      </template>

      <template #content>
        <div v-if="!isEditing" class="memo-display">
          <div v-if="memo" v-html="renderedMemo" class="memo-content" />
          <p v-else class="no-memo">No memo yet. Click to add notes.</p>

          <Button
            label="Edit Memo"
            icon="pi pi-pencil"
            text
            @click="startEdit"
          />
        </div>

        <div v-else class="memo-editor">
          <Textarea
            v-model="editableMemo"
            :autoResize="true"
            :maxRows="10"
            placeholder="Add your personal notes about this conversation..."
            :maxlength="1000"
          />

          <div class="memo-actions">
            <small>{{ editableMemo.length }}/1000</small>
            <div>
              <Button label="Cancel" severity="secondary" @click="cancelEdit" />
              <Button label="Save" @click="saveMemo" :loading="isSaving" />
            </div>
          </div>
        </div>
      </template>
    </Card>
  </aside>
</template>

<script setup lang="ts">
import { marked } from "marked";

const renderedMemo = computed(() => {
  return memo.value ? marked.parse(memo.value) : "";
});

const saveMemo = async () => {
  isSaving.value = true;
  try {
    await api.post(`/conversations/${conversationId}/memo`, {
      memo_text: editableMemo.value,
    });
    memo.value = editableMemo.value;
    isEditing.value = false;
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.memo-panel {
  width: 320px;
  position: sticky;
  top: var(--spacing-4);
}

.memo-content {
  padding: var(--spacing-3);
  background: var(--color-neutral-50);
  border-radius: 8px;
  margin-bottom: var(--spacing-3);
}

.memo-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-3);
}
</style>
```

---

## Common Components

### Header/Navigation

```vue
<template>
  <header class="app-header">
    <div class="header-content">
      <div class="logo-section">
        <router-link to="/">
          <img src="/logo.svg" alt="Gaji" class="logo" />
          <span class="app-name">Gaji</span>
        </router-link>
      </div>

      <nav class="main-nav">
        <router-link to="/scenarios/browse">Explore</router-link>
        <router-link to="/scenarios/create">Create</router-link>
        <router-link to="/conversations">My Conversations</router-link>
      </nav>

      <div class="user-section">
        <InputGroup class="search-input">
          <InputText placeholder="Search..." v-model="searchQuery" />
          <Button icon="pi pi-search" @click="search" />
        </InputGroup>

        <Button
          icon="pi pi-bell"
          severity="secondary"
          :badge="notificationCount"
        />

        <Avatar
          :image="currentUser.avatarUrl"
          :label="currentUser.username[0]"
          @click="toggleUserMenu"
        />
      </div>
    </div>
  </header>
</template>
```

---

## Responsive Design

### Breakpoints (PandaCSS)

```typescript
const breakpoints = {
  sm: "640px", // Mobile landscape
  md: "768px", // Tablet
  lg: "1024px", // Desktop
  xl: "1280px", // Large desktop
  "2xl": "1536px", // Extra large
};
```

### Mobile Adaptations

**Browse Page** (Mobile):

```css
@media (max-width: 768px) {
  .browse-page {
    grid-template-columns: 1fr; /* Stack filter sidebar */
  }

  .filter-sidebar {
    position: static;
    order: 2; /* Move filters below content */
  }

  .scenario-grid-area {
    order: 1;
  }
}
```

**Conversation Page** (Mobile):

```css
@media (max-width: 640px) {
  .conversation-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-2);
  }

  .message-content {
    max-width: 90%; /* Wider bubbles on mobile */
  }
}
```

**Tree Visualization** (Mobile):

```css
@media (max-width: 768px) {
  .tree-nav-controls {
    bottom: var(--spacing-2);
    right: var(--spacing-2);
    scale: 0.8;
  }

  .node-details-panel {
    width: 100%;
    bottom: 0;
    top: auto;
    right: 0;
  }
}
```

---

## Accessibility

### ARIA Labels

```vue
<!-- Buttons -->
<Button
  icon="pi pi-heart"
  aria-label="Like conversation"
  :aria-pressed="isLiked"
/>

<!-- Form Inputs -->
<InputText
  v-model="searchQuery"
  aria-label="Search scenarios"
  aria-describedby="search-hint"
/>
<small id="search-hint">Press Enter to search</small>

<!-- Navigation -->
<nav aria-label="Main navigation">
  <router-link to="/scenarios" aria-current="page">Explore</router-link>
</nav>
```

### Keyboard Navigation

```typescript
// Message input: Enter to send, Shift+Enter for newline
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

// Tree navigation: Arrow keys to move, Enter to select
const handleTreeKeyNav = (event: KeyboardEvent) => {
  switch (event.key) {
    case "ArrowUp":
      focusPreviousNode();
      break;
    case "ArrowDown":
      focusNextNode();
      break;
    case "Enter":
      selectNode();
      break;
  }
};
```

### Focus Management

```vue
<script setup lang="ts">
import { useFocusTrap } from "@vueuse/integrations/useFocusTrap";

// Modal focus trap
const modalRef = ref();
const { activate, deactivate } = useFocusTrap(modalRef);

watch(showModal, (visible) => {
  if (visible) {
    activate();
  } else {
    deactivate();
  }
});
</script>
```

---

## State Management (Pinia)

### User Store

```typescript
// stores/user.ts
import { defineStore } from "pinia";

export const useUserStore = defineStore("user", {
  state: () => ({
    currentUser: null as User | null,
    isAuthenticated: false,
    accessToken: localStorage.getItem("access_token"),
    refreshToken: localStorage.getItem("refresh_token"),
  }),

  actions: {
    async login(email: string, password: string) {
      const response = await api.post("/auth/login", { email, password });
      this.setTokens(response.data.tokens);
      this.currentUser = response.data.user;
      this.isAuthenticated = true;
    },

    async logout() {
      await api.post("/auth/logout", { refresh_token: this.refreshToken });
      this.clearTokens();
      this.currentUser = null;
      this.isAuthenticated = false;
    },

    setTokens(tokens: { access_token: string; refresh_token: string }) {
      this.accessToken = tokens.access_token;
      this.refreshToken = tokens.refresh_token;
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
    },

    clearTokens() {
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    },
  },
});
```

### Scenario Store

```typescript
// stores/scenario.ts
export const useScenarioStore = defineStore("scenario", {
  state: () => ({
    scenarios: [] as Scenario[],
    currentScenario: null as Scenario | null,
    filters: {
      baseStory: null,
      scenarioTypes: [],
      minQuality: 0,
    } as BrowseFilters,
  }),

  actions: {
    async fetchScenarios(page = 0, size = 20) {
      const response = await api.get("/scenarios", {
        params: { page, size, ...this.filters },
      });
      this.scenarios = response.data.content;
      return response.data;
    },

    async createScenario(data: ScenarioCreateRequest) {
      const response = await api.post("/scenarios", data);
      this.scenarios.unshift(response.data);
      return response.data;
    },
  },
});
```

---

## Performance Optimizations

### Lazy Loading Routes

```typescript
// router/index.ts
const routes = [
  {
    path: "/",
    component: () => import("@/views/HomePage.vue"),
  },
  {
    path: "/scenarios/create",
    component: () => import("@/views/ScenarioCreatePage.vue"),
  },
  {
    path: "/conversations/:id",
    component: () => import("@/views/ConversationPage.vue"),
  },
];
```

### Virtual Scrolling (Large Lists)

```vue
<template>
  <VirtualScroller :items="messages" :itemSize="80" class="message-list">
    <template #item="{ item }">
      <MessageBubble :message="item" />
    </template>
  </VirtualScroller>
</template>
```

### Image Optimization

```vue
<template>
  <img
    :src="optimizedImageUrl"
    :srcset="`
      ${imageUrl}?w=400 400w,
      ${imageUrl}?w=800 800w,
      ${imageUrl}?w=1200 1200w
    `"
    sizes="(max-width: 640px) 400px, (max-width: 1024px) 800px, 1200px"
    loading="lazy"
    alt="Scenario cover"
  />
</template>
```

---

## Support & Resources

- **PandaCSS Docs**: https://panda-css.com/
- **PrimeVue Components**: https://primevue.org/
- **Vue 3 Composition API**: https://vuejs.org/guide/extras/composition-api-faq.html
- **D3.js Tree Layout**: https://d3js.org/d3-hierarchy/tree
- **Architecture**: `/docs/architecture.md`
- **API Docs**: `/docs/API_DOCUMENTATION.md`
- **Story Files**: `/docs/stories/`

---

**Last Updated**: 2025-11-13  
**Maintained By**: Gaji Engineering Team
