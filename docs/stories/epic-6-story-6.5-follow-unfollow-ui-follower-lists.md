# Story 6.5: Follow/Unfollow UI & Follower Lists

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 6 hours

## Description

Create frontend UI for follow/unfollow button with optimistic updates, follower/following lists with pagination, and mutual follow indicator.

## Dependencies

**Blocks**:

- None (completes follow feature)

**Requires**:

- Story 6.4: Follow/Follower System Backend (follow API)
- Story 6.3: User Profile Page (displays follow button)

## Acceptance Criteria

- [ ] Follow button on user profile page (not on own profile)
- [ ] Button states: "Follow", "Following" (with mutual badge if mutual)
- [ ] Click "Follow" → Optimistic UI update → API call
- [ ] Click "Following" → Confirmation modal: "Unfollow @username?" → API call
- [ ] Follower/following count updates in real-time
- [ ] `/profile/:username/followers` route displays follower list
- [ ] `/profile/:username/following` route displays following list
- [ ] Lists paginated (20 per page)
- [ ] Each list item: avatar, username, follow status, follow/unfollow button
- [ ] Mutual follow badge shown with "↔" icon
- [ ] Empty state: "No followers yet" / "Not following anyone yet"
- [ ] Unit tests >80% coverage

## Technical Notes

**Follow Button Component**:

```vue
<template>
  <div class="follow-button-wrapper">
    <button
      v-if="!isFollowing"
      @click="handleFollow"
      :disabled="isLoading"
      class="btn-follow"
    >
      {{ isLoading ? "Following..." : "Follow" }}
    </button>

    <button
      v-else
      @click="showUnfollowModal = true"
      :disabled="isLoading"
      class="btn-following"
    >
      <span v-if="isMutual" class="mutual-badge">↔</span>
      Following
    </button>

    <!-- Unfollow Confirmation Modal -->
    <Modal v-if="showUnfollowModal" @close="showUnfollowModal = false">
      <h3>Unfollow @{{ username }}?</h3>
      <p>You will no longer see their scenarios in your feed.</p>
      <div class="modal-actions">
        <button @click="handleUnfollow" class="btn-danger">Unfollow</button>
        <button @click="showUnfollowModal = false" class="btn-secondary">
          Cancel
        </button>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import api from "@/services/api";

const props = defineProps<{
  userId: string;
  username: string;
}>();

const emit = defineEmits(["follow-change"]);

const isFollowing = ref(false);
const isMutual = ref(false);
const isLoading = ref(false);
const showUnfollowModal = ref(false);

onMounted(async () => {
  await checkFollowStatus();
});

const checkFollowStatus = async () => {
  try {
    const response = await api.get(`/users/${props.userId}/is-following`);
    isFollowing.value = response.data.isFollowing;
    isMutual.value = response.data.isMutual;
  } catch (error) {
    console.error("Failed to check follow status:", error);
  }
};

const handleFollow = async () => {
  // Optimistic update
  isFollowing.value = true;
  isLoading.value = true;

  try {
    const response = await api.post(`/users/${props.userId}/follow`);

    // Update from server response
    isFollowing.value = response.data.isFollowing;
    isMutual.value = response.data.isMutual;

    emit("follow-change", {
      isFollowing: true,
      followerCount: response.data.followerCount,
    });

    showToast(`You are now following @${props.username}`);
  } catch (error) {
    // Rollback on error
    isFollowing.value = false;
    console.error("Failed to follow user:", error);
    showError("Failed to follow user");
  } finally {
    isLoading.value = false;
  }
};

const handleUnfollow = async () => {
  showUnfollowModal.value = false;

  // Optimistic update
  isFollowing.value = false;
  isMutual.value = false;
  isLoading.value = true;

  try {
    const response = await api.delete(`/users/${props.userId}/unfollow`);

    emit("follow-change", {
      isFollowing: false,
      followerCount: response.data.followerCount,
    });

    showToast(`Unfollowed @${props.username}`);
  } catch (error) {
    // Rollback on error
    isFollowing.value = true;
    console.error("Failed to unfollow user:", error);
    showError("Failed to unfollow user");
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.btn-follow {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-follow:hover:not(:disabled) {
  background: #5568d3;
}

.btn-following {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 0.5rem 1.5rem;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-following:hover:not(:disabled) {
  background: #f5f5f5;
}

.mutual-badge {
  margin-right: 0.5rem;
  font-size: 14px;
}

.btn-follow:disabled,
.btn-following:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
```

**Follower List Page**:

```vue
<template>
  <div class="follower-list-page">
    <div class="page-header">
      <h1>{{ username }}'s Followers</h1>
      <p>{{ totalFollowers }} followers</p>
    </div>

    <div v-if="isLoading" class="loading-state">
      <Spinner /> Loading followers...
    </div>

    <div v-else-if="followers.length === 0" class="empty-state">
      <EmptyIcon />
      <p>No followers yet</p>
    </div>

    <div v-else class="user-list">
      <div v-for="user in followers" :key="user.id" class="user-item">
        <router-link :to="`/profile/${user.username}`" class="user-info">
          <img
            :src="user.avatarUrl || '/default-avatar.png'"
            alt="Avatar"
            class="avatar"
          />
          <div>
            <h3>{{ user.username }}</h3>
            <p class="bio">{{ user.bio || "No bio" }}</p>
          </div>
        </router-link>

        <FollowButton
          v-if="user.id !== currentUserId"
          :userId="user.id"
          :username="user.username"
        />
      </div>

      <Pagination
        :currentPage="currentPage"
        :totalPages="totalPages"
        @page-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";
import FollowButton from "@/components/FollowButton.vue";

const route = useRoute();
const authStore = useAuthStore();

const username = ref(route.params.username);
const followers = ref([]);
const totalFollowers = ref(0);
const currentPage = ref(0);
const totalPages = ref(0);
const isLoading = ref(true);

const currentUserId = computed(() => authStore.currentUser?.id);

onMounted(async () => {
  await loadFollowers();
});

const loadFollowers = async () => {
  isLoading.value = true;

  try {
    const response = await api.get(`/users/${username.value}/followers`, {
      params: { page: currentPage.value, size: 20 },
    });

    followers.value = response.data.content;
    totalFollowers.value = response.data.totalElements;
    totalPages.value = response.data.totalPages;
  } catch (error) {
    console.error("Failed to load followers:", error);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadFollowers();
};
</script>

<style scoped>
.follower-list-page {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 28px;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #666;
}

.user-list {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.user-item:last-child {
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-decoration: none;
  color: inherit;
  flex: 1;
}

.user-info:hover h3 {
  color: #667eea;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}

.user-info h3 {
  font-size: 16px;
  margin-bottom: 0.25rem;
}

.bio {
  font-size: 14px;
  color: #666;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #999;
}
</style>
```

**Following List Page** (Similar structure to Follower List):

```vue
<template>
  <div class="following-list-page">
    <div class="page-header">
      <h1>{{ username }} is Following</h1>
      <p>{{ totalFollowing }} following</p>
    </div>

    <div v-if="isLoading" class="loading-state"><Spinner /> Loading...</div>

    <div v-else-if="following.length === 0" class="empty-state">
      <EmptyIcon />
      <p>Not following anyone yet</p>
    </div>

    <div v-else class="user-list">
      <div v-for="user in following" :key="user.id" class="user-item">
        <router-link :to="`/profile/${user.username}`" class="user-info">
          <img
            :src="user.avatarUrl || '/default-avatar.png'"
            alt="Avatar"
            class="avatar"
          />
          <div>
            <h3>{{ user.username }}</h3>
            <p class="bio">{{ user.bio || "No bio" }}</p>
          </div>
        </router-link>

        <FollowButton
          v-if="user.id !== currentUserId"
          :userId="user.id"
          :username="user.username"
        />
      </div>

      <Pagination
        :currentPage="currentPage"
        :totalPages="totalPages"
        @page-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";
import FollowButton from "@/components/FollowButton.vue";

const route = useRoute();
const authStore = useAuthStore();

const username = ref(route.params.username);
const following = ref([]);
const totalFollowing = ref(0);
const currentPage = ref(0);
const totalPages = ref(0);
const isLoading = ref(true);

const currentUserId = computed(() => authStore.currentUser?.id);

onMounted(async () => {
  await loadFollowing();
});

const loadFollowing = async () => {
  isLoading.value = true;

  try {
    const response = await api.get(`/users/${username.value}/following`, {
      params: { page: currentPage.value, size: 20 },
    });

    following.value = response.data.content;
    totalFollowing.value = response.data.totalElements;
    totalPages.value = response.data.totalPages;
  } catch (error) {
    console.error("Failed to load following:", error);
  } finally {
    isLoading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadFollowing();
};
</script>
```

## QA Checklist

### Functional Testing

- [ ] Follow button appears on other users' profiles
- [ ] Follow button hidden on own profile
- [ ] Click "Follow" triggers optimistic update
- [ ] Click "Following" shows unfollow confirmation
- [ ] Follower count updates after follow/unfollow
- [ ] Mutual badge (↔) displays for mutual follows
- [ ] Follower list loads with pagination

### Optimistic UI Testing

- [ ] Follow button changes to "Following" immediately
- [ ] Follower count increments immediately on follow
- [ ] UI reverts if API call fails
- [ ] Loading state during API call
- [ ] Error toast shown on failure

### List Testing

- [ ] Follower list paginated (20 per page)
- [ ] Following list paginated (20 per page)
- [ ] Empty states display correctly
- [ ] User avatars render correctly
- [ ] Follow buttons work in lists

### Edge Cases

- [ ] Unfollow confirmation prevents accidental clicks
- [ ] Concurrent follow/unfollow handled gracefully
- [ ] Network error during follow handled
- [ ] Follow button disabled during loading

### Performance

- [ ] Follow/unfollow feels instant (optimistic update)
- [ ] List loads < 500ms
- [ ] Pagination smooth (< 300ms)

### Accessibility

- [ ] Follow button keyboard accessible
- [ ] Confirmation modal keyboard navigable
- [ ] Screen reader announces follow status changes
- [ ] Focus management in modal

## Estimated Effort

6 hours
