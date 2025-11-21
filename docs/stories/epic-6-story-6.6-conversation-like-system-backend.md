# Story 6.6: Conversation Like System Backend

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 5 hours

## Description

Create backend API for conversation like/unlike functionality with atomic operations, duplicate prevention, and like count aggregation.

## Dependencies

**Blocks**:

- Story 6.7: Like Button UI & Liked Conversations Feed

**Requires**:

- Story 4.1: Conversation Data Model
- Story 6.1: User Authentication Backend

## Acceptance Criteria

- [ ] `conversation_likes` junction table created
- [ ] Composite primary key: (user_id, conversation_id)
- [ ] POST /api/conversations/{id}/like endpoint (idempotent)
- [ ] DELETE /api/conversations/{id}/unlike endpoint (idempotent)
- [ ] GET /api/conversations/{id}/liked endpoint (check if user liked)
- [ ] GET /api/users/me/liked-conversations endpoint (paginated)
- [ ] Like count updated atomically
- [ ] Duplicate like prevention
- [ ] Authenticated users only
- [ ] Unit tests >80% coverage
- [ ] Integration tests for atomic operations

## Technical Notes

**Database Migration**:

```sql
-- V15__create_conversation_likes.sql
CREATE TABLE conversation_likes (
    user_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, conversation_id),

    CONSTRAINT fk_conversation_likes_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_conversation_likes_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE
);

-- Index for fetching user's liked conversations
CREATE INDEX idx_conversation_likes_user_created
    ON conversation_likes(user_id, created_at DESC);

-- Index for fetching conversation's like count
CREATE INDEX idx_conversation_likes_conversation
    ON conversation_likes(conversation_id);

-- Add like_count column to conversations table
ALTER TABLE conversations
    ADD COLUMN like_count INTEGER NOT NULL DEFAULT 0;

-- Create trigger to update like_count automatically
CREATE OR REPLACE FUNCTION update_conversation_like_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE conversations
        SET like_count = like_count + 1
        WHERE id = NEW.conversation_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE conversations
        SET like_count = GREATEST(like_count - 1, 0)
        WHERE id = OLD.conversation_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_conversation_like_count
AFTER INSERT OR DELETE ON conversation_likes
FOR EACH ROW
EXECUTE FUNCTION update_conversation_like_count();
```

**Entity - ConversationLike.java**:

```java
package com.gaji.domain.conversationlike;

import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConversationLike {

    private UUID userId;
    private UUID conversationId;
    private LocalDateTime createdAt;
}
```

**Composite Key - ConversationLikeId.java**:

```java
package com.gaji.domain.conversationlike;

import lombok.*;

import java.io.Serializable;
import java.util.UUID;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class ConversationLikeId implements Serializable {
    private UUID userId;
    private UUID conversationId;
}
```

**Mapper - ConversationLikeMapper.java**:

```java
package com.gaji.mapper;

import com.gaji.domain.conversationlike.ConversationLike;
import org.apache.ibatis.annotations.*;

import java.util.List;
import java.util.UUID;

@Mapper
public interface ConversationLikeMapper {

    @Select("SELECT COUNT(*) > 0 FROM conversation_likes WHERE user_id = #{userId} AND conversation_id = #{conversationId}")
    boolean existsByUserIdAndConversationId(@Param("userId") UUID userId, @Param("conversationId") UUID conversationId);

    @Select("""
        SELECT c.* FROM conversations c
        JOIN conversation_likes cl ON cl.conversation_id = c.id
        WHERE cl.user_id = #{userId}
        ORDER BY cl.created_at DESC
        LIMIT #{limit} OFFSET #{offset}
    """)
    List<Conversation> findLikedConversationsByUserId(
        @Param("userId") UUID userId,
        @Param("offset") int offset,
        @Param("limit") int limit
    );

    @Select("SELECT COUNT(*) FROM conversation_likes WHERE conversation_id = #{conversationId}")
    long countByConversationId(@Param("conversationId") UUID conversationId);
}
```

**Service - ConversationLikeService.java**:

```java
package com.gaji.service;

import com.gaji.domain.conversationlike.ConversationLike;
import com.gaji.dto.ConversationResponse;
import com.gaji.dto.LikeResponse;
import com.gaji.mapper.ConversationLikeMapper;
import com.gaji.mapper.ConversationMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ConversationLikeService {

    private final ConversationLikeRepository conversationLikeRepository;
    private final ConversationRepository conversationRepository;

    /**
     * Like a conversation (idempotent).
     * Returns true if newly liked, false if already liked.
     */
    @Transactional
    public LikeResponse likeConversation(UUID conversationId, UUID userId) {
        // Verify conversation exists
        var conversation = conversationRepository.findById(conversationId)
            .orElseThrow(() -> new IllegalArgumentException("Conversation not found: " + conversationId));

        // Check if already liked
        boolean alreadyLiked = conversationLikeRepository.existsByUserIdAndConversationId(userId, conversationId);

        if (alreadyLiked) {
            log.info("User {} already liked conversation {}", userId, conversationId);
            return LikeResponse.builder()
                .isLiked(true)
                .likeCount(conversation.getLikeCount())
                .build();
        }

        // Create like
        ConversationLike like = ConversationLike.builder()
            .userId(userId)
            .conversationId(conversationId)
            .build();

        conversationLikeRepository.save(like);

        // Refresh to get updated like_count from trigger
        conversationRepository.flush();
        conversation = conversationRepository.findById(conversationId).orElseThrow();

        log.info("User {} liked conversation {}", userId, conversationId);

        return LikeResponse.builder()
            .isLiked(true)
            .likeCount(conversation.getLikeCount())
            .build();
    }

    /**
     * Unlike a conversation (idempotent).
     * Returns true if unlike successful, false if not liked.
     */
    @Transactional
    public LikeResponse unlikeConversation(UUID conversationId, UUID userId) {
        // Verify conversation exists
        var conversation = conversationRepository.findById(conversationId)
            .orElseThrow(() -> new IllegalArgumentException("Conversation not found: " + conversationId));

        ConversationLikeId likeId = new ConversationLikeId(userId, conversationId);
        boolean existed = conversationLikeRepository.existsById(likeId);

        if (!existed) {
            log.info("User {} never liked conversation {}", userId, conversationId);
            return LikeResponse.builder()
                .isLiked(false)
                .likeCount(conversation.getLikeCount())
                .build();
        }

        conversationLikeRepository.deleteById(likeId);

        // Refresh to get updated like_count from trigger
        conversationRepository.flush();
        conversation = conversationRepository.findById(conversationId).orElseThrow();

        log.info("User {} unliked conversation {}", userId, conversationId);

        return LikeResponse.builder()
            .isLiked(false)
            .likeCount(conversation.getLikeCount())
            .build();
    }

    /**
     * Check if user liked a conversation.
     */
    @Transactional(readOnly = true)
    public LikeResponse isLiked(UUID conversationId, UUID userId) {
        var conversation = conversationRepository.findById(conversationId)
            .orElseThrow(() -> new IllegalArgumentException("Conversation not found: " + conversationId));

        boolean isLiked = conversationLikeRepository.existsByUserIdAndConversationId(userId, conversationId);

        return LikeResponse.builder()
            .isLiked(isLiked)
            .likeCount(conversation.getLikeCount())
            .build();
    }

    /**
     * Get paginated list of conversations liked by user.
     */
    @Transactional(readOnly = true)
    public Page<ConversationResponse> getLikedConversations(UUID userId, Pageable pageable) {
        Page<Conversation> conversations = conversationLikeRepository.findLikedConversationsByUserId(userId, pageable);

        return conversations.map(ConversationResponse::from);
    }
}
```

**DTO - LikeResponse.java**:

```java
package com.gaji.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LikeResponse {
    private boolean isLiked;
    private int likeCount;
}
```

**Controller - ConversationLikeController.java**:

```java
package com.gaji.controller;

import com.gaji.dto.ConversationResponse;
import com.gaji.dto.LikeResponse;
import com.gaji.security.CurrentUser;
import com.gaji.service.ConversationLikeService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/conversations")
@RequiredArgsConstructor
public class ConversationLikeController {

    private final ConversationLikeService conversationLikeService;

    /**
     * Like a conversation.
     * POST /api/conversations/{id}/like
     */
    @PostMapping("/{id}/like")
    public ResponseEntity<LikeResponse> likeConversation(
        @PathVariable UUID id,
        @AuthenticationPrincipal CurrentUser currentUser
    ) {
        LikeResponse response = conversationLikeService.likeConversation(id, currentUser.getUserId());
        return ResponseEntity.ok(response);
    }

    /**
     * Unlike a conversation.
     * DELETE /api/conversations/{id}/unlike
     */
    @DeleteMapping("/{id}/unlike")
    public ResponseEntity<LikeResponse> unlikeConversation(
        @PathVariable UUID id,
        @AuthenticationPrincipal CurrentUser currentUser
    ) {
        LikeResponse response = conversationLikeService.unlikeConversation(id, currentUser.getUserId());
        return ResponseEntity.ok(response);
    }

    /**
     * Check if user liked a conversation.
     * GET /api/conversations/{id}/liked
     */
    @GetMapping("/{id}/liked")
    public ResponseEntity<LikeResponse> isLiked(
        @PathVariable UUID id,
        @AuthenticationPrincipal CurrentUser currentUser
    ) {
        LikeResponse response = conversationLikeService.isLiked(id, currentUser.getUserId());
        return ResponseEntity.ok(response);
    }

    /**
     * Get user's liked conversations.
     * GET /api/users/me/liked-conversations
     */
    @GetMapping("/users/me/liked-conversations")
    public ResponseEntity<Page<ConversationResponse>> getLikedConversations(
        @AuthenticationPrincipal CurrentUser currentUser,
        @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable
    ) {
        Page<ConversationResponse> conversations = conversationLikeService.getLikedConversations(
            currentUser.getUserId(),
            pageable
        );
        return ResponseEntity.ok(conversations);
    }
}
```

## QA Checklist

### Functional Testing

- [ ] POST /like creates conversation_likes record
- [ ] DELETE /unlike removes conversation_likes record
- [ ] GET /liked returns correct isLiked status
- [ ] GET /users/me/liked-conversations returns paginated list
- [ ] like_count increments on like
- [ ] like_count decrements on unlike
- [ ] Trigger updates like_count atomically

### Data Integrity

- [ ] Composite primary key prevents duplicate likes
- [ ] CASCADE delete removes likes when conversation deleted
- [ ] CASCADE delete removes likes when user deleted
- [ ] like_count never goes below 0
- [ ] Concurrent likes handled correctly (no race condition)

### Idempotency

- [ ] Liking already-liked conversation returns same result
- [ ] Unliking already-unliked conversation returns same result
- [ ] No error on duplicate like/unlike

### Edge Cases

- [ ] Liking non-existent conversation returns 404
- [ ] Unliking non-existent conversation returns 404
- [ ] Unauthenticated request returns 401
- [ ] Missing conversationId returns 400

### Performance

- [ ] Like/unlike operation < 100ms
- [ ] Composite PK lookup optimized
- [ ] Index on user_id for liked conversations query
- [ ] Pagination query < 200ms

### Security

- [ ] Only authenticated users can like
- [ ] User cannot like on behalf of another user
- [ ] JWT validation on all endpoints

## Estimated Effort

5 hours
