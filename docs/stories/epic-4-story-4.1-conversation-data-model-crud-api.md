# Story 4.1: Conversation Data Model & CRUD API

**Epic**: Epic 4 - Conversation System  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Create the PostgreSQL database schema and Spring Boot REST API for managing conversations and messages with fork support and tree structure.

## Dependencies

**Blocks**:

- Story 4.2: Message Streaming & AI Integration (needs conversation data)
- Story 4.3: Conversation Forking UI (needs CRUD API)
- Epic 5 stories (tree visualization needs conversation data)

**Requires**:

- Story 0.1: Spring Boot Backend Setup
- Story 0.3: PostgreSQL Database Setup
- Story 1.1: Scenario Data Model (conversations reference scenarios)

## Acceptance Criteria

- [ ] `conversations` table created with UUID primary key, scenario_id FK, parent_conversation_id for fork tree, fork_message_count column
- [ ] `messages` table created with conversation_id FK, content TEXT, role ENUM (user/assistant), timestamp
- [ ] CRUD API endpoints for conversations: POST /api/conversations, GET /api/conversations/{id}, GET /api/conversations, PUT /api/conversations/{id}, DELETE /api/conversations/{id}
- [ ] Messages nested in conversation response: GET /api/conversations/{id} returns conversation with all messages
- [ ] **Fork Business Logic**: parent_conversation_id IS NULL validation (only ROOT conversations can be forked)
- [ ] **Fork Message Copy Logic**: POST /api/conversations/{id}/fork copies `min(6, total_message_count)` most recent messages to new conversation
- [ ] fork_message_count tracks actual copied message count in response
- [ ] B-tree indexes on scenario_id, creator_id, parent_conversation_id
- [ ] Soft delete pattern with deleted_at timestamp
- [ ] Java domain models with MyBatis relationships
- [ ] Response time < 150ms for conversation with 50 messages
- [ ] Unit tests >80% coverage

## Technical Notes

**Fork Copy Logic** (Critical):

```java
// Conversation fork endpoint implementation
public Conversation forkConversation(UUID conversationId) {
    Conversation original = findById(conversationId);

    // Validate: Only ROOT conversations can be forked
    if (original.getParentConversationId() != null) {
        throw new BusinessException("Cannot fork a forked conversation");
    }

    // Copy min(6, total) most recent messages
    List<Message> allMessages = original.getMessages();
    int totalCount = allMessages.size();
    int copyCount = Math.min(6, totalCount);

    List<Message> messagesToCopy = allMessages
        .subList(totalCount - copyCount, totalCount);

    Conversation forked = new Conversation();
    forked.setParentConversationId(conversationId);
    forked.setScenarioId(original.getScenarioId());
    forked.setForkMessageCount(copyCount); // Track actual copied count

    // Copy messages
    messagesToCopy.forEach(msg -> {
        Message copied = new Message();
        copied.setContent(msg.getContent());
        copied.setRole(msg.getRole());
        forked.addMessage(copied);
    });

    return save(forked);
}
```

## QA Checklist

### Functional Testing

- [ ] Create conversation linked to valid scenario
- [ ] Retrieve conversation with nested messages
- [ ] List conversations with pagination
- [ ] Update conversation title successfully
- [ ] Delete conversation (soft delete) works
- [ ] **Fork ROOT conversation with 10 messages → copies exactly 6 messages**
- [ ] **Fork ROOT conversation with 3 messages → copies all 3 messages**
- [ ] **Attempt to fork FORKED conversation → returns 400 error**

### Fork Business Logic Validation

- [ ] parent_conversation_id IS NULL check enforced
- [ ] Fork increments parent's fork_count
- [ ] fork_message_count matches actual copied messages
- [ ] Copied messages maintain original content and order
- [ ] Forked conversation shares parent's scenario_id

### Data Integrity

- [ ] Conversation requires valid scenario_id FK
- [ ] Messages require valid conversation_id FK
- [ ] Timestamps auto-populate correctly
- [ ] Soft delete preserves message history

### Performance

- [ ] Single conversation retrieval < 150ms (with 50 messages)
- [ ] List query with 1000 conversations < 300ms
- [ ] Fork operation < 200ms (copying 6 messages)
- [ ] No N+1 query issues in nested message loading

### Security

- [ ] Only authenticated users can create conversations
- [ ] Users can only delete their own conversations
- [ ] Fork validation prevents unauthorized parent access

## Estimated Effort

10 hours
