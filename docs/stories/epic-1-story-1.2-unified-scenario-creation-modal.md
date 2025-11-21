# Story 1.2: Unified Scenario Creation Modal

**Epic**: Epic 1 - What If Scenario Foundation  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 12 hours

## Description

Build a **single modal component** for creating What If scenarios with real-time validation, character counters, and unified form handling for all three scenario types (Character Changes, Event Alterations, Setting Modifications).

**Key Design Principle**: Simple, single-step modal (not a multi-step wizard) with optional fields and strict validation rules.

## Dependencies

**Blocks**:

- Story 3.1: Scenario Browse UI (needs scenarios to display)

**Requires**:

- Story 0.4: Vue.js Frontend Project Setup
- Story 1.1: Scenario Data Model & API

## Acceptance Criteria

### Core Modal Structure

- [ ] **PrimeVue Dialog component** for modal container
- [ ] **Triggered from Book Detail page** via `[+ Create Scenario]` button
- [ ] **Single unified form** (not tabs or wizard steps)
- [ ] **Three optional text fields** for scenario types:
  - Character Changes (optional)
  - Event Alterations (optional)
  - Setting Modifications (optional)
- [ ] **Required scenario title** field (max 100 characters)
- [ ] **Real-time character counters** for each field
- [ ] **Submit button** enabled only when validation passes

### Validation Rules

- [ ] **At least ONE of three scenario types must be filled**
- [ ] **Each filled field must have 10+ characters minimum**
- [ ] Empty fields are allowed (optional)
- [ ] Fields with < 10 characters show error state (red border + counter)
- [ ] Submit button disabled until: `title.trim() && hasAtLeastOneValidType()`
- [ ] **Error message**: "Please provide at least one scenario type with 10+ characters"

### Character Counter Implementation

- [ ] **Real-time counter** for each textarea: `{current_length}/10 chars`
- [ ] **Color coding**:
  - ✅ Green: ≥ 10 characters (valid)
  - ❌ Red: 1-9 characters (invalid)
  - ⚪ Gray: 0 characters (neutral, optional)
- [ ] Counter updates on every keystroke
- [ ] Visual feedback instant (no debounce)

### Form Fields

**Scenario Title** (Required):

```
[Scenario Title________________________] (0/100)
```

**Character Changes** (Optional):

```
[Character property changes...]
[Hermione sorted into Slytherin]
15/10 chars ✓
```

**Event Alterations** (Optional):

```
[Event outcome changes...]
[Troll incident: saved by Draco instead]
40/10 chars ✓
```

**Setting Modifications** (Optional):

```
[Setting/location/time changes...]
[                                    ]
0/10 chars (optional)
```

### API Integration

- [ ] POST /api/v1/scenarios endpoint integration
- [ ] Request payload:
  ```json
  {
    "book_id": "uuid",
    "scenario_title": "Hermione in Slytherin",
    "character_changes": "Hermione sorted into Slytherin instead of Gryffindor",
    "event_alterations": "Troll incident: saved by Draco and Pansy",
    "setting_modifications": ""
  }
  ```
- [ ] Success response: redirect to Scenario Detail page
- [ ] Error handling: display API errors in toast notification
- [ ] Loading state: disable submit button, show spinner

### UX Features

- [ ] **Pre-filled book context** (passed from Book Detail page)
- [ ] **Modal close on Escape key** with confirmation if form dirty
- [ ] **Focus management**: auto-focus title field on modal open
- [ ] **Mobile responsive**: fullscreen modal on < 768px width
- [ ] **Keyboard shortcuts**: Cmd+Enter / Ctrl+Enter to submit
- [ ] **Form reset** after successful submission

## Technical Implementation

### Component Structure

```vue
<template>
  <Dialog
    v-model:visible="showModal"
    modal
    :header="modalTitle"
    :style="{ width: '90vw', maxWidth: '600px' }"
    :closable="true"
    @hide="handleModalClose"
  >
    <form @submit.prevent="handleSubmit" class="scenario-creation-form">
      <!-- Scenario Title (Required) -->
      <div class="form-group">
        <label for="scenario-title" class="required">Scenario Title</label>
        <InputText
          id="scenario-title"
          v-model="form.title"
          placeholder="e.g., Hermione in Slytherin"
          maxlength="100"
          required
          :class="{ 'p-invalid': !isTitleValid && form.title.length > 0 }"
        />
        <CharCounter :text="form.title" :max="100" label="title" />
      </div>

      <!-- Character Changes (Optional) -->
      <div class="form-group">
        <label for="character-changes">
          👤 Character Changes
          <span class="optional">(Optional)</span>
        </label>
        <Textarea
          id="character-changes"
          v-model="form.character_changes"
          placeholder="e.g., Hermione sorted into Slytherin instead of Gryffindor"
          rows="3"
          :class="{
            'p-invalid':
              !isCharacterChangesValid && form.character_changes.length > 0,
          }"
        />
        <CharCounter
          :text="form.character_changes"
          :min="10"
          label="character"
        />
      </div>

      <!-- Event Alterations (Optional) -->
      <div class="form-group">
        <label for="event-alterations">
          🎬 Event Alterations
          <span class="optional">(Optional)</span>
        </label>
        <Textarea
          id="event-alterations"
          v-model="form.event_alterations"
          placeholder="e.g., Troll incident: saved by Draco instead of Harry"
          rows="3"
          :class="{
            'p-invalid':
              !isEventAlterationsValid && form.event_alterations.length > 0,
          }"
        />
        <CharCounter :text="form.event_alterations" :min="10" label="event" />
      </div>

      <!-- Setting Modifications (Optional) -->
      <div class="form-group">
        <label for="setting-modifications">
          🌍 Setting Modifications
          <span class="optional">(Optional)</span>
        </label>
        <Textarea
          id="setting-modifications"
          v-model="form.setting_modifications"
          placeholder="e.g., Set in modern-day Seoul instead of 1990s Britain"
          rows="3"
          :class="{
            'p-invalid':
              !isSettingModificationsValid &&
              form.setting_modifications.length > 0,
          }"
        />
        <CharCounter
          :text="form.setting_modifications"
          :min="10"
          label="setting"
        />
      </div>

      <!-- Validation Error Message -->
      <Message v-if="showValidationError" severity="error" :closable="false">
        Please provide at least one scenario type with 10+ characters
      </Message>

      <!-- Submit Button -->
      <div class="form-actions">
        <Button
          label="Cancel"
          severity="secondary"
          @click="handleCancel"
          :disabled="isSubmitting"
        />
        <Button
          type="submit"
          label="Create Scenario"
          :disabled="!isFormValid"
          :loading="isSubmitting"
        />
      </div>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Button from "primevue/button";
import Message from "primevue/message";
import CharCounter from "@/components/CharCounter.vue";
import api from "@/services/api";
import { useToast } from "primevue/usetoast";

interface ScenarioForm {
  title: string;
  character_changes: string;
  event_alterations: string;
  setting_modifications: string;
}

const props = defineProps<{
  bookId: string;
  bookTitle: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "created", scenarioId: string): void;
}>();

const router = useRouter();
const toast = useToast();

const showModal = ref(true);
const isSubmitting = ref(false);

const form = ref<ScenarioForm>({
  title: "",
  character_changes: "",
  event_alterations: "",
  setting_modifications: "",
});

// Character count validation helpers
const MIN_CHARS = 10;

const isTitleValid = computed(() => form.value.title.trim().length > 0);

const isCharacterChangesValid = computed(() => {
  const length = form.value.character_changes.trim().length;
  return length === 0 || length >= MIN_CHARS;
});

const isEventAlterationsValid = computed(() => {
  const length = form.value.event_alterations.trim().length;
  return length === 0 || length >= MIN_CHARS;
});

const isSettingModificationsValid = computed(() => {
  const length = form.value.setting_modifications.trim().length;
  return length === 0 || length >= MIN_CHARS;
});

// Check if at least one scenario type has valid content (≥10 chars)
const hasAtLeastOneValidType = computed(() => {
  return (
    form.value.character_changes.trim().length >= MIN_CHARS ||
    form.value.event_alterations.trim().length >= MIN_CHARS ||
    form.value.setting_modifications.trim().length >= MIN_CHARS
  );
});

// Overall form validation
const isFormValid = computed(() => {
  return (
    isTitleValid.value &&
    isCharacterChangesValid.value &&
    isEventAlterationsValid.value &&
    isSettingModificationsValid.value &&
    hasAtLeastOneValidType.value
  );
});

const showValidationError = computed(() => {
  // Show error if user has typed something but validation fails
  const hasTyped =
    form.value.character_changes.length > 0 ||
    form.value.event_alterations.length > 0 ||
    form.value.setting_modifications.length > 0;

  return hasTyped && !hasAtLeastOneValidType.value;
});

const modalTitle = computed(() => `Create Scenario for ${props.bookTitle}`);

const handleSubmit = async () => {
  if (!isFormValid.value) return;

  isSubmitting.value = true;

  try {
    const response = await api.post("/api/v1/scenarios", {
      book_id: props.bookId,
      scenario_title: form.value.title.trim(),
      character_changes: form.value.character_changes.trim() || null,
      event_alterations: form.value.event_alterations.trim() || null,
      setting_modifications: form.value.setting_modifications.trim() || null,
    });

    const scenarioId = response.data.id;

    toast.add({
      severity: "success",
      summary: "Scenario Created!",
      detail:
        "Your What If scenario is ready. Start a conversation to explore it.",
      life: 3000,
    });

    emit("created", scenarioId);
    router.push(`/books/${props.bookId}/scenarios/${scenarioId}`);
  } catch (error: any) {
    console.error("Failed to create scenario:", error);

    toast.add({
      severity: "error",
      summary: "Creation Failed",
      detail:
        error.response?.data?.message ||
        "Failed to create scenario. Please try again.",
      life: 5000,
    });
  } finally {
    isSubmitting.value = false;
  }
};

const handleCancel = () => {
  if (isFormDirty.value) {
    const confirmed = confirm("Discard scenario creation?");
    if (!confirmed) return;
  }

  showModal.value = false;
  emit("close");
};

const handleModalClose = () => {
  emit("close");
};

const isFormDirty = computed(() => {
  return (
    form.value.title.length > 0 ||
    form.value.character_changes.length > 0 ||
    form.value.event_alterations.length > 0 ||
    form.value.setting_modifications.length > 0
  );
});

// Keyboard shortcut: Cmd/Ctrl + Enter to submit
const handleKeyDown = (event: KeyboardEvent) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    if (isFormValid.value) {
      handleSubmit();
    }
  }
};

onMounted(() => {
  document.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeyDown);
});
</script>

<style scoped>
.scenario-creation-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  font-size: 14px;
  color: #374151;
}

.form-group label.required::after {
  content: " *";
  color: #ef4444;
}

.form-group .optional {
  font-weight: 400;
  font-size: 12px;
  color: #9ca3af;
  margin-left: 0.5rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
}

/* Mobile responsive */
@media (max-width: 767px) {
  .form-actions {
    flex-direction: column-reverse;
  }

  .form-actions button {
    width: 100%;
  }
}
</style>
```

### CharCounter Component

```vue
<template>
  <div class="char-counter" :class="statusClass">
    <span v-if="max">{{ length }}/{{ max }} {{ label }}</span>
    <span v-else-if="min">
      {{ length }}/{{ min }} chars
      <span v-if="length >= min" class="check-icon">✓</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  text: string;
  min?: number;
  max?: number;
  label?: string;
}>();

const length = computed(() => (props.text || "").length);

const statusClass = computed(() => {
  if (props.max) {
    // Max-based validation (for title)
    return length.value > props.max ? "over-limit" : "neutral";
  }

  if (props.min) {
    // Min-based validation (for scenario types)
    if (length.value === 0) return "neutral";
    return length.value >= props.min ? "valid" : "invalid";
  }

  return "neutral";
});
</script>

<style scoped>
.char-counter {
  font-size: 13px;
  font-weight: 500;
  text-align: right;
  transition: color 0.2s ease;
}

.char-counter.valid {
  color: #10b981; /* Green */
}

.char-counter.invalid {
  color: #ef4444; /* Red */
}

.char-counter.neutral {
  color: #6b7280; /* Gray */
}

.char-counter.over-limit {
  color: #ef4444; /* Red */
}

.check-icon {
  margin-left: 0.25rem;
  color: #10b981;
}
</style>
```

## QA Checklist

### Validation Testing

- [ ] **Empty form**: Submit button disabled
- [ ] **Title only**: Submit button disabled (needs at least 1 type)
- [ ] **Title + one valid type (≥10 chars)**: Submit enabled ✅
- [ ] **Title + one short type (<10 chars)**: Submit disabled, red border + counter
- [ ] **Title + multiple types mixed**: Only valid ones count toward "at least one"
- [ ] **All fields empty**: No error message shown
- [ ] **Typed but invalid**: Error message appears below form

### Character Counter Testing

- [ ] Counter updates on every keystroke
- [ ] **0 characters**: Gray counter, neutral state
- [ ] **1-9 characters**: Red counter, invalid state
- [ ] **10+ characters**: Green counter with ✓, valid state
- [ ] Title counter shows X/100 format
- [ ] Scenario type counters show X/10 format

### Form Interaction Testing

- [ ] Modal opens from Book Detail `[+ Create Scenario]` button
- [ ] Modal closes on Escape key (with dirty check)
- [ ] Auto-focus on title field when modal opens
- [ ] Cmd+Enter / Ctrl+Enter submits form (if valid)
- [ ] Cancel button shows confirmation if form dirty
- [ ] Cancel button closes modal immediately if form pristine

### API Integration Testing

- [ ] Success: Creates scenario and redirects to Scenario Detail page
- [ ] Success: Shows toast notification "Scenario Created!"
- [ ] Error: Displays API error message in toast
- [ ] Loading: Submit button shows spinner and is disabled
- [ ] Network error: Shows "Failed to create scenario" toast

### Mobile Responsive Testing

- [ ] Modal fullscreen on < 768px width
- [ ] Form fields stack vertically on mobile
- [ ] Action buttons stack vertically (Cancel on top, Submit on bottom)
- [ ] Textarea height adjusts for mobile keyboards
- [ ] No horizontal scroll on mobile

### Accessibility Testing

- [ ] All form fields have proper labels
- [ ] Required field indicator (asterisk) visible
- [ ] Optional field indicator visible
- [ ] Error messages announced by screen readers
- [ ] Keyboard navigation through all fields
- [ ] Focus trap within modal
- [ ] Escape key closes modal

### Performance Testing

- [ ] Character counter updates < 10ms (no debounce)
- [ ] Form validation computation < 5ms
- [ ] Modal open animation smooth (60fps)
- [ ] Form submission < 500ms (network dependent)

## Definition of Done

- [ ] Component built with PrimeVue Dialog
- [ ] All three scenario types implemented as optional fields
- [ ] Real-time character counters with color coding
- [ ] Validation enforces min 10 chars + at least 1 type rule
- [ ] API integration successful (POST /api/v1/scenarios)
- [ ] Mobile responsive (fullscreen on < 768px)
- [ ] Keyboard shortcuts working (Escape, Cmd+Enter)
- [ ] Unit tests >80% coverage
- [ ] E2E test: open modal → fill form → submit → redirect
- [ ] Accessibility audit passing (WCAG 2.1 AA)

## Estimated Effort

12 hours (consolidates Stories 1.2, 1.3, 1.4 into single unified implementation)

---

**Story Owner**: Frontend Lead

**Replaces**: Stories 1.2 (Character Property Change UI), 1.3 (Event Alteration UI), 1.4 (Setting Modification UI)

**Key Change**: Single modal replaces multi-step wizard, simplifying UX while enforcing quality through validation
