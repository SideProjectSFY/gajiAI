# Story 4.3: Conversation Forking & Branching UI

**Epic**: Epic 4 - Conversation System  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 12 hours

## Description

Enable users to fork conversations to explore alternative dialogue paths, with **scenario modification support** during forking. Users can optionally modify the scenario when forking, allowing them to explore "what if" variations based on the current conversation.

## Dependencies

**Blocks**:

- Epic 5 stories (tree visualization requires fork data structure)

**Requires**:

- Story 4.1: Conversation Data Model & CRUD API (needs conversation schema)
- Story 4.2: Message Streaming & AI Integration (needs message data)

## Acceptance Criteria

### Backend API Enhancement

- [ ] **Fork conversation API** - POST /api/v1/conversations/{id}/fork

  **Authentication**: Required

  **Validation**:

  - Validation 1: Check `conversation.parent_conversation_id IS NULL` (return 403 Forbidden if trying to fork a forked conversation)
  - Validation 2: Check `conversation.has_been_forked = false` (return 409 Conflict if root already forked)
  - Validation 3: If `scenario_modifications` provided, validate min 10 chars per field + at least 1 type filled

  **Request Body**:

  ```json
  {
    "fork_title": "Hermione in Ravenclaw", // REQUIRED
    "scenario_modifications": {
      // OPTIONAL
      "character_changes": "Hermione was sorted into Ravenclaw...",
      "event_alterations": "The Troll incident never happened...",
      "setting_modifications": "" // Can be empty
    }
  }
  ```

  **Message Copy Logic**: Copy `min(6, total_message_count)` most recent messages

  - If original has ≥6 messages → copy last 6 messages
  - If original has <6 messages → copy ALL messages

  **Fork Creation**:

  - Create new conversation with `fork_title`
  - If `scenario_modifications` provided:
    - Create new scenario with original + modifications merged
    - Link new conversation to new scenario
  - Else: link to original scenario
  - Copy messages according to logic above
  - Update parent: set `has_been_forked = true` (atomic)

  **Response**:

  ```json
  {
    "fork_id": "uuid",
    "forked_conversation_id": "uuid",
    "scenario_modified": true, // or false
    "messages_copied": 6
  }
  ```

### UI Components

- [ ] **ForkConversationButton** in conversation header

  - **Only show if**: `conversation.parent_conversation_id IS NULL` (root conversations only)
  - Show "Fork Conversation" button if `conversation.has_been_forked = false`
  - If conversation is a fork: hide button entirely (show badge: "Forked - cannot fork again")

- [ ] **ForkConversationModal** component

  **Modal Structure**:

  - **Section 1: Original Scenario (Read-Only)**

    - Display current scenario information
    - Label: "Original Scenario"
    - Show: scenario title + all 3 types (read-only text areas with gray background)

  - **Section 2: Fork Options**

    - Input: "Fork Title" (required, placeholder: "Give your fork a name...")
    - Toggle: "Modify Scenario" (default: OFF)
    - If toggle ON:
      - Show 3 editable textareas (pre-filled with original content)
      - Character counters with color coding (same as Story 1.2)
      - Validation: min 10 chars per filled field + at least 1 type

  - **Section 3: Message Preview**

    - Info message: "📋 Will copy last {count} messages"
    - Expandable list showing exact messages to be copied
    - Message format: `[{timestamp}] {sender}: {preview...}`

  - **Warning Message**

    - "⚠️ Original conversations can only be forked once"

  - **Action Buttons**
    - Cancel (secondary)
    - Create Fork (primary, disabled if validation fails)

## Technical Implementation

### Component: ForkConversationModal

```vue
<template>
  <Dialog
    v-model:visible="visible"
    modal
    header="Fork Conversation"
    :style="{ width: '50vw' }"
    :breakpoints="{ '768px': '90vw' }"
  >
    <!-- Section 1: Original Scenario (Read-Only) -->
    <div class="section original-scenario">
      <h3>Original Scenario</h3>
      <div class="read-only-fields">
        <div class="field">
          <label>Scenario Title</label>
          <InputText :value="originalScenario.title" readonly disabled />
        </div>

        <div class="field">
          <label>Character Changes</label>
          <Textarea
            :value="originalScenario.character_changes"
            readonly
            disabled
            rows="3"
          />
        </div>

        <div class="field">
          <label>Event Alterations</label>
          <Textarea
            :value="originalScenario.event_alterations"
            readonly
            disabled
            rows="3"
          />
        </div>

        <div class="field">
          <label>Setting Modifications</label>
          <Textarea
            :value="originalScenario.setting_modifications"
            readonly
            disabled
            rows="3"
          />
        </div>
      </div>
    </div>

    <!-- Section 2: Fork Options -->
    <div class="section fork-options">
      <div class="field">
        <label>Fork Title <span class="required">*</span></label>
        <InputText
          v-model="forkTitle"
          placeholder="Give your fork a name..."
          :invalid="forkTitleInvalid"
        />
        <small v-if="forkTitleInvalid" class="error">
          Fork title is required
        </small>
      </div>

      <div class="field">
        <div class="flex align-items-center gap-2">
          <Checkbox v-model="modifyScenario" inputId="modifyScenario" binary />
          <label for="modifyScenario">Modify Scenario</label>
        </div>
      </div>

      <!-- Editable Scenario Fields (if toggled) -->
      <div v-if="modifyScenario" class="scenario-modifications">
        <div class="field">
          <label>Character Changes</label>
          <Textarea
            v-model="scenarioModifications.character_changes"
            rows="4"
            placeholder="Describe character property changes..."
          />
          <CharCounter
            :text="scenarioModifications.character_changes"
            :min-length="10"
          />
        </div>

        <div class="field">
          <label>Event Alterations</label>
          <Textarea
            v-model="scenarioModifications.event_alterations"
            rows="4"
            placeholder="Describe event alterations..."
          />
          <CharCounter
            :text="scenarioModifications.event_alterations"
            :min-length="10"
          />
        </div>

        <div class="field">
          <label>Setting Modifications</label>
          <Textarea
            v-model="scenarioModifications.setting_modifications"
            rows="4"
            placeholder="Describe setting changes..."
          />
          <CharCounter
            :text="scenarioModifications.setting_modifications"
            :min-length="10"
          />
        </div>

        <Message severity="info" :closable="false">
          At least one scenario type must have min 10 characters
        </Message>
      </div>
    </div>

    <!-- Section 3: Message Preview -->
    <div class="section message-preview">
      <h3>Messages to Copy</h3>
      <Message severity="info" :closable="false">
        📋 Will copy last {{ messagesToCopy.length }} messages
      </Message>

      <Accordion>
        <AccordionTab header="Preview Messages">
          <div class="message-list">
            <div
              v-for="message in messagesToCopy"
              :key="message.id"
              class="message-item"
            >
              <span class="message-timestamp">{{
                formatTimestamp(message.created_at)
              }}</span>
              <span class="message-sender">{{ message.sender }}:</span>
              <span class="message-preview">{{
                truncate(message.content, 80)
              }}</span>
            </div>
          </div>
        </AccordionTab>
      </Accordion>
    </div>

    <!-- Warning -->
    <Message severity="warn" :closable="false">
      ⚠️ Original conversations can only be forked once
    </Message>

    <!-- Actions -->
    <template #footer>
      <Button label="Cancel" severity="secondary" @click="visible = false" />
      <Button
        label="Create Fork"
        severity="primary"
        :disabled="!isValid"
        :loading="isCreating"
        @click="handleCreateFork"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";
import Message from "primevue/message";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";
import CharCounter from "@/components/CharCounter.vue";
import api from "@/services/api";

interface Props {
  conversationId: string;
  originalScenario: {
    title: string;
    character_changes: string;
    event_alterations: string;
    setting_modifications: string;
  };
}

const props = defineProps<Props>();
const emit = defineEmits(["close", "forked"]);
const router = useRouter();

const visible = ref(true);
const forkTitle = ref("");
const modifyScenario = ref(false);
const scenarioModifications = ref({
  character_changes: props.originalScenario.character_changes || "",
  event_alterations: props.originalScenario.event_alterations || "",
  setting_modifications: props.originalScenario.setting_modifications || "",
});

const messagesToCopy = ref<Message[]>([]);
const isCreating = ref(false);

const forkTitleInvalid = computed(() => {
  return forkTitle.value.trim().length === 0;
});

const scenarioValid = computed(() => {
  if (!modifyScenario.value) return true;

  const hasCharChanges =
    scenarioModifications.value.character_changes.length >= 10;
  const hasEventAlters =
    scenarioModifications.value.event_alterations.length >= 10;
  const hasSettingMods =
    scenarioModifications.value.setting_modifications.length >= 10;

  return hasCharChanges || hasEventAlters || hasSettingMods;
});

const isValid = computed(() => {
  return !forkTitleInvalid.value && scenarioValid.value;
});

const fetchMessagesToCopy = async () => {
  try {
    const response = await api.get(
      `/api/v1/conversations/${props.conversationId}/messages`,
      {
        params: { limit: 6, order: "desc" },
      }
    );
    messagesToCopy.value = response.data.messages.reverse(); // Show in chronological order
  } catch (error) {
    console.error("Failed to fetch messages:", error);
  }
};

const handleCreateFork = async () => {
  if (!isValid.value) return;

  isCreating.value = true;

  try {
    const payload: any = {
      fork_title: forkTitle.value.trim(),
    };

    if (modifyScenario.value) {
      payload.scenario_modifications = {
        character_changes: scenarioModifications.value.character_changes.trim(),
        event_alterations: scenarioModifications.value.event_alterations.trim(),
        setting_modifications:
          scenarioModifications.value.setting_modifications.trim(),
      };
    }

    const response = await api.post(
      `/api/v1/conversations/${props.conversationId}/fork`,
      payload
    );

    emit("forked", response.data.forked_conversation_id);
    visible.value = false;

    // Navigate to forked conversation
    router.push(`/conversations/${response.data.forked_conversation_id}`);
  } catch (error) {
    console.error("Failed to create fork:", error);
    alert("Failed to create fork. Please try again.");
  } finally {
    isCreating.value = false;
  }
};

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString();
};

const truncate = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
};

onMounted(() => {
  fetchMessagesToCopy();
});
</script>

<style scoped>
.section {
  margin-bottom: 2rem;
}

.section h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 1rem;
}

.read-only-fields .field {
  margin-bottom: 1rem;
}

.read-only-fields label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #6b7280;
}

.read-only-fields :deep(.p-inputtext),
.read-only-fields :deep(.p-inputtextarea) {
  background: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
}

.field {
  margin-bottom: 1.5rem;
}

.field label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.required {
  color: #ef4444;
}

.error {
  color: #ef4444;
  display: block;
  margin-top: 0.25rem;
}

.scenario-modifications {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.message-list {
  max-height: 300px;
  overflow-y: auto;
}

.message-item {
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
}

.message-timestamp {
  color: #6b7280;
  margin-right: 0.5rem;
}

.message-sender {
  font-weight: 600;
  margin-right: 0.5rem;
}

.message-preview {
  color: #374151;
}
</style>
```

## QA Checklist

### Fork Business Logic

- [ ] ROOT conversation can be forked successfully
- [ ] Forked conversation returns 403 when attempting to fork
- [ ] Message copy works for <6 messages (copies all)
- [ ] Message copy works for ≥6 messages (copies last 6)
- [ ] Parent `has_been_forked` flag updates correctly

### Scenario Modification

- [ ] Fork without scenario modification uses original scenario
- [ ] Fork with scenario modification creates new scenario
- [ ] Validation: min 10 chars per field enforced
- [ ] Validation: at least 1 type required when modifying
- [ ] Character counters show correct colors (Green ≥10, Red 1-9, Gray 0)

### UI/UX Testing

- [ ] Fork button visible ONLY on ROOT conversations
- [ ] Fork button hidden on forked conversations
- [ ] Modal shows original scenario (read-only)
- [ ] "Modify Scenario" toggle works correctly
- [ ] Fork title validation prevents empty submission
- [ ] Message preview shows correct count and content
- [ ] Create Fork button disabled until validation passes

### Edge Cases

- [ ] Fork with 0 messages fails gracefully
- [ ] Fork with 1 message copies 1
- [ ] Fork with 6 messages copies 6
- [ ] Concurrent fork attempts (only one succeeds)
- [ ] Fork title with special characters handled correctly

### Security

- [ ] Only authenticated users can fork
- [ ] Forked conversation maintains permissions
- [ ] Scenario modifications validated server-side

### Performance

- [ ] Fork operation completes in <500ms
- [ ] Message preview loads quickly
- [ ] Modal opens/closes smoothly

## Estimated Effort

12 hours

---

**Story Owner**: Frontend + Backend Lead

**Key Enhancement**: Scenario modification during fork allows users to explore "what if" variations based on existing conversations
