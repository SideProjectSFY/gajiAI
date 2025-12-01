# Story 3.5: Scenario Forking UI & Meta-Fork Creation Flow

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.5
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Create Vue.js UI for forking scenarios with parameter addition workflow, fork preview, and visual representation of scenario lineage.

## Dependencies

**Blocks**:

- None (enhances user experience)

**Requires**:

- Story 3.1: Scenario Browse UI (displays scenarios to fork)
- Story 3.2: Scenario Forking Backend (fork API)

## Acceptance Criteria

- [ ] "Fork Scenario" button on scenario detail page
- [ ] `ForkScenarioModal.vue` component with two-step workflow: 1) Review parent scenario, 2) Add new parameters
- [ ] Parameter addition form inherits parent's scenario_type and shows merged preview
- [ ] Fork lineage breadcrumb shows: Root → Parent → New Fork
- [ ] Real-time preview: "What if [combined parameters]?"
- [ ] Form validation: New parameters must differ from parent
- [ ] Submit calls POST /api/scenarios/{id}/fork
- [ ] Success redirects to new forked scenario detail page
- [ ] Fork count badge updates on parent scenario card
- [ ] Toast notification: "Scenario forked! Explore your meta-timeline."
- [ ] Unit tests >80% coverage

## Technical Notes

**Fork Modal Component**:

```vue
<template>
  <div class="fork-scenario-modal" v-if="isOpen">
    <div class="modal-overlay" @click="close"></div>

    <div class="modal-content">
      <div class="modal-header">
        <h2>Fork Scenario</h2>
        <button @click="close" class="close-btn">✕</button>
      </div>

      <!-- Step 1: Review Parent -->
      <div v-if="step === 1" class="step-review">
        <h3>Parent Scenario</h3>
        <div class="parent-scenario-card">
          <p class="base-story">{{ parentScenario.base_story }}</p>
          <p class="scenario-preview">{{ parentPreview }}</p>
          <div class="parameters">
            <h4>Current Parameters:</h4>
            <ul>
              <li v-for="(value, key) in parentScenario.parameters" :key="key">
                <strong>{{ key }}:</strong> {{ value }}
              </li>
            </ul>
          </div>
        </div>

        <div class="fork-explanation">
          <p>
            Forking creates a <strong>meta-scenario</strong> that combines the
            parent's parameters with your new additions. This allows unlimited
            creative branching!
          </p>
          <p class="example">
            Example: "Hermione in Slytherin" → "Hermione in Slytherin AND Head
            Girl"
          </p>
        </div>

        <button @click="step = 2" class="btn-primary">
          Add New Parameters →
        </button>
      </div>

      <!-- Step 2: Add New Parameters -->
      <div v-if="step === 2" class="step-add-params">
        <h3>Add New Parameters</h3>

        <div class="fork-lineage">
          <span class="breadcrumb">
            {{ rootScenarioName }} → {{ parentScenario.base_story }} →
            <strong>Your Fork</strong>
          </span>
        </div>

        <form @submit.prevent="handleSubmit">
          <!-- CHARACTER_CHANGE specific -->
          <div
            v-if="parentScenario.scenario_type === 'CHARACTER_CHANGE'"
            class="form-group"
          >
            <label>Additional Character Property</label>
            <input
              v-model="newParams.additional_property"
              placeholder="e.g., Head Girl, Quidditch Captain"
              required
            />
            <p class="hint">This will be combined with existing properties</p>
          </div>

          <!-- EVENT_ALTERATION specific -->
          <div
            v-if="parentScenario.scenario_type === 'EVENT_ALTERATION'"
            class="form-group"
          >
            <label>Additional Event Modification</label>
            <textarea
              v-model="newParams.additional_event"
              placeholder="e.g., And Ned Stark becomes King in the North"
              rows="3"
              required
            />
          </div>

          <!-- SETTING_MODIFICATION specific -->
          <div
            v-if="parentScenario.scenario_type === 'SETTING_MODIFICATION'"
            class="form-group"
          >
            <label>Additional Setting Change</label>
            <input
              v-model="newParams.additional_setting"
              placeholder="e.g., With advanced AI technology"
              required
            />
          </div>

          <div class="preview-panel">
            <h4>Fork Preview</h4>
            <p class="merged-preview">{{ mergedPreview }}</p>
          </div>

          <div class="modal-actions">
            <button type="button" @click="step = 1" class="btn-secondary">
              ← Back
            </button>
            <button
              type="submit"
              :disabled="!canSubmit || isSubmitting"
              class="btn-primary"
            >
              {{ isSubmitting ? "Creating Fork..." : "Create Fork" }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";

const props = defineProps(["parentScenario", "isOpen"]);
const emit = defineEmits(["close", "forked"]);
const router = useRouter();

const step = ref(1);
const isSubmitting = ref(false);
const newParams = ref({
  additional_property: "",
  additional_event: "",
  additional_setting: "",
});

const parentPreview = computed(() => {
  const { scenario_type, parameters, base_story } = props.parentScenario;

  if (scenario_type === "CHARACTER_CHANGE") {
    return `${parameters.character} is ${parameters.new_property} instead of ${parameters.original_property}`;
  } else if (scenario_type === "EVENT_ALTERATION") {
    return `${parameters.event_name} had outcome: ${parameters.altered_outcome}`;
  } else {
    return `${base_story} takes place in ${parameters.new_setting}`;
  }
});

const mergedPreview = computed(() => {
  const { scenario_type, parameters } = props.parentScenario;

  if (scenario_type === "CHARACTER_CHANGE") {
    const additional = newParams.value.additional_property;
    if (!additional) return parentPreview.value;
    return `${parameters.character} is ${parameters.new_property} AND ${additional}`;
  } else if (scenario_type === "EVENT_ALTERATION") {
    const additional = newParams.value.additional_event;
    if (!additional) return parentPreview.value;
    return `${parentPreview.value} AND ${additional}`;
  } else {
    const additional = newParams.value.additional_setting;
    if (!additional) return parentPreview.value;
    return `${parentPreview.value} with ${additional}`;
  }
});

const canSubmit = computed(() => {
  const { scenario_type } = props.parentScenario;
  if (scenario_type === "CHARACTER_CHANGE") {
    return newParams.value.additional_property.trim().length > 0;
  } else if (scenario_type === "EVENT_ALTERATION") {
    return newParams.value.additional_event.trim().length > 0;
  } else {
    return newParams.value.additional_setting.trim().length > 0;
  }
});

const handleSubmit = async () => {
  isSubmitting.value = true;

  try {
    const response = await api.post(
      `/scenarios/${props.parentScenario.id}/fork`,
      {
        parameters: newParams.value,
      }
    );

    emit("forked", response.data);
    emit("close");

    // Show success toast
    showToast("Scenario forked! Explore your meta-timeline.");

    // Navigate to new forked scenario
    router.push(`/scenarios/${response.data.id}`);
  } catch (error) {
    const errorMsg = error.response?.data?.message || "Failed to fork scenario";
    showError(errorMsg);
  } finally {
    isSubmitting.value = false;
  }
};

const close = () => {
  step.value = 1;
  newParams.value = {
    additional_property: "",
    additional_event: "",
    additional_setting: "",
  };
  emit("close");
};
</script>

<style scoped>
.fork-scenario-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.parent-scenario-card {
  background: #f5f5f5;
  padding: 1.5rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.fork-lineage {
  background: #e3f2fd;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.preview-panel {
  background: #fff3e0;
  padding: 1rem;
  border-radius: 6px;
  margin: 1rem 0;
}

.merged-preview {
  font-size: 1.1rem;
  font-weight: 500;
  color: #e65100;
}
</style>
```

## QA Checklist

### Functional Testing

- [ ] Fork button appears on scenario detail page
- [ ] Modal opens with parent scenario review (Step 1)
- [ ] Step 2 shows parameter addition form for correct scenario_type
- [ ] Fork preview updates in real-time as user types
- [ ] Submit creates fork and redirects to new scenario
- [ ] Parent scenario's fork_count increments after fork
- [ ] Toast notification appears on success

### UI/UX Testing

- [ ] Modal responsive on mobile/tablet/desktop
- [ ] Two-step workflow clear and intuitive
- [ ] Fork lineage breadcrumb shows hierarchy correctly
- [ ] Preview panel highlights combined parameters
- [ ] Loading state during fork creation
- [ ] Error messages display clearly

### Validation Testing

- [ ] Empty new parameter prevents submission
- [ ] Identical parameter to parent rejected (backend validation)
- [ ] Submit button disabled when form invalid
- [ ] Modal closes and resets state after submission

### Performance

- [ ] Modal opens < 100ms
- [ ] Preview computation < 10ms
- [ ] Fork submission < 500ms
- [ ] No memory leaks on modal close

### Accessibility

- [ ] Modal keyboard navigable (Tab, Esc to close)
- [ ] Form inputs have proper labels
- [ ] Preview announced to screen readers
- [ ] Focus trapped in modal when open

## Estimated Effort

8 hours
