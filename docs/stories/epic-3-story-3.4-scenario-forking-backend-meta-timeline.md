# Story 3.4: Scenario Forking Backend & Meta-Timeline Logic

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.4
**Priority**: P1 - High  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Implement scenario forking system that allows users to create meta-scenarios by forking existing scenarios, enabling unlimited creative branching (e.g., "Hermione in Slytherin" → "Hermione in Slytherin AND Head Girl").

## Dependencies

**Blocks**:

- Story 3.3: Scenario Forking UI (needs backend fork logic)

**Requires**:

- Story 1.1: Scenario Data Model & API (parent_scenario_id column enables forking)
- Story 6.1: User Authentication Backend (requires authenticated users)

## Acceptance Criteria

- [ ] POST /api/scenarios/{id}/fork endpoint creates child scenario with parent_scenario_id reference
- [ ] Fork inherits parent's base_story and scenario_type
- [ ] Fork combines parent parameters + new parameters via JSONB merge
- [ ] Circular reference prevention: Cannot fork ancestor scenarios (prevents A→B→A loops)
- [ ] Fork depth unlimited (supports infinite meta-scenario chains)
- [ ] Fork increments parent's fork_count atomically
- [ ] GET /api/scenarios/{id}/forks returns all direct children
- [ ] GET /api/scenarios/{id}/fork-tree returns recursive tree structure (root to all descendants)
- [ ] Fork validation: New parameters must differ from parent (prevent duplicate forks)
- [ ] Database triggers maintain referential integrity
- [ ] Response time < 200ms for fork creation
- [ ] Unit tests >85% coverage

## Technical Notes

**Fork Endpoint Implementation**:

```java
@PostMapping("/scenarios/{id}/fork")
public ResponseEntity<?> forkScenario(
    @PathVariable UUID id,
    @RequestBody ForkScenarioRequest request,
    @CurrentUser User user
) {
    // Get parent scenario
    Scenario parent = scenarioRepository.findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("Scenario not found"));

    // Validate: New parameters must differ from parent
    if (request.getParameters().equals(parent.getParameters())) {
        throw new BusinessException("Fork must have different parameters than parent");
    }

    // Prevent circular reference: Check if parent is descendant of current user's scenarios
    if (isCircularReference(parent, user)) {
        throw new BusinessException("Cannot create circular scenario fork");
    }

    // Merge parameters: Parent parameters + New parameters
    Map<String, Object> mergedParams = new HashMap<>(parent.getParameters());
    mergedParams.putAll(request.getParameters());

    // Create forked scenario
    Scenario fork = new Scenario();
    fork.setBaseStory(parent.getBaseStory());
    fork.setScenarioType(parent.getScenarioType());
    fork.setParentScenarioId(id);
    fork.setParameters(mergedParams);
    fork.setCreatorId(user.getId());
    fork.setQualityScore(0.5); // Default score for forks

    Scenario savedFork = scenarioRepository.save(fork);

    // Increment parent's fork count atomically
    scenarioRepository.incrementForkCount(id);

    return ResponseEntity.ok(savedFork);
}

private boolean isCircularReference(Scenario parent, User user) {
    // Check if parent is already a descendant of any scenario owned by user
    // This prevents creating loops like: UserScenario → Parent → Fork → UserScenario
    Set<UUID> userScenarioIds = scenarioRepository.findAllByCreatorId(user.getId())
        .stream()
        .map(Scenario::getId)
        .collect(Collectors.toSet());

    Scenario current = parent;
    while (current.getParentScenarioId() != null) {
        if (userScenarioIds.contains(current.getId())) {
            return true; // Circular reference detected
        }
        current = scenarioRepository.findById(current.getParentScenarioId())
            .orElse(null);
        if (current == null) break;
    }

    return false;
}
```

**Fork Tree Query** (Recursive CTE):

```java
@Query(value = """
    WITH RECURSIVE scenario_tree AS (
        SELECT id, base_story, parent_scenario_id, parameters,
               creator_id, fork_count, quality_score, 0 AS depth
        FROM scenarios
        WHERE id = :rootId

        UNION ALL

        SELECT s.id, s.base_story, s.parent_scenario_id, s.parameters,
               s.creator_id, s.fork_count, s.quality_score, st.depth + 1
        FROM scenarios s
        INNER JOIN scenario_tree st ON s.parent_scenario_id = st.id
        WHERE st.depth < 20
    )
    SELECT * FROM scenario_tree ORDER BY depth, created_at
    """, nativeQuery = true)
List<Map<String, Object>> findForkTree(@Param("rootId") UUID rootId);
```

**Parameter Merging Example**:

```json
// Parent Scenario
{
  "character": "Hermione",
  "original_property": "Gryffindor",
  "new_property": "Slytherin"
}

// Fork Request (adds Head Girl dimension)
{
  "additional_property": "Head Girl"
}

// Merged Fork Parameters
{
  "character": "Hermione",
  "original_property": "Gryffindor",
  "new_property": "Slytherin",
  "additional_property": "Head Girl"
}
// Result: "Hermione in Slytherin AND Head Girl"
```

## QA Checklist

### Functional Testing

- [ ] Fork scenario successfully creates child with parent_scenario_id
- [ ] Fork inherits parent's base_story and scenario_type
- [ ] Fork merges parent and new parameters correctly
- [ ] Duplicate parameters rejected (same as parent)
- [ ] Circular reference prevention works (A→B→A blocked)
- [ ] Fork count incremented on parent after fork creation
- [ ] GET /forks returns all direct children
- [ ] GET /fork-tree returns complete recursive tree

### Fork Logic Validation

- [ ] First-level fork: Parent → Child works
- [ ] Second-level fork: Parent → Child → Grandchild works
- [ ] Third-level fork and beyond works (unlimited depth)
- [ ] Multiple children from same parent allowed
- [ ] Fork tree depth limit (20 levels) prevents infinite recursion

### Data Integrity

- [ ] parent_scenario_id foreign key constraint enforced
- [ ] Deleting parent scenario handles children gracefully (cascade or prevent)
- [ ] fork_count accurate after multiple forks
- [ ] Concurrent fork requests handled correctly (race condition safe)

### Performance

- [ ] Fork creation < 200ms
- [ ] Fork tree query < 500ms for tree with 50 nodes
- [ ] Circular reference check < 100ms
- [ ] Atomic fork_count increment uses database lock

### Edge Cases

- [ ] Fork root scenario (no parent) works
- [ ] Fork deeply nested scenario (10+ levels) works
- [ ] Fork with identical parameters rejected
- [ ] Non-existent parent scenario returns 404

## Estimated Effort

10 hours
