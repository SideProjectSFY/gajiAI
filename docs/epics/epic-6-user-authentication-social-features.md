# Epic 6: User Authentication & Social Features

## Epic Goal

Implement comprehensive user management system including registration, login, JWT authentication, user profiles, follow/follower system, conversation likes, and personal memos, enabling social interaction and personalized user experience.

## User Value

Users can create accounts, build their identity through profiles, follow other creators whose What If scenarios they enjoy, like compelling conversations, and save personal notes on conversations for future reference. This transforms Gaji from an anonymous platform to a social community where users build reputation and connections.

## Timeline

**Week 1, Day 4 - Week 2, Day 2 of MVP development**

## Stories

### Story 6.1: User Registration & Authentication Backend

**Priority: P0 - Critical**

**Description**: Implement Spring Boot backend for user registration, login, JWT token generation, and password encryption using BCrypt.

**Acceptance Criteria**:

- [ ] User domain model created (see Epic 0, Story 0.3 for schema)
- [ ] UserMapper with MyBatis methods:
  - `findByEmail(String email)`
  - `findByUsername(String username)`
  - `existsByEmail(String email)`
  - `existsByUsername(String username)`
- [ ] UserService with methods:
  - `registerUser(RegisterRequest) → UserResponse`
  - `loginUser(LoginRequest) → AuthResponse`
  - `getCurrentUser(String token) → UserResponse`
  - `updateProfile(UUID userId, UpdateProfileRequest) → UserResponse`
- [ ] Password encryption using BCrypt (strength: 12)
- [ ] JWT token generation with claims:
  - `sub`: user ID
  - `username`: username
  - `email`: email
  - `exp`: expiration (7 days)
- [ ] JWT token validation and parsing
- [ ] REST API endpoints:
  - POST /api/v1/auth/register
  - POST /api/v1/auth/login
  - GET /api/v1/auth/me (requires authentication)
  - PUT /api/v1/users/{id}/profile (requires authentication)
  - GET /api/v1/users/{id} (public profile)
- [ ] Validation rules:
  - Email: valid email format, unique
  - Username: 3-50 chars, alphanumeric + underscore, unique
  - Password: min 8 chars, at least 1 uppercase, 1 lowercase, 1 number
  - Display name: max 100 chars
  - Bio: max 500 chars
- [ ] Error responses:
  - 400 Bad Request: validation errors
  - 401 Unauthorized: invalid credentials
  - 409 Conflict: email/username already exists
- [ ] Unit tests for UserService (registration, login, password encryption)
- [ ] Integration tests for auth endpoints

**API Examples**:

**POST /api/v1/auth/register**

```json
Request:
{
  "email": "user@example.com",
  "username": "hermione_fan",
  "password": "SecurePass123",
  "display_name": "Hermione Fan"
}

Response (201 Created):
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "hermione_fan",
    "display_name": "Hermione Fan",
    "avatar_url": null,
    "created_at": "2025-11-12T10:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": "2025-11-19T10:00:00Z"
}
```

**POST /api/v1/auth/login**

```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response (200 OK):
{
  "user": { /* same as register */ },
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": "2025-11-19T10:00:00Z"
}
```

**Technical Notes**:

- Use Spring Security's PasswordEncoder (BCryptPasswordEncoder)
- JWT secret stored in environment variable (min 256-bit key)
- Token expiration: 7 days for MVP (consider refresh tokens in Phase 2)
- Soft delete users: set `deleted_at` timestamp (preserve data integrity)

**Estimated Effort**: 8 hours

---

### Story 6.2: User Authentication Frontend (Login/Register)

**Priority: P0 - Critical**

**Description**: Build Vue.js login and registration pages with form validation, error handling, and JWT token storage.

**Acceptance Criteria**:

- [ ] LoginView component (`/login` route)
  - Email input with validation
  - Password input with show/hide toggle
  - "Remember me" checkbox (optional)
  - Submit button with loading state
  - "Don't have an account? Register" link
  - Error message display
- [ ] RegisterView component (`/register` route)
  - Email input with validation
  - Username input with real-time availability check
  - Password input with strength indicator
  - Confirm password input
  - Display name input
  - Terms of service checkbox
  - Submit button with loading state
  - "Already have an account? Login" link
  - Error message display
- [ ] Form validation (client-side):
  - Email format validation
  - Username: 3-50 chars, alphanumeric + underscore
  - Password strength: weak/medium/strong indicator
  - Passwords match validation
- [ ] AuthStore (Pinia) with actions:
  - `login(email, password)`
  - `register(registerData)`
  - `logout()`
  - `checkAuth()` (validate stored token)
  - `getCurrentUser()`
- [ ] Token storage:
  - Store JWT in localStorage
  - Add token to Axios default headers
  - Clear token on logout
- [ ] Navigation guards:
  - Redirect to /browse if logged in user visits /login or /register
  - Redirect to /login if unauthenticated user visits protected routes
- [ ] Error handling:
  - Display validation errors from backend
  - Show network errors gracefully
  - Auto-dismiss success messages after 3 seconds
- [ ] Responsive design (mobile-first, 375px+ width)
- [ ] Accessibility: keyboard navigation, ARIA labels

**User Flow**:

```
1. User visits /register
2. Fills form: email, username, password, display name
3. Clicks "Create Account"
4. Loading spinner shows
5. On success:
   - Token stored in localStorage
   - Redirect to /browse
   - Welcome toast: "Welcome, {display_name}!"
6. On error:
   - Show error message below form
   - Keep form filled (don't clear inputs)
```

**Technical Notes**:

- Use VeeValidate or manual validation with computed properties
- Password strength: use zxcvbn library or simple regex patterns
- Username availability: debounce API call (300ms delay)
- Store user object in AuthStore (avoid repeated API calls)

**Estimated Effort**: 8 hours

---

### Story 6.3: User Profile Page & Edit Profile

**Priority: P1 - High**

**Description**: Build user profile page displaying user info, created scenarios, liked conversations, and enable profile editing.

**Acceptance Criteria**:

- [ ] ProfileView component (`/users/{username}` route)
  - Profile header:
    - Avatar (default if not uploaded)
    - Display name
    - Username (@username)
    - Bio
    - Join date
    - Follower count / Following count
    - "Edit Profile" button (if own profile)
    - "Follow" / "Unfollow" button (if other user)
  - Tabs:
    - "Scenarios" (created scenarios by this user)
    - "Conversations" (public conversations by this user)
    - "Liked" (liked conversations, visible only to own profile)
  - Scenario cards (same as browse view from Epic 3)
  - Conversation cards showing conversation title, scenario, message count, like count
- [ ] EditProfileModal component
  - Display name input (max 100 chars)
  - Bio textarea (max 500 chars, character counter)
  - Avatar upload (optional for MVP, can use URL input)
  - "Save Changes" button with loading state
  - Cancel button
- [ ] API integration:
  - GET /api/v1/users/{username}
  - GET /api/v1/users/{username}/scenarios
  - GET /api/v1/users/{username}/conversations
  - GET /api/v1/users/{username}/liked (requires authentication, only own profile)
  - PUT /api/v1/users/{id}/profile
- [ ] Loading states for each tab
- [ ] Empty states:
  - "No scenarios created yet" with "Create First Scenario" CTA
  - "No conversations started yet"
  - "No liked conversations yet"
- [ ] Responsive design (mobile: single column, desktop: two columns)
- [ ] SEO meta tags with user info (og:title, og:description)

**Profile Display Example**:

```
┌──────────────────────────────────────┐
│  [Avatar]  Hermione Fan              │
│            @hermione_fan              │
│            Exploring What If          │
│            timelines for HP           │
│            📅 Joined Nov 2025         │
│            👥 42 followers            │
│            👤 15 following            │
│            [Edit Profile] or [Follow]│
├──────────────────────────────────────┤
│  [Scenarios] [Conversations] [Liked] │
├──────────────────────────────────────┤
│  [Scenario Card 1]  [Scenario Card 2]│
│  [Scenario Card 3]  [Scenario Card 4]│
└──────────────────────────────────────┘
```

**Technical Notes**:

- Avatar: accept image URL for MVP, file upload in Phase 2
- Use skeleton loaders for better perceived performance
- Cache user profile in Pinia store (avoid repeated fetches)
- Profile route uses username slug, not UUID (better SEO)

**Estimated Effort**: 10 hours

---

### Story 6.4: Follow/Follower System Backend

**Priority: P1 - High**

**Description**: Implement backend API for following/unfollowing users, retrieving follower/following lists, and maintaining accurate counts.

**Acceptance Criteria**:

- [ ] Follow entity created (see Epic 0, Story 0.3 for schema)
- [ ] FollowRepository with methods:
  - `findByFollowerIdAndFollowingId(UUID, UUID)`
  - `existsByFollowerIdAndFollowingId(UUID, UUID)`
  - `deleteByFollowerIdAndFollowingId(UUID, UUID)`
  - `countByFollowingId(UUID)` (follower count)
  - `countByFollowerId(UUID)` (following count)
  - `findAllByFollowerId(UUID, Pageable)` (get following list)
  - `findAllByFollowingId(UUID, Pageable)` (get follower list)
- [ ] FollowService with methods:
  - `followUser(UUID followerId, UUID followingId)`
  - `unfollowUser(UUID followerId, UUID followingId)`
  - `isFollowing(UUID followerId, UUID followingId) → boolean`
  - `getFollowers(UUID userId, Pageable) → Page<UserResponse>`
  - `getFollowing(UUID userId, Pageable) → Page<UserResponse>`
- [ ] REST API endpoints:
  - POST /api/v1/users/{id}/follow (requires authentication)
  - DELETE /api/v1/users/{id}/unfollow (requires authentication)
  - GET /api/v1/users/{id}/followers (public, paginated)
  - GET /api/v1/users/{id}/following (public, paginated)
  - GET /api/v1/users/{id}/is-following (requires authentication)
- [ ] Business rules:
  - Cannot follow yourself (return 400 Bad Request)
  - Cannot follow same user twice (idempotent: return 200 OK)
  - Unfollowing non-followed user is idempotent (return 200 OK)
  - Following increments both follower_count and following_count (atomic transaction)
  - Unfollowing decrements both counts (atomic transaction)
- [ ] Atomic count updates:
  ```sql
  UPDATE users SET follower_count = follower_count + 1 WHERE id = ?
  UPDATE users SET following_count = following_count + 1 WHERE id = ?
  ```
- [ ] Validation:
  - User IDs must exist (return 404 Not Found if not)
  - Authenticated user can only follow/unfollow as themselves
- [ ] Unit tests for FollowService
- [ ] Integration tests for follow/unfollow endpoints
- [ ] Race condition testing (concurrent follow/unfollow)

**API Examples**:

**POST /api/v1/users/{id}/follow**

```json
Request: (no body, user ID from auth token)

Response (200 OK):
{
  "following": true,
  "follower_count": 43,
  "following_count": 16
}
```

**GET /api/v1/users/{id}/followers?page=0&size=20**

```json
Response (200 OK):
{
  "content": [
    {
      "id": "uuid",
      "username": "harry_potter_fan",
      "display_name": "Harry Potter Fan",
      "avatar_url": "https://...",
      "follower_count": 120,
      "following_count": 80
    },
    // ... more users
  ],
  "page": 0,
  "size": 20,
  "total_elements": 43,
  "total_pages": 3
}
```

**Technical Notes**:

- Use database transactions for count updates (prevent inconsistencies)
- Add unique constraint on (follower_id, following_id) to prevent duplicates
- Consider eventual consistency for counts (can rebuild if desync occurs)
- Index on follower_id and following_id for fast queries

**Estimated Effort**: 6 hours

---

### Story 6.5: Follow/Unfollow UI & Follower Lists

**Priority: P1 - High**

**Description**: Build frontend components for following/unfollowing users, displaying follower/following lists, and showing follow status.

**Acceptance Criteria**:

- [ ] FollowButton component
  - Props: `userId`, `isFollowing` (initial state)
  - States: "Follow" (not following), "Following" (following), "Loading"
  - Hover state on "Following": changes to "Unfollow" (red)
  - Click toggles follow status with API call
  - Optimistic update (update UI immediately, rollback if API fails)
  - Emits event: `@follow-changed` with new state
- [ ] FollowerListModal component (`/users/{username}/followers` or modal)
  - List of users with avatar, username, display name
  - Each user has FollowButton (if not self)
  - Infinite scroll pagination (load 20 per batch)
  - Empty state: "No followers yet"
  - Close button
- [ ] FollowingListModal component (similar to FollowerListModal)
- [ ] Integration in ProfileView:
  - Click "42 followers" → opens FollowerListModal
  - Click "15 following" → opens FollowingListModal
  - FollowButton in profile header (if not own profile)
- [ ] UserStore (Pinia) actions:
  - `followUser(userId)`
  - `unfollowUser(userId)`
  - `getFollowers(userId, page)`
  - `getFollowing(userId, page)`
  - `checkFollowStatus(userId)`
- [ ] Notification toast on follow/unfollow:
  - "You are now following @username"
  - "You unfollowed @username"
- [ ] Error handling:
  - Show error toast if follow/unfollow fails
  - Rollback optimistic update on failure

**Follow Button States**:

```
Not Following:
┌─────────────────┐
│  Follow         │ (primary color)
└─────────────────┘

Following (default):
┌─────────────────┐
│  ✓ Following    │ (gray)
└─────────────────┘

Following (hover):
┌─────────────────┐
│  Unfollow       │ (red)
└─────────────────┘

Loading:
┌─────────────────┐
│  [spinner]      │ (disabled)
└─────────────────┘
```

**Technical Notes**:

- Use optimistic updates for better UX (don't wait for API)
- Rollback logic: revert to previous state if API fails
- Debounce rapid clicks (prevent double-follow)
- Cache follower/following lists (5-minute TTL)

**Estimated Effort**: 7 hours

---

### Story 6.6: Conversation Like System

**Priority: P1 - High**

**Description**: Implement like functionality for conversations, allowing users to appreciate compelling What If discussions.

**Acceptance Criteria**:

- [ ] Like entity created (see Epic 0, Story 0.3 for schema)
- [ ] Conversation entity updated with `like_count` column
- [ ] LikeRepository with methods:
  - `findByUserIdAndConversationId(UUID, UUID)`
  - `existsByUserIdAndConversationId(UUID, UUID)`
  - `deleteByUserIdAndConversationId(UUID, UUID)`
  - `countByConversationId(UUID)` (like count)
- [ ] LikeService with methods:
  - `likeConversation(UUID userId, UUID conversationId)`
  - `unlikeConversation(UUID userId, UUID conversationId)`
  - `hasLiked(UUID userId, UUID conversationId) → boolean`
  - `getLikeCount(UUID conversationId) → long`
- [ ] REST API endpoints:
  - POST /api/v1/conversations/{id}/like (requires authentication)
  - DELETE /api/v1/conversations/{id}/unlike (requires authentication)
  - GET /api/v1/conversations/{id}/liked (requires authentication)
- [ ] Conversation API updated:
  - GET /api/v1/conversations/{id} includes `like_count` and `liked_by_me` (boolean)
  - GET /api/v1/conversations includes like_count for each conversation
- [ ] Business rules:
  - Cannot like own conversation (return 400 Bad Request)
  - Liking twice is idempotent (return 200 OK)
  - Unliking non-liked conversation is idempotent
  - Like increments conversation.like_count atomically
  - Unlike decrements conversation.like_count atomically
- [ ] Atomic count updates (prevent race conditions)
- [ ] Unit tests for LikeService
- [ ] Integration tests for like/unlike endpoints

**API Examples**:

**POST /api/v1/conversations/{id}/like**

```json
Response (200 OK):
{
  "liked": true,
  "like_count": 42
}
```

**GET /api/v1/conversations/{id}**

```json
Response (200 OK):
{
  "id": "uuid",
  "scenario_id": "uuid",
  "title": "Exploring Slytherin Hermione",
  "message_count": 15,
  "like_count": 42,
  "liked_by_me": true,
  "created_at": "2025-11-12T10:00:00Z",
  // ... other fields
}
```

**Technical Notes**:

- Use unique constraint (user_id, conversation_id) to prevent duplicate likes
- Consider soft delete for likes (preserve analytics)
- Add index on conversation_id for fast like count queries
- Transaction for like + count increment

**Estimated Effort**: 5 hours

---

### Story 6.7: Like Button UI & Liked Conversations Feed

**Priority: P1 - High**

**Description**: Build like button component for conversations and display user's liked conversations in their profile.

**Acceptance Criteria**:

- [ ] LikeButton component
  - Props: `conversationId`, `initialLikeCount`, `initialLiked`
  - States: liked (filled heart), not liked (outline heart)
  - Click toggles like status with API call
  - Animated like (heart scale + color transition)
  - Displays like count next to heart icon
  - Optimistic update (immediate UI change)
  - Disabled state (when not authenticated, show tooltip "Login to like")
- [ ] Integration in conversation cards:
  - Show LikeButton in bottom-right corner
  - Display "42 likes" text next to button
- [ ] Integration in conversation detail view:
  - LikeButton in header or footer
  - Prominent like count display
- [ ] Liked conversations tab in ProfileView:
  - Display liked conversations with scenario context
  - Show when conversation was liked (created_at from likes table)
  - Infinite scroll pagination
  - Empty state: "You haven't liked any conversations yet"
- [ ] ConversationStore (Pinia) actions:
  - `likeConversation(conversationId)`
  - `unlikeConversation(conversationId)`
  - `getLikedConversations(page)`
- [ ] Error handling:
  - Show error toast if like/unlike fails
  - Rollback optimistic update on failure
- [ ] Accessibility: keyboard support (Enter/Space to like)

**Like Button States**:

```
Not Liked:
┌──────────────┐
│  ♡  42       │ (gray outline)
└──────────────┘

Liked:
┌──────────────┐
│  ♥  43       │ (red filled, animated)
└──────────────┘

Not Authenticated:
┌──────────────┐
│  ♡  42  🔒   │ (gray, tooltip: "Login to like")
└──────────────┘
```

**Technical Notes**:

- Use CSS transitions for smooth heart animation
- Optimistic update: increment count immediately, rollback if failed
- Cache liked status in Pinia store (avoid repeated API calls)
- Sort liked conversations by most recent first

**Estimated Effort**: 6 hours

---

## Epic-Level Acceptance Criteria

- [ ] Users can register and login securely (JWT authentication)
- [ ] Users have profiles with avatars and bios
- [ ] Users can follow/unfollow other users
- [ ] Follow counts display correctly on profiles
- [ ] Users can like conversations
- [ ] Like counts update in real-time
- [ ] Mobile responsive design for all user features
- [ ] Password security follows best practices (bcrypt)

- Use UPSERT (ON CONFLICT DO UPDATE) for create/update in single query
- Unique constraint (user_id, conversation_id) enforces one memo per user
- Index on user_id for fast "my memos" queries
- Markdown support for memo content (optional, nice-to-have)

**Estimated Effort**: 4 hours

---

### Story 6.9: Memo UI in Conversation View

**Priority: P2 - Medium**

**Description**: Build memo editor component in conversation detail view, allowing users to add/edit/delete private notes.

**Acceptance Criteria**:

- [ ] MemoEditor component in conversation detail view
  - Collapsible section: "My Notes 📝" (collapsed by default)
  - Expand shows textarea for memo content
  - Character counter (2000 max, show warning at 1900+)
  - "Save Memo" button with loading state
  - "Delete Memo" button (if memo exists)
  - Auto-save draft to localStorage (prevent data loss)
  - Success message on save: "Memo saved"
- [ ] Display existing memo on page load (if exists)
- [ ] Markdown preview toggle (optional, nice-to-have)
- [ ] Memo indicator on conversation cards:
  - Small 📝 icon if user has memo on this conversation
  - Tooltip: "You have notes on this conversation"
- [ ] MemoStore (Pinia) actions:
  - `saveMemo(conversationId, content)`
  - `getMemo(conversationId)`
  - `deleteMemo(conversationId)`
- [ ] Error handling:
  - Show error toast if save fails
  - Preserve draft in localStorage if save fails
  - Confirm before deleting memo

**Memo Editor UI**:

```
Conversation: "Exploring Slytherin Hermione"
─────────────────────────────────────────────
[Chat messages...]
─────────────────────────────────────────────
▼ My Notes 📝

┌─────────────────────────────────────┐
│ Interesting take on Slytherin       │
│ values. Need to explore ambition    │
│ vs. cunning distinction more.       │
│                                     │
│                         65/2000     │
└─────────────────────────────────────┘

[Save Memo]  [Delete Memo]  [Preview]
```

**Technical Notes**:

- Auto-save draft every 2 seconds using debounce
- Clear localStorage draft after successful save
- Use contenteditable or textarea for input
- Markdown rendering using marked.js (optional)

**Estimated Effort**: 5 hours

---

## Epic-Level Acceptance Criteria

- [ ] Users can register, login, and logout successfully
- [ ] JWT authentication protects all authenticated routes
- [ ] User profiles display created scenarios, conversations, likes
- [ ] Follow/unfollow system works with accurate counts
- [ ] Conversation likes work with accurate counts
- [ ] Personal memos save and display correctly
- [ ] All social features accessible on mobile (responsive design)
- [ ] No race conditions in count updates (follower, following, like)
- [ ] Authentication state persists across page refreshes

## Dependencies

**Blocks**:

- Epic 1-5: All epics can function without auth but significantly enhanced with it
- Social features enable viral growth and retention

**Requires**:

- Epic 0: Project Setup & Infrastructure (database, backend, frontend)
- User table schema from Epic 0, Story 0.3

## Success Metrics

**Technical Metrics**:

- Registration success rate > 95%
- Login response time < 200ms (p95)
- JWT token validation < 10ms
- Follow/unfollow API < 100ms
- Like/unlike API < 100ms
- Zero count inconsistencies (follower, like counts accurate)

**User Metrics** (Phase 1 - 3 months):

- 60%+ of visitors create accounts
- 30%+ of users follow at least one other user
- 50%+ of users like at least one conversation
- 20%+ of users create memos
- 40%+ retention after 7 days (logged-in users)

## Risk Mitigation

**Risk 1: Password security vulnerabilities**

- Mitigation: Use BCrypt with strength 12 (industry standard)
- Mitigation: Enforce password complexity (8+ chars, mixed case, numbers)
- Mitigation: Add rate limiting to prevent brute force (Phase 2)

**Risk 2: Count inconsistencies (followers, likes)**

- Mitigation: Use atomic database transactions
- Mitigation: Add database triggers for count maintenance
- Mitigation: Periodic count reconciliation job (Phase 2)

**Risk 3: Token theft/XSS attacks**

- Mitigation: Set HttpOnly cookies (Phase 2, use localStorage for MVP)
- Mitigation: Short token expiration (7 days)
- Mitigation: Implement refresh tokens (Phase 2)
- Mitigation: CSP headers to prevent XSS

**Risk 4: Spam follows/likes**

- Mitigation: Rate limiting (max 100 follows/hour, Phase 2)
- Mitigation: Suspicious activity detection (Phase 3)
- Mitigation: User reporting system (Phase 2)

## Technical Debt Decisions

**Accepted Debt** (to be addressed post-MVP):

- No email verification (trust-based registration)
- No password reset flow (contact support for MVP)
- No two-factor authentication
- No OAuth (Google, Twitter login)
- No refresh tokens (7-day expiration acceptable)
- No rate limiting on auth endpoints
- Token stored in localStorage (migrate to HttpOnly cookies Phase 2)

**Won't Build** (architectural decisions):

- Session-based authentication (JWT stateless approach)
- Role-based access control beyond user/admin (not needed for MVP)
- Multi-device session management

## Testing Strategy

**Unit Tests**:

- UserService: registration, login, password validation
- FollowService: follow, unfollow, count updates
- LikeService: like, unlike, count updates
- MemoService: create, update, delete

**Integration Tests**:

- Auth flow: register → login → access protected route
- Follow flow: follow user → verify counts → unfollow
- Like flow: like conversation → verify count → unlike
- Memo flow: create → read → update → delete

**E2E Tests**:

- User journey: register → create profile → follow user → like conversation → add memo
- Social interaction: User A follows User B → User B sees follower count increase
- Authentication: Login → access protected page → logout → redirect to login

**Security Tests**:

- SQL injection on registration (parameterized queries)
- XSS on bio/memo content (sanitization)
- Invalid JWT rejection
- Expired JWT rejection

## Open Questions

1. **Q**: Should follower/following lists be public or private?
   **A**: Public for MVP (Twitter model). Privacy settings in Phase 2.

2. **Q**: Should we notify users when someone follows them?
   **A**: Not in MVP. Notification system in Phase 2 (Epic 7).

3. **Q**: Can users unlike a conversation after deleting it?
   **A**: Soft delete conversations preserve likes. Hard delete removes likes (cascade).

4. **Q**: Should memos support rich text (bold, italic, links)?
   **A**: Plain text for MVP. Markdown preview optional (nice-to-have). Rich editor Phase 2.

5. **Q**: Maximum follow limit to prevent spam?
   **A**: No hard limit in MVP. Rate limiting (100 follows/hour) in Phase 2.

## Definition of Done

- [ ] All 9 stories completed with acceptance criteria met
- [ ] Users can register, login, edit profile successfully
- [ ] Follow/unfollow system functional with accurate counts
- [ ] Like system functional on conversations
- [ ] Memo system allows private notes on conversations
- [ ] Unit tests >80% coverage on services
- [ ] Integration tests passing for all auth and social endpoints
- [ ] E2E test: complete user journey from registration to social interaction
- [ ] Security tests passing (no SQL injection, XSS vulnerabilities)
- [ ] Password encryption verified (BCrypt strength 12)
- [ ] JWT tokens validated correctly (expiration, signature)
- [ ] No race conditions in count updates (tested with concurrent requests)
- [ ] Mobile responsive design verified on 375px+ width
- [ ] Code review completed, no P0/P1 security issues
- [ ] Deployed to Railway staging, smoke tested

---

**Epic Owner**: Backend Lead + Frontend Lead (joint ownership)

**Start Date**: Week 1, Day 4 of MVP development

**Target Completion**: Week 2, Day 1 (3.5 working days)

**Estimated Total Effort**: 50 hours

**Priority**: HIGH - Social features essential for viral growth and retention
