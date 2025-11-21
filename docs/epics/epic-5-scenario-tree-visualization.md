# Epic 5: Scenario Tree Visualization

## Epic Goal

Build intuitive tree visualization components that display scenario fork hierarchies and conversation branch structures, enabling users to navigate complex multi-timeline networks and understand relationships between alternate What If scenarios.

## User Value

Users can visually explore how scenarios branch from each other (meta-timelines), see which conversations forked from where, and navigate through complex decision trees without getting lost. The visual representation makes the platform's core "branching timelines" concept immediately tangible and browsable.

## Timeline

**Week 3, Day 1-3 of MVP development**

## Stories

### Story 5.1: Scenario Tree Data Structure & API

**Priority: P1 - High**

**Description**: Build backend API endpoints to retrieve scenario hierarchies (parent-child relationships) and conversation fork trees with efficient recursive queries.

**Acceptance Criteria**:

- [ ] ScenarioTreeService with methods:
  - `getScenarioTree(UUID scenarioId) → ScenarioTreeNode`
  - `getScenarioAncestors(UUID scenarioId) → List<ScenarioResponse>` (breadcrumb path)
  - `getScenarioChildren(UUID scenarioId) → List<ScenarioResponse>` (direct children)
  - `getScenarioSiblings(UUID scenarioId) → List<ScenarioResponse>` (same parent)
- [ ] ConversationTreeService with methods:
  - `getConversationParent(UUID conversationId) → ConversationResponse` (returns parent if exists, null if root)
  - `getConversationChild(UUID conversationId) → ConversationResponse` (returns child if exists, null if not forked)
  - `getConversationForkRelationship(UUID conversationId) → ConversationForkRelationshipDTO` (returns {parent, current, child} - max 2 non-null)
  - `isRootConversation(UUID conversationId) → boolean` (check if parent_conversation_id IS NULL)
  - `hasBeenForked(UUID conversationId) → boolean` (check has_been_forked flag)
- [ ] REST API endpoints:
  - GET /api/v1/scenarios/{id}/tree (full tree structure - scenarios only)
  - GET /api/v1/scenarios/{id}/ancestors (breadcrumb path - scenarios only)
  - GET /api/v1/scenarios/{id}/children (direct children only - scenarios only)
  - GET /api/v1/scenarios/{id}/siblings (same parent scenarios)
  - **GET /api/v1/conversations/{id}/parent** (returns parent conversation if exists, 404 if root)
  - **GET /api/v1/conversations/{id}/child** (returns child conversation if exists, 404 if not forked)
  - **GET /api/v1/conversations/{id}/fork-relationship** (returns {parent, current, child} DTO with fork status)
- [ ] Tree data structure (JSON response - scenarios only):
  ```json
  {
    "id": "uuid",
    "title": "Hermione in Slytherin",
    "type": "CHARACTER_CHANGE",
    "depth": 2,
    "fork_count": 3,
    "conversation_count": 15,
    "parent_id": "parent-uuid",
    "children": [
      {
        "id": "child-uuid-1",
        "title": "Hermione befriends Draco",
        "type": "EVENT_ALTERATION",
        "depth": 3,
        "fork_count": 1,
        "conversation_count": 8,
        "children": [...]
      },
      // ... more children
    ]
  }
  ```
- [ ] **Conversation Fork Relationship DTO** (simplified for max depth 1):
  ```json
  {
    "current": {
      "id": "current-uuid",
      "first_message_preview": "How do you feel about...",
      "is_root": true,
      "has_been_forked": true,
      "message_count": 15,
      "like_count": 5,
      "creator": { "username": "user1", "avatar_url": "..." }
    },
    "parent": null, // null if current is root, otherwise parent conversation data
    "child": {
      "id": "child-uuid",
      "first_message_preview": "But what about...",
      "is_root": false,
      "has_been_forked": false,
      "message_count": 8,
      "like_count": 2,
      "copied_message_count": 6, // min(6, parent's total messages)
      "creator": { "username": "user2", "avatar_url": "..." }
    },
    "fork_status": "root_forked" // "root_can_fork" | "root_forked" | "fork"
  }
  ```
- [ ] **Simplified SQL queries for conversations (NO recursive CTE needed)**:

  ```sql
  -- Get parent (if current is a fork)
  SELECT * FROM conversations WHERE id = (
    SELECT parent_conversation_id FROM conversations WHERE id = ?
  );

  -- Get child (if current is a root that has been forked)
  SELECT * FROM conversations WHERE parent_conversation_id = ?;

  -- Get fork relationship (max 2 queries, no recursion)
  -- Query 1: Get current + parent
  SELECT c1.*, c2.* FROM conversations c1
  LEFT JOIN conversations c2 ON c1.parent_conversation_id = c2.id
  WHERE c1.id = ?;

  -- Query 2: Get child (only if c1.has_been_forked = true)
  SELECT * FROM conversations WHERE parent_conversation_id = ?;
  ```

- [ ] Recursive SQL query using Common Table Expressions (CTE) **for scenarios only**:
  ```sql
  WITH RECURSIVE scenario_tree AS (
    SELECT id, parent_scenario_id, scenario_title, scenario_type, 0 as depth
    FROM scenarios WHERE id = ?
    UNION ALL
    SELECT s.id, s.parent_scenario_id, s.scenario_title, s.scenario_type, st.depth + 1
    FROM scenarios s
    INNER JOIN scenario_tree st ON s.parent_scenario_id = st.id
    WHERE st.depth < 5  -- Max depth limit
  )
  SELECT * FROM scenario_tree ORDER BY depth, created_at
  ```
- [ ] Max tree depth validation (limit to 5 levels to prevent infinite recursion)
- [ ] Performance optimization:
  - Cache tree structure (Redis, 5-minute TTL)
  - Lazy loading for deep trees (load children on demand)
  - Index on parent_scenario_id for fast child queries
- [ ] Business rules:
  - Circular reference prevention (already enforced in Epic 1)
  - Deleted scenarios excluded from tree
  - Orphaned scenarios (parent deleted) show as root nodes
- [ ] Unit tests for tree building logic
- [ ] Integration tests for tree API endpoints
- [ ] Performance test: tree with 100+ nodes loads in <500ms

**API Example**:

**GET /api/v1/scenarios/{id}/tree**

```json
Response (200 OK):
{
  "id": "root-uuid",
  "title": "What if Hermione was in Slytherin?",
  "type": "CHARACTER_CHANGE",
  "depth": 0,
  "fork_count": 3,
  "conversation_count": 42,
  "quality_score": 85,
  "creator": {
    "username": "hermione_fan",
    "avatar_url": "https://..."
  },
  "parent_id": null,
  "children": [
    {
      "id": "child-1",
      "title": "Hermione befriends Draco in Year 1",
      "type": "EVENT_ALTERATION",
      "depth": 1,
      "fork_count": 2,
      "conversation_count": 15,
      "parent_id": "root-uuid",
      "children": [
        {
          "id": "grandchild-1",
          "title": "Draco introduces Hermione to Lucius",
          "type": "EVENT_ALTERATION",
          "depth": 2,
          "fork_count": 0,
          "conversation_count": 5,
          "parent_id": "child-1",
          "children": []
        }
      ]
    },
    {
      "id": "child-2",
      "title": "Hermione competes with Draco for top grades",
      "type": "CHARACTER_CHANGE",
      "depth": 1,
      "fork_count": 1,
      "conversation_count": 20,
      "parent_id": "root-uuid",
      "children": [...]
    }
  ]
}
```

**Technical Notes**:

- Use PostgreSQL recursive CTEs for efficient tree queries
- Denormalize depth for faster rendering (calculate on scenario creation)
- Cache full tree in Redis with scenario_id as key
- Invalidate cache on scenario creation/deletion
- Add `tree_position` column for custom ordering (Phase 2)

**Estimated Effort**: 8 hours

---

### Story 5.2: Interactive Scenario Tree Visualization Component

**Priority: P1 - High**

**Description**: Build responsive Vue component that renders scenario trees as interactive visual diagrams with expandable nodes, zoom/pan controls, and navigation.

**Acceptance Criteria**:

- [ ] ScenarioTreeVisualization component
  - Renders tree using SVG or Canvas (SVG for MVP, better accessibility)
  - Tree layout algorithms: horizontal or vertical layout (user preference)
  - Node rendering:
    - Rounded rectangle with scenario title (truncated to 30 chars)
    - Scenario type badge (CHARACTER_CHANGE, EVENT_ALTERATION, etc.)
    - Metadata: fork count, conversation count
    - Color coding by scenario type (consistent with Epic 1)
    - Highlight current scenario (bold border)
  - Edge/connector rendering:
    - Curved lines connecting parent to children (Bezier curves)
    - Arrow indicators showing fork direction
    - Line thickness based on conversation_count (popular paths thicker)
  - Interaction:
    - Click node → navigate to scenario detail page
    - Hover node → show tooltip with full title, creator, quality score
    - Expandable nodes: collapsed by default beyond depth 2
    - Click expand icon → load and render children
    - Double-click node → expand/collapse all descendants
  - Zoom/pan controls:
    - Zoom in/out buttons (or mouse wheel)
    - Pan by dragging background
    - "Fit to view" button (auto-zoom to show full tree)
    - "Center on current" button (focus on active scenario)
  - Mobile support:
    - Touch gestures: pinch to zoom, drag to pan
    - Simplified layout (vertical only, larger nodes)
    - Collapsible by default (expand on tap)
- [ ] TreeStore (Pinia) with state:
  - `currentTree` (scenario tree data)
  - `expandedNodes` (Set of expanded node IDs)
  - `viewportState` (zoom level, pan offset)
  - Actions:
    - `loadScenarioTree(scenarioId)`
    - `toggleNodeExpand(nodeId)`
    - `expandAll()`, `collapseAll()`
    - `centerOnNode(nodeId)`
- [ ] Layout algorithm:
  - Use Reingold-Tilford algorithm for tree layout
  - Alternative: D3.js tree layout (if using D3)
  - Node spacing: min 100px horizontal, 80px vertical
  - Auto-calculate canvas size based on tree dimensions
- [ ] Performance optimization:
  - Virtualization for large trees (render only visible nodes)
  - Lazy rendering: load children on expand
  - Debounce zoom/pan events (60fps smooth)
  - Canvas rendering for >100 nodes (better performance)
- [ ] Accessibility:
  - Keyboard navigation (Tab, Arrow keys, Enter)
  - Screen reader support (ARIA tree role)
  - Focus indicators for keyboard users
- [ ] Empty state: "This scenario has no forks yet. Be the first to fork it!"

**Tree Visualization Layout (Horizontal)**:

```
                    ┌────────────────────┐
                    │ Hermione in        │
                    │ Slytherin          │
                    │ 🔵 CHARACTER       │
                    │ ↗ 3  💬 42         │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼────────┐  ┌──▼──────────┐  ┌─▼──────────────┐
    │ Befriends Draco  │  │ Competes    │  │ Joins Dark    │
    │ 🟡 EVENT         │  │ with Draco  │  │ Arts Club     │
    │ ↗ 2  💬 15       │  │ 🔵 CHAR     │  │ 🟡 EVENT      │
    └─────────┬────────┘  │ ↗ 1  💬 20  │  │ ↗ 0  💬 7     │
              │           └─────────────┘  └───────────────┘
              │
    ┌─────────▼──────────┐
    │ Meets Lucius       │
    │ 🟡 EVENT           │
    │ ↗ 0  💬 5          │
    └────────────────────┘

Legend:
🔵 CHARACTER_CHANGE  🟡 EVENT_ALTERATION  🟢 SETTING_MODIFICATION
↗ Fork count  💬 Conversation count
```

**Technical Notes**:

- Use D3.js for tree layout (well-tested library) or implement Reingold-Tilford
- SVG for smaller trees (<50 nodes), Canvas for larger trees
- Store viewport state in Pinia (persist zoom/pan across navigation)
- Use `requestAnimationFrame` for smooth zoom/pan animations
- Implement virtual scrolling for trees >100 nodes

**Estimated Effort**: 14 hours

---

### Story 5.3: Conversation Fork Tree UI (Simplified for Max Depth 1)

**Priority: P2 - Medium**

**Description**: Build **simplified** conversation fork relationship display showing parent-child connection (max depth 1: ROOT → fork only), integrated into conversation detail page. No complex tree structure needed - just a simple 2-node parent-child visualization.

**Acceptance Criteria**:

- [ ] ConversationForkRelationship component (simple 2-node structure)
  - **Simple vertical or horizontal layout** (root → child, max 2 nodes total)
  - **No tree algorithm needed** - just display parent + child if they exist
  - Node rendering:
    - First user message as node label (truncated to 40 chars)
    - Badge: "ROOT" (green) for original conversations, "FORK" (blue) for forked conversations
    - "📋 6 messages preserved" indicator on fork nodes (shows min(6, total) value)
    - Like count (♥ X), message count (💬 Y)
    - Creator username
  - **Simple 2-level layout** (parent above/left, child below/right)
  - Click node → navigate to that conversation
  - Highlight current conversation with border
  - **Show fork status indicators**:
    - Root not forked: "✓ Can fork" (green)
    - Root forked: "✗ Already forked" (gray)
    - Forked conversation: "⚠️ Cannot fork again" (orange)
- [ ] Integration in ConversationView (Story 4.3):
  - "View Fork Relationship" button in conversation header (only show if parent or child exists)
  - Opens modal or sidebar showing 2-level structure
  - **If conversation is ROOT**: show self + child (if child exists via `GET /api/v1/conversations/{id}/child`)
  - **If conversation is FORK**: show parent + self (via `GET /api/v1/conversations/{id}/parent`)
  - Badge in conversation header: "ROOT (can fork)" or "ROOT (forked)" or "FORK (depth 1)"
- [ ] ConversationForkRelationshipModal component:
  - Modal overlay with simple 2-node visualization
  - Close button
  - Mobile-friendly (full-screen on mobile)
  - Shows **parent-child only**: root → fork (max 2 nodes, no recursion)
  - Clear labels: "Original Conversation" and "Forked Conversation"
  - Display "📋 X messages preserved from parent" on fork node
- [ ] ConversationStore actions (Pinia):
  - `loadConversationParent(conversationId)` - fetch parent if exists
  - `loadConversationChild(conversationId)` - fetch child if exists
  - `getConversationForkStatus(conversationId)` - returns "root_can_fork" | "root_forked" | "fork"
- [ ] **Simple navigation** (no complex tree):
  - Click root node → navigate to original conversation
  - Click fork node → navigate to forked conversation
  - Show "📋 6 messages preserved from parent" indicator on fork node
  - Show "⚠️ Cannot be forked again (max depth 1)" indicator on fork node
- [ ] Backend API endpoints (from Story 5.1):

  - GET /api/v1/conversations/{id}/parent → returns parent conversation if exists (NULL if root)
  - GET /api/v1/conversations/{id}/child → returns child conversation if exists (NULL if not forked)
  - Simple queries (no recursive CTE needed):

    ```sql
    -- Get parent
    SELECT * FROM conversations WHERE id = (SELECT parent_conversation_id FROM conversations WHERE id = ?)

    -- Get child
    SELECT * FROM conversations WHERE parent_conversation_id = ?
    ```

- [ ] Performance:
  - Load relationship on demand (simple queries: parent + child)
  - Cache structure (Redis, 5-minute TTL) - just 2 rows max
  - No virtualization needed (always ≤ 2 nodes)
- [ ] Empty states:
  - Root not forked: "This conversation has not been forked yet. You can fork it **once**."
  - Fork conversation: "This is a forked conversation (depth 1). It **cannot be forked again**. Only ROOT conversations can be forked."
  - Orphaned fork (parent deleted): "Parent conversation deleted" (show grayed-out parent placeholder)

**Conversation Fork Relationship** (Max Depth 1: ROOT → Fork Only):

```
┌─────────────────────────────────┐
│ ROOT: "How do you feel..."      │
│ 💬 15  ♥ 5                      │
│ [Original Conversation]         │
│ ✓ Can fork (not forked yet)     │
└────────────┬────────────────────┘
             │ (ONE fork allowed only)
             ▼
┌─────────────────────────────────┐
│ FORK: "But what about..."       │
│ 💬 8  ♥ 2                       │
│ [Forked Conversation - Depth 1] │
│ 📋 6 msgs preserved from parent │
│ ⚠️  Cannot fork again (max depth 1) │
└─────────────────────────────────┘

Note: Only ROOT conversations (parent_conversation_id IS NULL)
can be forked, and only ONCE. Forked conversations cannot be
forked again (architectural constraint: max depth = 1).

INVALID (prevented by system):
┌─────────────────────────────────┐
│ ROOT: "How do you feel..."      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ FORK: "But what about..."       │
│ (is_root = FALSE)               │
└────────────┬────────────────────┘
             │ ❌ NOT ALLOWED (403 Forbidden)
             ▼
┌─────────────────────────────────┐
│ FORK of FORK ❌                 │
│ (Depth 2 - BLOCKED by backend)  │
│ Backend returns 403 Forbidden   │
└─────────────────────────────────┘
```

**Technical Notes**:

- **Extremely simple layout** (max 2 nodes: parent + child)
- **No tree algorithm needed** - just simple parent-child relationship display
- **No recursive queries** - trivial SQL: `SELECT parent WHERE id = parent_conversation_id` or `SELECT child WHERE parent_conversation_id = ?`
- **Simpler styling than scenario tree** (less visual weight, minimal design)
- **Lazy load relationship** (only when user clicks "View Fork Relationship" button)
- **Mobile**: full-screen modal, vertical layout (root above, fork below)
- **Database query example**:
  ```sql
  -- Get fork relationship (max 2 rows returned)
  SELECT * FROM conversations
  WHERE id = ? -- current conversation
     OR parent_conversation_id = ? -- child of current (if current is root)
     OR id = (SELECT parent_conversation_id FROM conversations WHERE id = ?) -- parent of current (if current is fork)
  LIMIT 2; -- max 2 rows: parent + current OR current + child
  ```
- **Frontend logic**:
  ```javascript
  const relationship = await conversationStore.loadForkRelationship(
    conversationId
  );
  // relationship.parent: null if current is root, or parent data if current is fork
  // relationship.child: null if not forked, or child data if current is root with fork
  // relationship.current: current conversation data
  // relationship.forkStatus: "root_can_fork" | "root_forked" | "fork"
  ```

**Estimated Effort**: **6 hours** (reduced from 8 hours due to simplification - no complex tree logic needed)

---

## Epic-Level Acceptance Criteria

- [ ] Tree data structure correctly represents parent-child relationships
- [ ] Interactive tree visualization renders scenario hierarchy
- [ ] Conversation fork trees show ROOT → child relationship (max depth 1)
- [ ] Users can navigate tree by clicking nodes
- [ ] Performance optimized for large trees (virtual scrolling)
- [ ] Mobile responsive design
- [ ] Accessibility support (keyboard navigation)

**Technical Notes**:

- Use CSS `overflow-x: auto` for horizontal scroll on mobile
- Implement "scroll into view" for current scenario
- Cache breadcrumb data in Pinia (avoid repeated API calls)
- Use `position: sticky` for breadcrumb (stays visible on scroll)

**Estimated Effort**: 4 hours

---

### Story 5.5: Tree Minimap & Overview Panel

**Priority: P2 - Medium**

**Description**: Add minimap and overview panel for large scenario trees, helping users orient themselves in complex hierarchies.

**Acceptance Criteria**:

- [ ] TreeMinimap component
  - Small overview of entire tree (150px × 150px)
  - Simplified rendering: nodes as dots, edges as lines
  - Current viewport highlighted (semi-transparent rectangle)
  - Drag viewport rectangle to pan main tree
  - Click on minimap → jump to that area of tree
  - Toggle button to show/hide minimap
- [ ] TreeOverviewPanel component
  - Sidebar showing tree statistics:
    - Total scenarios in tree: X
    - Max depth: Y levels
    - Total forks: Z
    - Most popular branch (highest conversation_count)
  - List of "Featured Scenarios" (top 5 by likes or conversations)
  - Click scenario → jump to that node in tree
  - Collapsible panel (default: collapsed on mobile)
- [ ] Integration in ScenarioTreeVisualization:
  - Minimap in bottom-right corner
  - Overview panel in right sidebar (desktop) or collapsible (mobile)
  - Sync viewport: pan/zoom main tree → update minimap
- [ ] Performance:
  - Render minimap using Canvas (faster for large trees)
  - Update minimap on debounce (300ms after pan/zoom)
  - Lazy render overview panel (only when visible)
- [ ] Accessibility:
  - Keyboard shortcut to toggle minimap (M key)
  - Screen reader: describe tree structure in overview panel

**Minimap Layout**:

```
Main Tree (SVG):
┌─────────────────────────────────────┐
│                                     │
│   [Large scenario tree visual]     │
│                                     │
│                                     │
│              ┌──────────────┐       │
│              │ Minimap      │       │ ← Bottom-right corner
│              │ [Tree dots]  │       │
│              │ [Viewport ▭] │       │
│              └──────────────┘       │
└─────────────────────────────────────┘
```

**Overview Panel**:

```
Tree Overview
─────────────────
Total Scenarios: 42
Max Depth: 4 levels
Total Forks: 37
Total Conversations: 156

Featured Scenarios:
1. Hermione befriends... (42 💬)
2. Competes with Draco (35 💬)
3. Joins Dark Arts... (28 💬)

[View All Scenarios →]
```

**Technical Notes**:

- Use Canvas 2D API for minimap (better performance)
- Update minimap only when pan/zoom stops (debounce)
- Cache featured scenarios (updated hourly)
- Minimap viewport dragging: convert minimap coords to main tree coords

**Estimated Effort**: 7 hours

---

### Story 5.6: Tree Export & Sharing

**Priority: P3 - Low (Nice-to-Have)**

**Description**: Enable users to export scenario trees as images or shareable links with custom views.

**Acceptance Criteria**:

- [ ] Export tree as PNG image
  - "Export" button in tree visualization toolbar
  - Render entire tree to PNG (even if larger than viewport)
  - Max resolution: 4000×4000px (to prevent memory issues)
  - Download file: `{scenario-title}-tree.png`
  - Include watermark: "Gaji - What If Scenarios" in corner
- [ ] Share tree view with custom state
  - Generate shareable link with viewport state encoded
  - URL format: `/scenarios/{id}/tree?zoom=1.5&center=node-uuid&expanded=node1,node2`
  - Parse URL params on load → restore viewport state
  - Social sharing: generate og:image showing tree preview
- [ ] TreeExportModal component:
  - Export format options: PNG, SVG (future: PDF)
  - Customize export: include/exclude metadata, adjust size
  - Preview before export
  - "Copy shareable link" button
- [ ] Backend support:
  - GET /api/v1/scenarios/{id}/tree-image.png (server-side rendering)
  - Use headless browser (Puppeteer) or Java image library
  - Cache generated images (Redis, 1-hour TTL)
  - Serve via CDN for sharing
- [ ] Social sharing optimization:
  - og:image shows tree preview (1200×630px)
  - Twitter card with tree visual
  - Include scenario title, fork count in meta description

**Export Dialog**:

```
┌────────────────────────────────────┐
│ Export Scenario Tree               │
├────────────────────────────────────┤
│ Format:                            │
│ ○ PNG Image (recommended)          │
│ ○ SVG Vector                       │
│                                    │
│ Size:                              │
│ ○ Fit to content (auto)            │
│ ○ Custom (4000×3000px)             │
│                                    │
│ Include:                           │
│ ☑ Scenario titles                  │
│ ☑ Metadata (forks, conversations)  │
│ ☐ Creator usernames                │
│                                    │
│ [Preview]  [Export]  [Cancel]      │
└────────────────────────────────────┘
```

**Technical Notes**:

- Use html2canvas or dom-to-image for client-side PNG export
- SVG export: serialize SVG DOM to file
- Server-side rendering: Puppeteer with headless Chrome
- Cache exported images (scenario_id + timestamp as key)
- Invalidate cache on scenario tree changes

**Estimated Effort**: 6 hours

---

## Epic-Level Acceptance Criteria

- [ ] Users can view scenario fork hierarchies as interactive trees
- [ ] Tree visualization loads in <500ms for trees with 50+ nodes
- [ ] Conversation fork trees display correctly in conversation view
- [ ] Breadcrumb navigation works on all scenario pages
- [ ] Tree zoom/pan controls are smooth (60fps)
- [ ] Mobile-responsive tree view (touch gestures work)
- [ ] Minimap accurately reflects viewport position
- [ ] Tree export generates valid PNG/SVG files
- [ ] Keyboard navigation works for accessibility
- [ ] No performance degradation on trees with 100+ nodes

## Dependencies

**Blocks**:

- None (tree visualization is enhancement, not blocker)

**Requires**:

- Epic 0: Project Setup & Infrastructure (database, frontend)
- Epic 1: What If Scenario Foundation (scenario parent_scenario_id relationships)
- Epic 4: Conversation System (conversation parent_conversation_id for fork trees)

## Success Metrics

**Technical Metrics**:

- Tree rendering time < 500ms for 50-node trees (p95)
- Tree rendering time < 2s for 200-node trees (p95)
- Zoom/pan frame rate > 60fps
- Recursive query performance < 100ms (p95)
- Cache hit rate > 80% for tree data
- Export image generation < 3s (p95)

**User Metrics** (Phase 1 - 3 months):

- 40%+ users view tree visualization at least once
- 20%+ users use zoom/pan controls
- 15%+ users click tree nodes to navigate
- 10%+ users export tree as image
- 5%+ users share tree links

## Visual Design Guidelines

**Color Palette** (Scenario Types):

- CHARACTER_CHANGE: Blue (#3B82F6)
- EVENT_ALTERATION: Yellow (#F59E0B)
- SETTING_MODIFICATION: Green (#10B981)

**Node Styling**:

- Border: 2px solid {color}
- Background: White (#FFFFFF)
- Hover: Background → {color} with 10% opacity
- Selected: Border → 4px, shadow effect

**Edge Styling**:

- Color: Gray (#9CA3AF)
- Thickness: 2px (normal), 4px (popular paths with >10 conversations)
- Style: Curved Bezier (smooth, organic look)

**Typography**:

- Scenario title: 14px, semibold
- Metadata: 12px, regular
- Breadcrumb: 13px, medium

**Spacing**:

- Node padding: 12px horizontal, 8px vertical
- Node spacing: 100px horizontal, 80px vertical
- Minimap margin: 16px from edges

## Performance Optimization Strategies

**Large Tree Handling** (>100 nodes):

1. **Virtualization**: Render only nodes in viewport + buffer
2. **Progressive Loading**: Load children on expand (lazy loading)
3. **Canvas Rendering**: Switch from SVG to Canvas for better performance
4. **Level-of-Detail**: Show less metadata when zoomed out
5. **Debouncing**: Debounce zoom/pan events (60fps cap)

**Caching Strategy**:

- Tree data: Redis cache, 5-minute TTL
- Breadcrumb paths: In-memory cache (Pinia), session-scoped
- Exported images: Redis cache, 1-hour TTL
- Featured scenarios: Redis cache, 1-hour TTL

**Database Optimization**:

- Index on parent_scenario_id (B-tree)
- Index on parent_conversation_id (B-tree)
- Denormalize depth column (avoid recursive calculation)
- Use prepared statements for recursive queries

## Risk Mitigation

**Risk 1: Performance degradation on very large trees (>500 nodes)**

- Mitigation: Implement virtualization (only render visible nodes)
- Mitigation: Switch to Canvas rendering automatically
- Mitigation: Add pagination (show one subtree at a time)
- Mitigation: Warn users when creating deep trees (>5 levels)

**Risk 2: Circular reference bugs (scenario points to ancestor)**

- Mitigation: Validate on scenario creation (Epic 1 has prevention)
- Mitigation: Add max recursion depth in SQL query (LIMIT 5)
- Mitigation: Weekly cron job to detect and break circular refs

**Risk 3: Mobile UX challenges (small screen, complex tree)**

- Mitigation: Vertical-only layout on mobile
- Mitigation: Simplified nodes (less metadata)
- Mitigation: Touch-optimized controls (larger buttons, gestures)
- Mitigation: Collapsible by default (expand on tap)

**Risk 4: Browser crashes on export (out of memory)**

- Mitigation: Limit max export resolution (4000×4000px)
- Mitigation: Server-side rendering for very large exports
- Mitigation: Progressive PNG rendering (chunks)
- Mitigation: Warn user before exporting >100-node tree

## Technical Debt Decisions

**Accepted Debt** (to be addressed post-MVP):

- No custom tree layouts (only horizontal/vertical, no radial or circular)
- No tree animation (nodes don't animate when expanding)
- No collaborative tree editing (multi-user view)
- No tree comparison (side-by-side different trees)
- No tree diff (show changes between versions)
- Simple minimap (no zoom levels, no filtering)

**Won't Build** (architectural decisions):

- 3D tree visualization (2D sufficient for MVP)
- Force-directed graph layout (tree layout clearer)
- Timeline scrubbing (show tree evolution over time)
- Tree merging (only forking, no merging branches)

## Testing Strategy

**Unit Tests**:

- Tree building logic (recursive query results → tree structure)
- Breadcrumb path calculation (scenario → ancestors list)
- Tree depth calculation
- Circular reference detection

**Integration Tests**:

- GET /scenarios/{id}/tree → returns valid tree JSON
- GET /scenarios/{id}/ancestors → returns breadcrumb path
- Tree includes all descendants up to max depth
- Deleted scenarios excluded from tree

**Visual Regression Tests**:

- Tree rendering matches design mockups
- Node positioning correct (Reingold-Tilford algorithm)
- Zoom/pan viewport updates correctly
- Minimap viewport rectangle position accurate

**Performance Tests**:

- Load tree with 50 nodes → renders in <500ms
- Load tree with 200 nodes → renders in <2s
- Zoom/pan 100 times → maintains 60fps
- Export tree with 100 nodes → generates PNG in <3s

**Accessibility Tests**:

- Keyboard navigation (Tab, Arrow keys)
- Screen reader announces tree structure
- Focus indicators visible
- ARIA tree role applied

## Open Questions

1. **Q**: Should we support other tree layouts (radial, circular)?
   **A**: Not for MVP. Horizontal/vertical sufficient. Radial layout in Phase 2 if users request.

2. **Q**: Maximum tree depth before we warn users?
   **A**: 5 levels (enforced in Epic 1). Warn at 4 levels: "This tree is getting deep!"

3. **Q**: Should tree nodes show thumbnails (scenario preview images)?
   **A**: Not for MVP (performance concerns). Text-only nodes. Images in Phase 2.

4. **Q**: Can users rearrange tree nodes (custom ordering)?
   **A**: Not for MVP (chronological by created_at). Custom ordering in Phase 2.

5. **Q**: Should we support collapsing branches (hide entire subtrees)?
   **A**: Yes, implement in Story 5.2 (collapse beyond depth 2 by default).

6. **Q**: Export format for conversation trees?
   **A**: Same as scenario trees (PNG, SVG). Conversation trees typically smaller.

## Definition of Done

- [ ] All 6 stories completed with acceptance criteria met
- [ ] Scenario tree visualization renders correctly for trees up to 200 nodes
- [ ] Conversation fork tree displays in conversation view
- [ ] Breadcrumb navigation works on all scenario pages
- [ ] Zoom/pan controls smooth at 60fps
- [ ] Minimap reflects viewport accurately
- [ ] Tree export generates valid PNG files
- [ ] Mobile responsive (touch gestures work)
- [ ] Unit tests >80% coverage on tree logic
- [ ] Integration tests passing for tree API endpoints
- [ ] Visual regression tests passing (tree rendering matches designs)
- [ ] Performance tests passing (500ms for 50 nodes, 2s for 200 nodes)
- [ ] Accessibility tests passing (keyboard navigation, screen reader)
- [ ] Code review completed, no P0/P1 issues
- [ ] Deployed to Railway staging, smoke tested with sample trees

---

**Epic Owner**: Frontend Lead

**Start Date**: Week 3, Day 1 of MVP development

**Target Completion**: Week 3, Day 2 (1.5 working days)

**Estimated Total Effort**: **26 hours**

**Breakdown**:

- Story 5.1: 8 hours (scenario tree API + simplified conversation fork relationship API)
- Story 5.2: 14 hours (scenario tree UI with D3.js/Reingold-Tilford)
- Story 5.3: **6 hours** (conversation fork relationship UI - simplified for max depth 1)

**Priority**: HIGH - Visual navigation critical for understanding branching timelines

**Note**: Conversation fork visualization is **significantly simpler** than scenario tree due to max depth 1 constraint (ROOT → fork only). No complex tree algorithms or recursive queries needed for conversations.
