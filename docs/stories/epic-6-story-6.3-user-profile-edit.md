# Story 6.3: User Profile Page & Edit Profile

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 7 hours

## Description

Create user profile page displaying user information, scenario/conversation statistics, and edit profile functionality with avatar upload and bio editing.

## Dependencies

**Blocks**:

- Story 6.5: Follow/Follower UI (profile displays follow counts)

**Requires**:

- Story 6.1: User Authentication Backend (user endpoints)
- Story 6.2: User Authentication Frontend (logged-in user context)

## Acceptance Criteria

- [ ] `/profile/:username` route displays public user profile
- [ ] `/profile/edit` route for editing own profile (authenticated)
- [ ] Profile displays: avatar, username, bio, join date, stats (scenarios created, conversations started, followers, following)
- [ ] Edit profile form: username, bio (max 200 chars), avatar upload
- [ ] Avatar upload supports JPG/PNG, max 5MB, with client-side image preview
- [ ] Avatar cropped to square (1:1 aspect ratio) before upload
- [ ] Profile updates saved to backend with success toast
- [ ] View own profile shows "Edit Profile" button
- [ ] View other's profile shows "Follow" button (Story 6.5 dependency)
- [ ] Empty state: "No scenarios created yet" if user has 0 scenarios
- [ ] Unit tests >80% coverage

## Technical Notes

**Backend Profile API**:

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private ScenarioRepository scenarioRepository;

    @Autowired
    private ConversationRepository conversationRepository;

    @Autowired
    private FileStorageService fileStorageService;

    @GetMapping("/{username}")
    public ResponseEntity<UserProfileDTO> getUserProfile(@PathVariable String username) {
        User user = userService.findByUsername(username)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        long scenarioCount = scenarioRepository.countByCreatedBy(user);
        long conversationCount = conversationRepository.countByCreatedBy(user);
        long followerCount = user.getFollowers().size();
        long followingCount = user.getFollowing().size();

        UserProfileDTO dto = UserProfileDTO.builder()
            .id(user.getId())
            .username(user.getUsername())
            .bio(user.getBio())
            .avatarUrl(user.getAvatarUrl())
            .joinedAt(user.getCreatedAt())
            .scenarioCount(scenarioCount)
            .conversationCount(conversationCount)
            .followerCount(followerCount)
            .followingCount(followingCount)
            .build();

        return ResponseEntity.ok(dto);
    }

    @PutMapping("/profile")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<UserDTO> updateProfile(
        @RequestBody UpdateProfileRequest request,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User user = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        // Update username (check uniqueness)
        if (!user.getUsername().equals(request.getUsername())) {
            if (userService.existsByUsername(request.getUsername())) {
                throw new BadRequestException("Username already taken");
            }
            user.setUsername(request.getUsername());
        }

        // Update bio
        if (request.getBio() != null && request.getBio().length() <= 200) {
            user.setBio(request.getBio());
        }

        User updatedUser = userService.save(user);
        return ResponseEntity.ok(toDTO(updatedUser));
    }

    @PostMapping("/profile/avatar")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<AvatarUploadResponse> uploadAvatar(
        @RequestParam("file") MultipartFile file,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        // Validate file type and size
        String contentType = file.getContentType();
        if (!contentType.equals("image/jpeg") && !contentType.equals("image/png")) {
            throw new BadRequestException("Only JPG and PNG images are allowed");
        }

        if (file.getSize() > 5 * 1024 * 1024) { // 5MB limit
            throw new BadRequestException("File size exceeds 5MB limit");
        }

        User user = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        // Save file and get URL
        String avatarUrl = fileStorageService.storeAvatar(file, user.getId());

        // Update user avatar URL
        user.setAvatarUrl(avatarUrl);
        userService.save(user);

        return ResponseEntity.ok(new AvatarUploadResponse(avatarUrl));
    }
}
```

**File Storage Service**:

```java
@Service
public class FileStorageService {

    @Value("${file.upload-dir}")
    private String uploadDir;

    @Value("${app.base-url}")
    private String baseUrl;

    public String storeAvatar(MultipartFile file, UUID userId) {
        try {
            // Generate unique filename
            String originalFilename = file.getOriginalFilename();
            String extension = originalFilename.substring(originalFilename.lastIndexOf("."));
            String filename = userId.toString() + "_" + System.currentTimeMillis() + extension;

            // Create upload directory if not exists
            Path uploadPath = Paths.get(uploadDir, "avatars");
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            // Save file
            Path targetLocation = uploadPath.resolve(filename);
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);

            // Return public URL
            return baseUrl + "/uploads/avatars/" + filename;
        } catch (IOException e) {
            throw new RuntimeException("Failed to store avatar file", e);
        }
    }
}
```

**Profile Page Component**:

```vue
<template>
  <div class="profile-page">
    <div v-if="isLoading" class="loading-state">
      <Spinner /> Loading profile...
    </div>

    <div v-else-if="profile" class="profile-container">
      <div class="profile-header">
        <img
          :src="profile.avatarUrl || '/default-avatar.png'"
          alt="Avatar"
          class="avatar-large"
        />

        <div class="profile-info">
          <h1>{{ profile.username }}</h1>
          <p class="bio">{{ profile.bio || "No bio yet." }}</p>
          <p class="join-date">Joined {{ formatDate(profile.joinedAt) }}</p>

          <div class="profile-stats">
            <div class="stat">
              <strong>{{ profile.scenarioCount }}</strong>
              <span>Scenarios</span>
            </div>
            <div class="stat">
              <strong>{{ profile.conversationCount }}</strong>
              <span>Conversations</span>
            </div>
            <div class="stat">
              <strong>{{ profile.followerCount }}</strong>
              <span>Followers</span>
            </div>
            <div class="stat">
              <strong>{{ profile.followingCount }}</strong>
              <span>Following</span>
            </div>
          </div>

          <div class="profile-actions">
            <router-link
              v-if="isOwnProfile"
              to="/profile/edit"
              class="btn-primary"
            >
              Edit Profile
            </router-link>
            <!-- Follow button added in Story 6.5 -->
          </div>
        </div>
      </div>

      <!-- User's scenarios and conversations -->
      <div class="profile-content">
        <h2>Scenarios Created</h2>
        <div v-if="scenarios.length === 0" class="empty-state">
          <p>No scenarios created yet.</p>
        </div>
        <div v-else class="scenario-grid">
          <ScenarioCard
            v-for="scenario in scenarios"
            :key="scenario.id"
            :scenario="scenario"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";

const route = useRoute();
const authStore = useAuthStore();

const profile = ref(null);
const scenarios = ref([]);
const isLoading = ref(true);

const isOwnProfile = computed(() => {
  return authStore.currentUser?.username === route.params.username;
});

onMounted(async () => {
  await loadProfile();
  await loadUserScenarios();
});

const loadProfile = async () => {
  try {
    const response = await api.get(`/users/${route.params.username}`);
    profile.value = response.data;
  } catch (error) {
    console.error("Failed to load profile:", error);
  } finally {
    isLoading.value = false;
  }
};

const loadUserScenarios = async () => {
  try {
    const response = await api.get(
      `/scenarios?createdBy=${route.params.username}`
    );
    scenarios.value = response.data.content;
  } catch (error) {
    console.error("Failed to load scenarios:", error);
  }
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
  });
};
</script>

<style scoped>
.profile-header {
  display: flex;
  gap: 2rem;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-large {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #667eea;
}

.profile-info h1 {
  font-size: 32px;
  margin-bottom: 0.5rem;
}

.bio {
  color: #666;
  margin-bottom: 0.5rem;
}

.profile-stats {
  display: flex;
  gap: 2rem;
  margin: 1.5rem 0;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat strong {
  font-size: 24px;
  color: #667eea;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}
</style>
```

**Edit Profile Page Component**:

```vue
<template>
  <div class="edit-profile-page">
    <div class="edit-profile-card">
      <h1>Edit Profile</h1>

      <form @submit.prevent="handleSubmit">
        <div class="avatar-section">
          <img
            :src="avatarPreview || profile.avatarUrl || '/default-avatar.png'"
            alt="Avatar"
            class="avatar-large"
          />
          <div class="avatar-upload">
            <label for="avatar" class="btn-secondary"> Choose Image </label>
            <input
              id="avatar"
              type="file"
              accept="image/jpeg,image/png"
              @change="handleAvatarChange"
              style="display: none;"
            />
            <p class="hint">JPG or PNG, max 5MB</p>
          </div>
        </div>

        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            :class="{ 'input-error': errors.username }"
          />
          <span v-if="errors.username" class="error-message">{{
            errors.username
          }}</span>
        </div>

        <div class="form-group">
          <label for="bio">Bio</label>
          <textarea
            id="bio"
            v-model="form.bio"
            rows="4"
            maxlength="200"
            placeholder="Tell us about yourself..."
          />
          <p class="char-count">{{ form.bio.length }} / 200</p>
        </div>

        <div class="form-actions">
          <button type="submit" :disabled="isSaving" class="btn-primary">
            {{ isSaving ? "Saving..." : "Save Changes" }}
          </button>
          <router-link to="/profile" class="btn-secondary">Cancel</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import api from "@/services/api";

const router = useRouter();
const authStore = useAuthStore();

const profile = ref(authStore.currentUser);
const avatarPreview = ref(null);
const avatarFile = ref<File | null>(null);
const isSaving = ref(false);

const form = reactive({
  username: "",
  bio: "",
});

const errors = reactive({
  username: "",
});

onMounted(() => {
  form.username = profile.value.username;
  form.bio = profile.value.bio || "";
});

const handleAvatarChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (file) {
    // Validate file type
    if (!file.type.match(/image\/(jpeg|png)/)) {
      alert("Only JPG and PNG images are allowed");
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert("File size exceeds 5MB limit");
      return;
    }

    avatarFile.value = file;

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      avatarPreview.value = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }
};

const handleSubmit = async () => {
  errors.username = "";

  if (form.username.length < 3) {
    errors.username = "Username must be at least 3 characters";
    return;
  }

  isSaving.value = true;

  try {
    // Upload avatar if changed
    if (avatarFile.value) {
      const formData = new FormData();
      formData.append("file", avatarFile.value);

      await api.post("/users/profile/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    }

    // Update profile
    await api.put("/users/profile", {
      username: form.username,
      bio: form.bio,
    });

    // Update auth store
    authStore.user.username = form.username;
    authStore.user.bio = form.bio;

    showToast("Profile updated successfully!");
    router.push(`/profile/${form.username}`);
  } catch (error: any) {
    errors.username =
      error.response?.data?.message || "Failed to update profile";
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.edit-profile-card {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.avatar-upload {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #666;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}
</style>
```

## QA Checklist

### Functional Testing

- [ ] Profile page displays user information correctly
- [ ] Profile stats (scenarios, conversations, followers, following) accurate
- [ ] Edit profile form pre-filled with current data
- [ ] Username update validates uniqueness
- [ ] Bio limited to 200 characters
- [ ] Avatar upload works with JPG/PNG
- [ ] Avatar preview shown before save

### Validation Testing

- [ ] Avatar file type validation (JPG/PNG only)
- [ ] Avatar file size validation (≤5MB)
- [ ] Username length validation (≥3 chars)
- [ ] Bio character limit enforced (≤200 chars)
- [ ] Username uniqueness checked on server

### UI/UX Testing

- [ ] Profile page responsive on mobile
- [ ] Avatar displayed as circle (1:1 aspect ratio)
- [ ] Empty state shows when no scenarios
- [ ] Edit profile button only visible on own profile
- [ ] Success toast after profile update

### Performance

- [ ] Profile loads < 500ms
- [ ] Avatar upload completes < 2 seconds
- [ ] Profile update completes < 800ms

### Accessibility

- [ ] Avatar upload button keyboard accessible
- [ ] Form inputs have proper labels
- [ ] Character counter updates in real-time
- [ ] Error messages announced to screen readers

## Estimated Effort

7 hours
