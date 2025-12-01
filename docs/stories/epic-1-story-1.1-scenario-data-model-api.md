# Story 1.1: Scenario Data Model & API Foundation

**Epic**: Epic 1 - What If Scenario Foundation  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Create the PostgreSQL database schema and Spring Boot REST API for managing What If scenarios with JSONB parameter flexibility.

## Dependencies

**Blocks**:

- Story 1.2-1.5: All other Epic 1 stories (need scenario API)
- Epic 2 stories (AI adaptation needs scenario data)
- Epic 3 stories (discovery needs scenarios to browse)
- Epic 4 stories (conversations need scenarios for context)

**Requires**:

- Story 0.1: Spring Boot Backend Setup
- Story 0.3: PostgreSQL Database Setup

## Acceptance Criteria

- [ ] `scenarios` table created with UUID primary key, parent_scenario_id for forking, scenario_type enum, JSONB parameters column
- [ ] Recursive CTE query support for scenario tree retrieval
- [ ] CRUD API endpoints: POST /api/scenarios, GET /api/scenarios/{id}, GET /api/scenarios, PUT /api/scenarios/{id}, DELETE /api/scenarios/{id}
- [ ] Scenario forking endpoint: POST /api/scenarios/{id}/fork
- [ ] Circular reference prevention trigger implemented
- [ ] GIN index on JSONB column, B-tree indexes on base_story, creator_id, quality_score
- [ ] Soft delete pattern with deleted_at timestamp
- [ ] Java domain models with MyBatis JSONB mapping support
- [ ] Response time < 100ms for single scenario retrieval
- [ ] Unit tests >80% coverage on mapper and service layers

## Technical Notes

- JSONB enables schema-free scenario parameters supporting future scenario type expansion
- parent_scenario_id enables infinite meta-scenario branching ("Hermione in Slytherin AND Head Girl")
- fork_count, conversation_count, quality_score support future recommendation algorithms

## QA Checklist

### Functional Testing

- [ ] Create scenario with all three types (CHARACTER_CHANGE, EVENT_ALTERATION, SETTING_MODIFICATION)
- [ ] Retrieve scenario by ID returns correct data
- [ ] List scenarios with pagination works
- [ ] Update scenario parameters successfully
- [ ] Delete scenario (soft delete) works
- [ ] Fork scenario creates child with parent_scenario_id
- [ ] Circular reference prevention rejects invalid forks

### Data Integrity

- [ ] JSONB parameters validate correctly for each scenario type
- [ ] Scenario type enum accepts only valid values
- [ ] Timestamps (created_at, updated_at) auto-populate
- [ ] Soft delete sets deleted_at without removing data
- [ ] Fork increments parent's fork_count

### Performance

- [ ] Single scenario retrieval < 100ms
- [ ] List query with 1000 scenarios < 200ms
- [ ] JSONB queries use GIN index efficiently
- [ ] No N+1 query issues

### Security

- [ ] Only authenticated users can create scenarios
- [ ] Users can only delete their own scenarios
- [ ] JSONB injection attacks prevented

## Estimated Effort

8 hours
