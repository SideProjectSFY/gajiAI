# Epic 3: Scenario Discovery & Forking

## Epic Goal

Enable users to discover compelling What If scenarios through multiple discovery paths (browse, search, trending), fork scenarios to create meta-timelines, and share scenarios on social media with viral-optimized og:image cards.

## User Value

Users don't just create scenarios—they discover incredible What If timelines created by others ("OMG someone made 'Gatsby as a tech entrepreneur'!"), fork them to explore variations ("What if tech entrepreneur Gatsby ALSO met Daisy?"), and share discoveries on Twitter/Reddit/Discord, driving viral growth through "Let's gaji this timeline" social sharing.

## Timeline

**Week 2-3 of MVP development**

## Stories (7 total, 63 hours)

### Story 3.1: Book Browse Page

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-3-story-3.1-book-browse-page.md`

**Description**: Create the primary book discovery page implementing book-first navigation with search, filters, and infinite scroll.

**Estimated Effort**: 8 hours

---

### Story 3.2: Book Detail Page

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-3-story-3.2-book-detail-page.md`

**Description**: Build the book detail hub displaying book information, statistics, and all scenarios for that book with a prominent Create Scenario CTA.

**Estimated Effort**: 10 hours

---

### Story 3.3: Scenario Browse UI & Filtering

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-3-story-3.3-scenario-browse-ui-filtering.md`

**Description**: Build Vue.js interface for browsing What If scenarios with multi-dimensional filtering (by book, scenario type, popularity) and card-based discovery UX.

**Acceptance Criteria**:

- [ ] ScenarioExplorer component with card-grid layout (3 columns desktop, 2 tablet, 1 mobile)
- [ ] Scenario card displays:
  - Scenario title
  - Base story (book title)
  - Scenario type badge (CHARACTER_CHANGE, EVENT_ALTERATION, SETTING_MODIFICATION)
  - Fork count + conversation count
  - Creator username + avatar
  - "Gaji This →" CTA button
- [ ] Filter sidebar with:
  - Book selector (dropdown, shows only books with scenarios)
  - Scenario type multi-select (checkboxes)
  - Sort by: "Most Gaji'd" (fork_count DESC), "Most Discussed" (conversation_count DESC), "Newest" (created_at DESC), "Most Liked" (like_count DESC)
  - Date range: "Last 7 days", "Last 30 days", "All time"
- [ ] Infinite scroll pagination (load 20 scenarios per batch)
- [ ] API integration: GET /api/scenarios with query params (?book=&type=&sort=&page=)
- [ ] Loading states with skeleton cards
- [ ] Empty state: "No scenarios found. Create the first one!"
- [ ] Mobile responsive (375px+ width)

**Card Interaction**:

- Click card → Navigate to scenario detail page
- Click "Gaji This →" → Open fork modal (Story 3.2)
- Hover card → Show preview tooltip with first 100 characters of scenario description

**Technical Notes**:

- Cards use panda CSS utility classes for consistent styling
- Infinite scroll uses Intersection Observer API
- URL params sync with filters (`/browse?book=harry-potter&type=character-change&sort=forks`)
- Pinia store manages filter state

**Estimated Effort**: 8 hours

---

### Story 3.4: Scenario Forking Backend & Meta-Timeline Logic

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-3-story-3.4-scenario-forking-backend-meta-timeline.md`

**Description**: Implement Spring Boot API endpoint for forking scenarios to create meta-timelines, with circular reference prevention and fork tracking.

**Acceptance Criteria**:

- [ ] POST /api/scenarios/{id}/fork endpoint
- [ ] Request body includes:
  - `additional_changes`: JSONB object with new changes to apply
  - `fork_title`: Optional custom title (auto-generated if not provided)
  - `fork_description`: Optional description of what's different in this meta-fork
- [ ] Response includes newly created scenario with:
  - `parent_scenario_id` set to forked scenario's ID
  - `scenario_parameters` merged from parent + additional changes
  - `fork_count` incremented on parent scenario
- [ ] Circular reference prevention:
  - Recursive CTE query checks if new fork would create loop
  - Return 400 Bad Request if circular reference detected
  - Error message: "Cannot fork: would create circular timeline"
- [ ] Fork depth limit: max 5 levels (prevents infinite meta-fork chains)
- [ ] Parent scenario `fork_count` incremented atomically (prevent race conditions)
- [ ] Audit log: record fork event with parent_id, child_id, creator_id, timestamp
- [ ] Integration test: fork scenario → verify parent updated → fork again → verify chain

**Fork Logic Example**:

```
Original Scenario: "Hermione in Slytherin"
- parent_scenario_id: null
- scenario_parameters: { character: "Hermione", property: "house", alternate: "Slytherin", ... }

User forks with additional_changes: { additional_property: "Head Girl status", alternate: "Yes" }

New Meta-Fork: "Hermione in Slytherin AND Head Girl"
- parent_scenario_id: {original scenario ID}
- scenario_parameters: {
    character: "Hermione",
    property: "house",
    alternate: "Slytherin",
    additional_property: "Head Girl status",
    alternate: "Yes",
    ...
  }

Original scenario.fork_count → incremented from 0 to 1
```

**Technical Notes**:

- Use PostgreSQL recursive CTE to detect circular references
- JSONB merge uses `jsonb_set()` for deep merging
- Fork title auto-generation: "{parent_title} + {additional_change_summary}"
- Atomic increment using `UPDATE scenarios SET fork_count = fork_count + 1 WHERE id = ?`

**Estimated Effort**: 10 hours

---

### Story 3.5: Scenario Forking UI & Meta-Fork Creation Flow

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-3-story-3.5-scenario-forking-ui-meta-fork-creation.md`

**Description**: Build Vue.js modal interface for forking scenarios with additional change input and visual parent-child relationship preview.

**Acceptance Criteria**:

- [ ] ForkScenarioModal component triggered by "Gaji This →" button
- [ ] Modal displays:
  - Parent scenario summary (title, type, key changes)
  - "Add Changes to Create Meta-Fork" section with form:
    - For CHARACTER_CHANGE: additional property selector + alternate value
    - For EVENT_ALTERATION: additional event selector + modification
    - For SETTING_MODIFICATION: additional cultural context textarea
  - Fork title input (auto-populated, user can edit)
  - Fork description textarea (optional, 200-500 characters)
  - Preview section showing "Parent Timeline → Meta-Fork Timeline" comparison
- [ ] Validation:
  - At least one additional change required
  - Changes cannot contradict parent scenario (client-side basic check)
  - Fork title max 500 characters
- [ ] API integration: POST /api/scenarios/{id}/fork
- [ ] Success state:
  - Show "Meta-Fork Created!" confirmation
  - Display new scenario card with "View Your Meta-Fork" link
  - Increment parent scenario's fork count in UI (optimistic update)
- [ ] Error handling: circular reference → show alert "This would create an impossible timeline loop"
- [ ] Mobile responsive modal (fullscreen on <768px width)

**Fork Flow Example**:

```
User viewing: "Hermione in Slytherin"
Clicks: "Gaji This →"

Modal opens:
┌─────────────────────────────────────┐
│ Fork: Hermione in Slytherin         │
├─────────────────────────────────────┤
│ Parent Timeline Changes:            │
│ • Character: Hermione Granger       │
│ • Property: House → Slytherin       │
│ • Effects: Befriends Draco, etc.    │
├─────────────────────────────────────┤
│ Add Your Changes:                   │
│ Additional Property: [Head Girl▼]   │
│ Alternate Value: [Yes________]      │
│                                     │
│ Fork Title:                         │
│ [Hermione in Slytherin AND Head     │
│  Girl_________________________]     │
│                                     │
│ Description (optional):             │
│ [Explores how ambition + authority  │
│  would make Hermione even more      │
│  formidable_________________]       │
├─────────────────────────────────────┤
│ Preview:                            │
│ Parent: Hermione in Slytherin       │
│    ↓                                │
│ Meta-Fork: + Head Girl status       │
├─────────────────────────────────────┤
│ [Cancel]  [Create Meta-Fork →]      │
└─────────────────────────────────────┘
```

**Technical Notes**:

- Modal uses Teleport to render at document root (z-index management)
- Parent scenario data fetched from Pinia store (already loaded in browse view)
- Optimistic UI update: increment fork count immediately, rollback if API fails
- Form validation uses Vuelidate or manual validation logic

**Estimated Effort**: 8 hours

---

### Story 3.6: Scenario Search & Advanced Filtering

**Priority: P1 - High**

**Story File**: `docs/stories/epic-3-story-3.6-scenario-search-advanced-filtering.md`

**Description**: Implement full-text search for scenarios using PostgreSQL's text search capabilities, with smart filtering combining search + metadata filters.

**Acceptance Criteria**:

- [ ] Search bar in ScenarioExplorer with autocomplete
- [ ] Backend API: GET /api/scenarios/search?q={query}&book=&type=&sort=
- [ ] Full-text search on:
  - scenario_title (weighted 3x)
  - scenario_parameters JSONB → extracted text fields (weighted 2x)
  - base_story (weighted 1x)
- [ ] Search features:
  - Fuzzy matching (tolerate 1-2 typos)
  - Partial word matching ("Herm" matches "Hermione")
  - Phrase search ("Hermione Slytherin" as phrase)
  - Boolean operators: AND, OR, NOT (advanced users)
- [ ] Search results ranked by:
  - Text relevance score (PostgreSQL ts_rank)
  - Popularity (fork_count + conversation_count + like_count as tie-breaker)
- [ ] Autocomplete suggests:
  - Popular character names
  - Book titles
  - Scenario types
  - Recent searches (client-side localStorage)
- [ ] Search analytics: log queries, results count, click-through rate (for future optimization)
- [ ] Empty search results: "No scenarios found. Try different keywords or create your own!"
- [ ] Performance: search results < 200ms for 100,000+ scenarios

**Search Examples**:

- "Hermione" → Returns all scenarios featuring Hermione
- "Slytherin house" → Returns CHARACTER_CHANGE scenarios with house modifications
- "Gatsby California" → Returns scenarios where Gatsby moved to California
- "Pride Prejudice Seoul" → Returns SETTING_MODIFICATION for P&P in Seoul

**Technical Implementation**:

```sql
-- Add GIN index for full-text search
CREATE INDEX idx_scenarios_fts ON scenarios
USING GIN(to_tsvector('english',
  scenario_title || ' ' ||
  scenario_parameters::text || ' ' ||
  base_story
));

-- Search query
SELECT *, ts_rank(to_tsvector('english', scenario_title), plainto_tsquery('english', ?)) AS rank
FROM scenarios
WHERE to_tsvector('english', scenario_title || ' ' || scenario_parameters::text)
      @@ plainto_tsquery('english', ?)
ORDER BY rank DESC, fork_count DESC, conversation_count DESC
LIMIT 20;
```

**Technical Notes**:

- Use PostgreSQL's `to_tsvector()` and `ts_rank()` for relevance ranking
- JSONB text extraction: `scenario_parameters->>'character'` + other fields
- Autocomplete uses separate API: GET /api/scenarios/autocomplete?q=
- Search analytics stored in separate `search_logs` table (async write)

**Estimated Effort**: 9 hours

---

### Story 3.7: Social Sharing with og:image Generation

**Priority: P1 - High**

**Story File**: `docs/stories/epic-3-story-3.7-social-sharing-dynamic-og-image.md`

**Description**: Generate beautiful Open Graph images for scenario sharing on Twitter, Reddit, Discord, enabling viral "Check out this timeline!" posts.

**Acceptance Criteria**:

- [ ] Dynamic og:image generation endpoint: GET /api/scenarios/{id}/og-image
- [ ] Image specifications:
  - Size: 1200x630px (Twitter/Facebook recommended)
  - Format: PNG or JPEG
  - File size: < 1MB
- [ ] Image content:
  - Background: gradient matching scenario type (blue for CHARACTER_CHANGE, green for EVENT_ALTERATION, purple for SETTING_MODIFICATION)
  - Scenario title (max 80 characters, truncated with "...")
  - Base story title with book icon
  - Scenario type badge
  - Fork count + conversation count with icons
  - "Branch all of story" tagline + Gaji logo
  - Visual flourish: tree branch illustration (가지 imagery)
- [ ] HTML meta tags in scenario detail page:
  - `<meta property="og:title" content="{scenario_title} - Gaji">`
  - `<meta property="og:description" content="Explore this What If timeline: {first 150 chars}">`
  - `<meta property="og:image" content="{og-image URL}">`
  - `<meta property="og:url" content="{scenario URL}">`
  - `<meta name="twitter:card" content="summary_large_image">`
- [ ] Image caching: generated images cached on CDN (Railway CDN or Cloudflare)
- [ ] Fallback: if generation fails, serve default Gaji branded image
- [ ] Share buttons on scenario detail page:
  - Twitter: pre-populated tweet "Check out this What If timeline: {scenario_title} {URL}"
  - Reddit: pre-populated title for r/books, r/FanTheories
  - Discord: copyable link with rich preview
  - Direct link copy with "Link copied!" toast

**og:image Generation Options**:

**Option A: Server-side rendering (Puppeteer)**

- Use Headless Chrome to render HTML template → screenshot → PNG
- Pros: Full CSS control, easy to design
- Cons: Slow (1-2 seconds per image), resource-intensive

**Option B: Image library (Canvas/ImageMagick)**

- Use Java BufferedImage or ImageMagick to composite text + graphics
- Pros: Fast (<100ms per image), efficient
- Cons: More code, limited design flexibility

**Recommended**: Option B for MVP (speed), Option A for Phase 2 (richer designs)

**Technical Implementation (Option B)**:

```java
@GetMapping("/api/scenarios/{id}/og-image")
public ResponseEntity<byte[]> generateOgImage(@PathVariable UUID id) {
  Scenario scenario = scenarioRepository.findById(id);

  BufferedImage image = new BufferedImage(1200, 630, BufferedImage.TYPE_INT_RGB);
  Graphics2D g = image.createGraphics();

  // Draw gradient background
  g.setPaint(getGradientForType(scenario.getScenarioType()));
  g.fillRect(0, 0, 1200, 630);

  // Draw scenario title
  g.setFont(new Font("Arial", Font.BOLD, 48));
  g.setColor(Color.WHITE);
  g.drawString(truncate(scenario.getScenarioTitle(), 80), 50, 200);

  // Draw metadata
  g.setFont(new Font("Arial", Font.PLAIN, 32));
  g.drawString("From: " + scenario.getBaseStory(), 50, 300);
  g.drawString("Forks: " + scenario.getForkCount(), 50, 400);

  // Draw logo + tagline
  g.drawString("Gaji: Branch all of story", 50, 580);

  // Convert to PNG bytes
  ByteArrayOutputStream baos = new ByteArrayOutputStream();
  ImageIO.write(image, "png", baos);

  return ResponseEntity.ok()
    .contentType(MediaType.IMAGE_PNG)
    .body(baos.toByteArray());
}
```

**Technical Notes**:

- Cache images in Redis (key: `og-image:{scenario_id}`, TTL: 7 days)
- Serve cached images via CDN for fast social media scraping
- Update cache when scenario metadata changes (title, fork count)
- Tree branch SVG illustration as overlay (pre-rendered asset)

**Estimated Effort**: 10 hours

---

## Epic-Level Acceptance Criteria

- [ ] Users can browse 100+ scenarios without performance issues
- [ ] Forking creates valid meta-scenarios with correct parent-child relationships
- [ ] Search returns relevant results in < 200ms for typical queries
- [ ] Social sharing generates og:images that preview correctly on Twitter, Reddit, Discord
- [ ] No circular reference errors in production (first 3 months)
- [ ] Viral sharing: 10%+ of users share at least one scenario on social media (Phase 1 target)

## Dependencies

**Blocks**:

- Epic 4: Conversation System (users discover scenarios before starting conversations)
- Epic 5: Scenario Tree Visualization (tree view displays forked scenarios from this epic)

**Requires**:

- Epic 1: What If Scenario Foundation (needs scenario data, API endpoints)
- Frontend infrastructure (Vue.js, panda CSS, Pinia)
- Backend infrastructure (Spring Boot, PostgreSQL)

## Success Metrics

**Technical Metrics**:

- Search latency < 200ms (p95) for 100,000+ scenarios
- og:image generation < 100ms (p95) with caching
- Fork API < 150ms (p95) including database write + parent update
- Zero circular reference bugs in production

**User Metrics** (Phase 1 - 3 months):

- 60%+ of users browse scenarios before creating their own (validates discovery-first flow)
- 40%+ scenario fork rate (proves scenarios inspire meta-exploration)
- 10%+ social sharing rate (users share scenarios on Twitter/Reddit/Discord)
- 30%+ of new users arrive via shared links (validates viral growth)
- Qualitative: "I found an amazing timeline and gaji'd it!" user feedback

## Risk Mitigation

**Risk 1: Poor scenario discoverability → users don't find quality content**

- Mitigation: Multi-dimensional filtering (book, type, popularity)
- Mitigation: Smart sorting (Most Gaji'd, Most Discussed, Highest Rated)
- Mitigation: Search with autocomplete reduces friction
- Mitigation: Curated "Timeline of the Week" editorial picks (deferred to Phase 2)

**Risk 2: Forking creates contradictory meta-scenarios**

- Mitigation: Client-side validation before fork submission
- Mitigation: Local LLM validation (Story 1.5) checks coherence
- Mitigation: User can report contradictory scenarios (Phase 2 feature)

**Risk 3: Social sharing doesn't drive viral growth**

- Mitigation: Eye-catching og:images optimized for social platforms
- Mitigation: Pre-populated tweets/posts reduce sharing friction
- Mitigation: "Share to unlock analytics" incentive (Phase 2)
- Mitigation: A/B test different og:image designs

**Risk 4: Search doesn't return relevant results**

- Mitigation: Weighted ranking (title > parameters > book)
- Mitigation: Quality score boost for high-rated scenarios
- Mitigation: Search analytics identify poor queries for optimization
- Mitigation: Autocomplete guides users to successful searches

## Technical Debt Decisions

**Accepted Debt** (to be addressed post-MVP):

- No ML-based recommendation engine (using popularity metrics: likes, forks, conversations)
- No collaborative filtering ("Users who forked X also forked Y")
- No saved searches or followed books
- No "Trending Timelines" real-time feed (using static sorting)
- No advanced analytics dashboard for scenario creators

**Won't Build** (architectural decisions):

- Real-time scenario updates (polling is sufficient for MVP)
- Scenario merge functionality (forking is one-way)
- Multi-level undo for forks (no rollback)

## Testing Strategy

**Unit Tests**:

- Fork logic: circular reference detection, fork count increment
- Search ranking algorithm accuracy
- og:image generation with various scenario types

**Integration Tests**:

- Browse → filter → paginate → verify results
- Fork scenario → verify parent updated → verify child created
- Search → verify relevance ranking → verify performance
- Generate og:image → verify format → verify caching

**E2E Tests**:

- User browses scenarios → filters by book → sorts by forks → forks scenario → shares on Twitter
- User searches "Hermione" → clicks result → views scenario detail
- og:image preview on Twitter using Twitter Card Validator

**Performance Tests**:

- Browse 100,000+ scenarios with various filters (< 200ms)
- Concurrent forking (100 users fork same scenario simultaneously)
- Search load test (1,000 queries/second)
- og:image generation (100 images/second with caching)

## Open Questions

1. **Q**: Should we limit fork depth? (e.g., max 5 levels of meta-forks)
   **A**: Yes, max 5 levels. Prevents complexity explosion. Return 400 error: "Fork depth limit reached."

2. **Q**: What happens if parent scenario is deleted while child scenarios exist?
   **A**: Soft delete only. Children preserved, marked as "orphaned" with note: "Parent timeline deleted."

3. **Q**: Should search index scenario conversations for deeper relevance?
   **A**: Not in MVP. Scenarios only. Phase 2 can add conversation text indexing.

4. **Q**: How to handle offensive scenario sharing on social media?
   **A**: Validation system (Story 1.5) filters pre-publish. User reports → manual review → hide scenario + update og:image cache.

5. **Q**: Should we track which social platforms users share to?
   **A**: Yes. Log share events with platform (Twitter/Reddit/Discord) for analytics. Privacy-safe (no user data).

## Definition of Done

- [ ] All 7 stories completed with acceptance criteria met
- [ ] Browse UI functional with filtering, sorting, pagination
- [ ] Forking creates valid meta-scenarios with parent-child tracking
- [ ] Search returns relevant results < 200ms for 100,000 scenarios
- [ ] og:images generate correctly for Twitter, Reddit, Discord
- [ ] Unit tests >80% coverage on fork logic, search ranking
- [ ] Integration tests passing for all API endpoints
- [ ] E2E tests: browse → fork → share workflow complete
- [ ] Performance benchmarks met (< 200ms search, < 100ms og:image with cache)
- [ ] Social sharing verified on Twitter using Card Validator
- [ ] Code review completed, no P0/P1 issues
- [ ] Deployed to Railway staging, smoke tested with 20+ scenarios

---

**Epic Owner**: Frontend Lead + Backend Lead (joint ownership)

**Start Date**: Week 2, Day 3 of MVP development (parallel with Epic 2)

**Target Completion**: Week 3, Day 2 (6 working days)

**Estimated Total Effort**: 63 hours (achievable within 2 weeks for 2 engineers)
