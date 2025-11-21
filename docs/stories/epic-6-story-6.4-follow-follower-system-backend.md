# Story 6.4: Follow/Follower System Backend

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 6 hours

## Description

Implement backend API for user following relationships with follow/unfollow endpoints, follower/following lists, and mutual follow detection.

## Dependencies

**Blocks**:

- Story 6.5: Follow/Unfollow UI (requires follow API)

**Requires**:

- Story 6.1: User Authentication Backend (users table)

## Acceptance Criteria

- [ ] `user_follows` junction table with composite primary key (follower_id, following_id)
- [ ] POST /api/users/{id}/follow endpoint (authenticated)
- [ ] DELETE /api/users/{id}/unfollow endpoint (authenticated)
- [ ] GET /api/users/{id}/followers endpoint with pagination
- [ ] GET /api/users/{id}/following endpoint with pagination
- [ ] GET /api/users/{id}/is-following endpoint (check if current user follows target)
- [ ] Follower/following counts exposed in user profile DTO
- [ ] Prevent self-follow (validation)
- [ ] Idempotent follow/unfollow (no error if already followed/unfollowed)
- [ ] Database constraint: Unique (follower_id, following_id)
- [ ] Unit tests >80% coverage

## Technical Notes

**Database Migration**:

```sql
-- Migration: V9__create_user_follows_table.sql
CREATE TABLE user_follows (
    follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id <> following_id) -- Prevent self-follow
);

-- Index for reverse lookup (who is following this user)
CREATE INDEX idx_user_follows_following ON user_follows(following_id);

-- Index for forward lookup (who this user is following)
CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
```

**UserFollow Domain Model**:

```java
@Data
public class UserFollow {
    private UUID followerId;
    private UUID followingId;
    private User follower;
    private User following;
    private Instant createdAt;
}

@Data
public class UserFollowId implements Serializable {
    private UUID followerId;
    private UUID followingId;
}
```

**Follow Service**:

```java
@Service
public class UserFollowService {

    @Autowired
    private UserFollowRepository userFollowRepository;

    @Autowired
    private UserRepository userRepository;

    public void followUser(UUID followerId, UUID followingId) {
        // Validate: Cannot follow yourself
        if (followerId.equals(followingId)) {
            throw new BadRequestException("Cannot follow yourself");
        }

        // Validate: Both users exist
        User follower = userRepository.findById(followerId)
            .orElseThrow(() -> new ResourceNotFoundException("Follower not found"));
        User following = userRepository.findById(followingId)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        // Idempotent: Check if already following
        if (userFollowRepository.existsByFollowerIdAndFollowingId(followerId, followingId)) {
            return; // Already following, no-op
        }

        // Create follow relationship
        UserFollow userFollow = new UserFollow();
        userFollow.setFollowerId(followerId);
        userFollow.setFollowingId(followingId);
        userFollow.setFollower(follower);
        userFollow.setFollowing(following);

        userFollowRepository.save(userFollow);
    }

    public void unfollowUser(UUID followerId, UUID followingId) {
        // Idempotent: Delete if exists
        userFollowRepository.deleteByFollowerIdAndFollowingId(followerId, followingId);
    }

    public boolean isFollowing(UUID followerId, UUID followingId) {
        return userFollowRepository.existsByFollowerIdAndFollowingId(followerId, followingId);
    }

    public Page<User> getFollowers(UUID userId, Pageable pageable) {
        return userFollowRepository.findFollowersByUserId(userId, pageable);
    }

    public Page<User> getFollowing(UUID userId, Pageable pageable) {
        return userFollowRepository.findFollowingByUserId(userId, pageable);
    }

    public long getFollowerCount(UUID userId) {
        return userFollowRepository.countByFollowingId(userId);
    }

    public long getFollowingCount(UUID userId) {
        return userFollowRepository.countByFollowerId(userId);
    }

    public boolean isMutualFollow(UUID userId1, UUID userId2) {
        return userFollowRepository.existsByFollowerIdAndFollowingId(userId1, userId2) &&
               userFollowRepository.existsByFollowerIdAndFollowingId(userId2, userId1);
    }
}
```

**Mapper with Custom Queries**:

```java
@Mapper
public interface UserFollowMapper {

    @Select("SELECT COUNT(*) > 0 FROM user_follows WHERE follower_id = #{followerId} AND following_id = #{followingId}")
    boolean existsByFollowerIdAndFollowingId(@Param("followerId") UUID followerId, @Param("followingId") UUID followingId);

    @Delete("DELETE FROM user_follows WHERE follower_id = #{followerId} AND following_id = #{followingId}")
    void deleteByFollowerIdAndFollowingId(@Param("followerId") UUID followerId, @Param("followingId") UUID followingId);

    @Select("SELECT COUNT(*) FROM user_follows WHERE following_id = #{followingId}")
    long countByFollowingId(@Param("followingId") UUID followingId); // Follower count

    @Select("SELECT COUNT(*) FROM user_follows WHERE follower_id = #{followerId}")
    long countByFollowerId(@Param("followerId") UUID followerId); // Following count

    @Select("""
        SELECT u.* FROM users u
        JOIN user_follows uf ON u.id = uf.follower_id
        WHERE uf.following_id = #{userId}
        ORDER BY uf.created_at DESC
        LIMIT #{limit} OFFSET #{offset}
        """)
    List<User> findFollowersByUserId(
        @Param("userId") UUID userId,
        @Param("offset") int offset,
        @Param("limit") int limit
    );

    @Select("""
        SELECT u.* FROM users u
        JOIN user_follows uf ON u.id = uf.following_id
        WHERE uf.follower_id = #{userId}
        ORDER BY uf.created_at DESC
        LIMIT #{limit} OFFSET #{offset}
        """)
    List<User> findFollowingByUserId(
        @Param("userId") UUID userId,
        @Param("offset") int offset,
        @Param("limit") int limit
    );
}
```

**Follow Controller**:

```java
@RestController
@RequestMapping("/api/users")
public class UserFollowController {

    @Autowired
    private UserFollowService userFollowService;

    @Autowired
    private UserService userService;

    @PostMapping("/{id}/follow")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<FollowResponse> followUser(
        @PathVariable UUID id,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User currentUser = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        userFollowService.followUser(currentUser.getId(), id);

        return ResponseEntity.ok(new FollowResponse(
            true,
            userFollowService.getFollowerCount(id),
            userFollowService.isMutualFollow(currentUser.getId(), id)
        ));
    }

    @DeleteMapping("/{id}/unfollow")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<FollowResponse> unfollowUser(
        @PathVariable UUID id,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User currentUser = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        userFollowService.unfollowUser(currentUser.getId(), id);

        return ResponseEntity.ok(new FollowResponse(
            false,
            userFollowService.getFollowerCount(id),
            false
        ));
    }

    @GetMapping("/{id}/is-following")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<IsFollowingResponse> isFollowing(
        @PathVariable UUID id,
        @AuthenticationPrincipal UserDetails userDetails
    ) {
        User currentUser = userService.findByEmail(userDetails.getUsername())
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        boolean isFollowing = userFollowService.isFollowing(currentUser.getId(), id);
        boolean isMutual = userFollowService.isMutualFollow(currentUser.getId(), id);

        return ResponseEntity.ok(new IsFollowingResponse(isFollowing, isMutual));
    }

    @GetMapping("/{id}/followers")
    public ResponseEntity<Page<UserDTO>> getFollowers(
        @PathVariable UUID id,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size);
        Page<User> followers = userFollowService.getFollowers(id, pageable);

        return ResponseEntity.ok(followers.map(this::toDTO));
    }

    @GetMapping("/{id}/following")
    public ResponseEntity<Page<UserDTO>> getFollowing(
        @PathVariable UUID id,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size);
        Page<User> following = userFollowService.getFollowing(id, pageable);

        return ResponseEntity.ok(following.map(this::toDTO));
    }

    private UserDTO toDTO(User user) {
        return UserDTO.builder()
            .id(user.getId())
            .username(user.getUsername())
            .avatarUrl(user.getAvatarUrl())
            .bio(user.getBio())
            .build();
    }
}
```

**Response DTOs**:

```java
@Data
@AllArgsConstructor
public class FollowResponse {
    private boolean isFollowing;
    private long followerCount;
    private boolean isMutual;
}

@Data
@AllArgsConstructor
public class IsFollowingResponse {
    private boolean isFollowing;
    private boolean isMutual;
}
```

## QA Checklist

### Functional Testing

- [ ] Follow endpoint creates relationship in database
- [ ] Unfollow endpoint deletes relationship from database
- [ ] Follower count increments on follow
- [ ] Follower count decrements on unfollow
- [ ] is-following returns true after follow
- [ ] is-following returns false after unfollow
- [ ] Mutual follow detected correctly

### Data Integrity Testing

- [ ] Self-follow rejected (CHECK constraint)
- [ ] Duplicate follow prevented (composite primary key)
- [ ] Follow idempotent (no error if already following)
- [ ] Unfollow idempotent (no error if not following)
- [ ] Cascade delete on user deletion (ON DELETE CASCADE)

### Edge Cases

- [ ] Follow non-existent user returns 404
- [ ] Unauthenticated follow returns 401
- [ ] Follower/following lists paginated correctly
- [ ] Empty follower/following lists handled
- [ ] Concurrent follow/unfollow handled safely

### Performance

- [ ] Follow operation < 100ms
- [ ] Unfollow operation < 100ms
- [ ] Follower count query < 50ms (with index)
- [ ] Follower/following list query < 200ms
- [ ] is-following check < 50ms

### Security

- [ ] Cannot follow/unfollow without authentication
- [ ] Cannot follow yourself
- [ ] Follow relationships private to authenticated users
- [ ] Rate limiting on follow/unfollow (prevent spam)

## Estimated Effort

6 hours
