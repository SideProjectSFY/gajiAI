# Story 5.1: Conversation Tree Data Structure

**Epic**: Epic 5 - Conversation Tree Visualization  
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 6 hours

## Description

Create recursive query logic and Spring Boot endpoint to retrieve conversation fork trees with metadata for D3.js visualization.

## Dependencies

**Blocks**:

- Story 5.2: Tree Visualization Component (needs tree data structure)
- Story 5.3: Tree Navigation (needs tree endpoint)

**Requires**:

- Story 4.1: Conversation Data Model (parent_conversation_id enables tree)
- Story 4.3: Conversation Forking UI (creates forks to visualize)

## Acceptance Criteria

- [ ] Recursive CTE query retrieves conversation tree from root to all descendants
- [ ] GET /api/conversations/{id}/tree endpoint returns nested JSON structure
- [ ] Each tree node includes: id, title, parent_id, message_count, created_at, is_active (current conversation)
- [ ] Tree depth limited to 10 levels (error if exceeded)
- [ ] Response includes root conversation even if forked from another
- [ ] Leaf nodes flagged with `has_children: false`
- [ ] Response time < 300ms for tree with 50 nodes
- [ ] Unit tests for tree query logic >80% coverage

## Technical Notes

**Expected Response Structure**:

```json
{
  "id": "root-uuid",
  "title": "Original Conversation",
  "parent_id": null,
  "message_count": 12,
  "fork_message_count": null,
  "created_at": "2024-01-15T10:00:00Z",
  "is_active": false,
  "has_children": true,
  "children": [
    {
      "id": "fork-1-uuid",
      "title": "What if Hermione arrived late?",
      "parent_id": "root-uuid",
      "message_count": 8,
      "fork_message_count": 6,
      "created_at": "2024-01-15T11:30:00Z",
      "is_active": true,
      "has_children": false,
      "children": []
    }
  ]
}
```

**Recursive CTE Query** (PostgreSQL):

```sql
WITH RECURSIVE tree AS (
  -- Base case: root conversation
  SELECT id, title, parent_conversation_id, message_count, created_at, 0 AS depth
  FROM conversations
  WHERE id = :root_id

  UNION ALL

  -- Recursive case: children
  SELECT c.id, c.title, c.parent_conversation_id, c.message_count, c.created_at, t.depth + 1
  FROM conversations c
  INNER JOIN tree t ON c.parent_conversation_id = t.id
  WHERE t.depth < 10
)
SELECT * FROM tree ORDER BY depth, created_at;
```

## QA Checklist

### Functional Testing

- [ ] Retrieve tree for root conversation with 5 forks
- [ ] Retrieve tree for leaf conversation (returns single node)
- [ ] Tree structure matches actual parent-child relationships
- [ ] is_active flag correctly identifies current conversation
- [ ] has_children flag correctly identifies leaf nodes

### Tree Query Validation

- [ ] Recursive CTE returns all descendants correctly
- [ ] Depth limit prevents infinite loops (test with malformed data)
- [ ] Tree ordered by depth and created_at
- [ ] Nested children array structure correct

### Performance

- [ ] Tree with 50 nodes retrieved < 300ms
- [ ] Tree with 100 nodes retrieved < 500ms
- [ ] Query uses index on parent_conversation_id

### Edge Cases

- [ ] Tree with single node (no children) works
- [ ] Tree with max depth (10 levels) works
- [ ] Deleted conversations excluded from tree
- [ ] Non-existent conversation ID returns 404

## Estimated Effort

6 hours
