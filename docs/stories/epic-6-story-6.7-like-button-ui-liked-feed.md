# Story 6.7: Like Button UI & Liked Conversations Feed

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 6 hours

## Description

Create frontend UI for conversation like button with heart animation, optimistic updates, and liked conversations feed page.

## Dependencies

**Blocks**:

- None (completes like feature)

**Requires**:

- Story 6.6: Conversation Like System Backend (like API)
- Story 6.2: User Authentication Frontend (authenticated state)

## Acceptance Criteria

- [ ] Heart icon like button on conversation cards
- [ ] Heart fills red on click with animation
- [ ] Click again to unlike (heart outline)
- [ ] Like count displays next to heart
- [ ] Optimistic UI update on click
- [ ] Rollback if API fails
- [ ] `/liked` route displays liked conversations feed
- [ ] Liked feed paginated (20 per page)
- [ ] Empty state: "No liked conversations yet"
- [ ] Like button visible only when logged in
- [ ] Unit tests >80% coverage

## Technical Notes

**Like Button Component**:

```vue
<template>
  <button
    @click.stop="handleLikeToggle"
    :disabled="isLoading || !isAuthenticated"
    class="like-button"
    :class="{ liked: isLiked, animating: isAnimating }"
    :aria-label="isLiked ? 'Unlike' : 'Like'"
  >
    <svg width="24" height="24" viewBox="0 0 24 24" class="heart-icon">
      <path
        d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
        :fill="isLiked ? '#e63946' : 'none'"
        :stroke="isLiked ? '#e63946' : '#666'"
        stroke-width="2"
      />
    </svg>

    <span class="like-count">{{ displayCount }}</span>
  </button>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";

const props = defineProps<{
  conversationId: string;
  initialLikeCount?: number;
}>();

const emit = defineEmits(["like-change"]);

const authStore = useAuthStore();

const isLiked = ref(false);
const likeCount = ref(props.initialLikeCount || 0);
const isLoading = ref(false);
const isAnimating = ref(false);

const isAuthenticated = computed(() => authStore.isAuthenticated);

const displayCount = computed(() => {
  if (likeCount.value === 0) return "";
  if (likeCount.value >= 1000) {
    return `${(likeCount.value / 1000).toFixed(1)}k`;
  }
  return likeCount.value.toString();
});

onMounted(async () => {
  if (isAuthenticated.value) {
    await checkLikeStatus();
  }
});

const checkLikeStatus = async () => {
  try {
    const response = await api.get(
      `/conversations/${props.conversationId}/liked`
    );
    isLiked.value = response.data.isLiked;
    likeCount.value = response.data.likeCount;
  } catch (error) {
    console.error("Failed to check like status:", error);
  }
};

const handleLikeToggle = async () => {
  if (!isAuthenticated.value) {
    showToast("Please log in to like conversations");
    return;
  }

  // Trigger animation
  isAnimating.value = true;
  setTimeout(() => {
    isAnimating.value = false;
  }, 300);

  // Optimistic update
  const previousLiked = isLiked.value;
  const previousCount = likeCount.value;

  isLiked.value = !isLiked.value;
  likeCount.value = isLiked.value
    ? likeCount.value + 1
    : Math.max(0, likeCount.value - 1);

  isLoading.value = true;

  try {
    const endpoint = isLiked.value
      ? `/conversations/${props.conversationId}/like`
      : `/conversations/${props.conversationId}/unlike`;

    const method = isLiked.value ? "post" : "delete";

    const response = await api[method](endpoint);

    // Update from server response
    isLiked.value = response.data.isLiked;
    likeCount.value = response.data.likeCount;

    emit("like-change", {
      isLiked: isLiked.value,
      likeCount: likeCount.value,
    });
  } catch (error) {
    // Rollback on error
    isLiked.value = previousLiked;
    likeCount.value = previousCount;

    console.error("Failed to toggle like:", error);
    showError("Failed to update like");
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.like-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.like-button:hover:not(:disabled) {
  background: rgba(230, 57, 70, 0.1);
}

.like-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.heart-icon {
  transition: transform 0.2s ease;
}

.like-button.animating .heart-icon {
  animation: heartbeat 0.3s ease;
}

@keyframes heartbeat {
  0%,
  100% {
    transform: scale(1);
  }
  25% {
    transform: scale(1.3);
  }
  50% {
    transform: scale(1.1);
  }
  75% {
    transform: scale(1.2);
  }
}

.like-button.liked .heart-icon {
  filter: drop-shadow(0 0 4px rgba(230, 57, 70, 0.5));
}

.like-count {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  min-width: 20px;
  text-align: left;
}

.like-button.liked .like-count {
  color: #e63946;
}
</style>
```

**Liked Conversations Feed Page**:

```vue
<template>
  <div class="liked-feed-page">
    <div class="page-header">
      <h1>Liked Conversations</h1>
      <p>{{ totalLiked }} conversations you've liked</p>
    </div>

    <div v-if="isLoading" class="loading-state">
      <Spinner /> Loading liked conversations...
    </div>

    <div v-else-if="conversations.length === 0" class="empty-state">
      <HeartOutlineIcon class="empty-icon" />
      <h2>No liked conversations yet</h2>
      <p>Like conversations to save them here for quick access</p>
      <router-link to="/discover" class="btn-primary">
        Discover Conversations
      </router-link>
    </div>

    <div v-else class="conversation-grid">
      <ConversationCard
        v-for="conversation in conversations"
        :key="conversation.id"
        :conversation="conversation"
        @like-change="handleLikeChange(conversation.id, $event)"
      />

      <Pagination
        :currentPage="currentPage"
        :totalPages="totalPages"
        @page-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import api from "@/services/api";
import ConversationCard from "@/components/ConversationCard.vue";

const router = useRouter();
const authStore = useAuthStore();

const conversations = ref([]);
const totalLiked = ref(0);
const currentPage = ref(0);
const totalPages = ref(0);
const isLoading = ref(true);

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push("/login");
    return;
  }

  await loadLikedConversations();
});

const loadLikedConversations = async () => {
  isLoading.value = true;

  try {
    const response = await api.get("/users/me/liked-conversations", {
      params: { page: currentPage.value, size: 20 },
    });

    conversations.value = response.data.content;
    totalLiked.value = response.data.totalElements;
    totalPages.value = response.data.totalPages;
  } catch (error) {
    console.error("Failed to load liked conversations:", error);
    showError("Failed to load liked conversations");
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadLikedConversations();
};

const handleLikeChange = (
  conversationId: string,
  event: { isLiked: boolean }
) => {
  if (!event.isLiked) {
    // Remove from list if unliked
    conversations.value = conversations.value.filter(
      (c) => c.id !== conversationId
    );
    totalLiked.value = Math.max(0, totalLiked.value - 1);
  }
};
</script>

<style scoped>
.liked-feed-page {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 32px;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #666;
  font-size: 16px;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 4rem 2rem;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  width: 80px;
  height: 80px;
  color: #ccc;
  margin-bottom: 1.5rem;
}

.empty-state h2 {
  font-size: 24px;
  margin-bottom: 0.5rem;
  color: #333;
}

.empty-state p {
  color: #666;
  margin-bottom: 2rem;
}

.btn-primary {
  display: inline-block;
  background: #667eea;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #5568d3;
}

.conversation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .conversation-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

**Update ConversationCard to include LikeButton**:

```vue
<template>
  <div class="conversation-card">
    <!-- Existing card content -->
    <div class="card-header">
      <h3>{{ conversation.title }}</h3>
      <LikeButton
        :conversationId="conversation.id"
        :initialLikeCount="conversation.likeCount"
        @like-change="$emit('like-change', $event)"
      />
    </div>

    <p class="description">{{ conversation.description }}</p>

    <div class="card-footer">
      <span class="message-count"
        >{{ conversation.messageCount }} messages</span
      >
      <span class="created-date">{{ formatDate(conversation.createdAt) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from "vue";
import LikeButton from "@/components/LikeButton.vue";

defineProps<{
  conversation: {
    id: string;
    title: string;
    description: string;
    messageCount: number;
    likeCount: number;
    createdAt: string;
  };
}>();

defineEmits(["like-change"]);

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString();
};
</script>

<style scoped>
.conversation-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.conversation-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.card-header h3 {
  font-size: 18px;
  flex: 1;
  margin-right: 1rem;
}

.description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #999;
}
</style>
```

## QA Checklist

### Functional Testing

- [ ] Heart icon appears on conversation cards
- [ ] Click heart fills it red (like)
- [ ] Click again outlines it (unlike)
- [ ] Like count updates on click
- [ ] Liked feed route displays user's liked conversations
- [ ] Empty state shown when no likes
- [ ] Pagination works on liked feed

### Optimistic UI Testing

- [ ] Heart fills immediately on click
- [ ] Like count increments immediately
- [ ] UI reverts if API fails
- [ ] Animation plays on like/unlike
- [ ] Loading state during API call

### Animation Testing

- [ ] Heartbeat animation on click
- [ ] Smooth transition between filled/outline
- [ ] Animation doesn't block interaction
- [ ] Animation works on mobile

### Edge Cases

- [ ] Like button hidden when not logged in
- [ ] Clicking while loading does nothing
- [ ] Network error during like handled
- [ ] Unlike removes from liked feed

### Performance

- [ ] Like feels instant (optimistic update)
- [ ] Animation smooth (60fps)
- [ ] Liked feed loads < 500ms

### Accessibility

- [ ] Like button keyboard accessible
- [ ] Aria-label announces like/unlike
- [ ] Screen reader announces like count changes
- [ ] Focus visible on keyboard navigation

## Estimated Effort

6 hours
