# Story 3.1: Book Browse Page

**Epic**: Epic 3 - Scenario Discovery & Forking  
**Story ID**: 3.1  
**Story Title**: Book Browse Page  
**Estimated Effort**: 8 hours  
**Priority**: High (MVP - Book-Centric Architecture Foundation)

---

## Story

As a **user exploring the platform**,  
I want to **browse available books in a visually appealing grid/list**,  
So that I can **discover books and explore scenarios within them**.

---

## Context

This is the entry point for the new **Book-Centric Architecture** (Version 1.1). Users now start by browsing books, then dive into scenarios within each book. This story implements the first page in the navigation hierarchy: Browse Books → Book Detail → Scenario Detail → Conversation.

**Navigation Flow:**

1. User lands on `/books` (Book Browse Page)
2. Clicks a book card → navigates to `/books/{id}` (Book Detail Page - Story 3.2)
3. Clicks a scenario → navigates to scenario detail
4. Starts conversation

**Key Requirements:**

- Display books in card grid (mobile-first, responsive)
- Filter by genre, sort by popularity/scenarios/conversations/newest
- Show key metrics: scenario count, conversation count
- No quality score display (removed in v1.1)

---

## Acceptance Criteria

### AC1: Book List Display

- [ ] Book cards display in responsive grid (1 col mobile, 2 cols tablet, 3-4 cols desktop)
- [ ] Each card shows:
  - Book cover image (placeholder if unavailable)
  - Book title
  - Author name
  - Genre tag
  - Scenario count (e.g., "24 scenarios")
  - Conversation count (e.g., "156 conversations")
- [ ] No quality score displayed anywhere
- [ ] Cards are clickable → navigate to Book Detail page

### AC2: Filtering & Sorting

- [ ] Genre filter dropdown (All, Fantasy, Sci-Fi, Romance, Mystery, etc.)
- [ ] Sort dropdown with options:
  - Most Scenarios (default)
  - Most Conversations
  - Newest Books
  - Alphabetical (A-Z)
- [ ] Filter/sort triggers instant re-fetch from API
- [ ] Active filter/sort persists in URL query params

### AC3: Pagination

- [ ] Display 20 books per page
- [ ] Pagination controls at bottom (Prev, 1, 2, 3..., Next)
- [ ] Current page highlighted
- [ ] Total count displayed (e.g., "Showing 1-20 of 156 books")

### AC4: Empty States

- [ ] When no books exist: "No books available yet. Check back soon!"
- [ ] When filter returns no results: "No books found for [genre]. Try another filter."

### AC5: Loading States

- [ ] Skeleton cards while loading (3-4 skeleton cards)
- [ ] Loading spinner on filter/sort change
- [ ] Smooth transition when data arrives

### AC6: Mobile Responsive

- [ ] Single column on mobile (< 768px)
- [ ] Touch-friendly cards (min height 120px)
- [ ] Genre filter becomes bottom sheet on mobile
- [ ] Sort becomes dropdown at top

### AC7: Performance

- [ ] Page loads within 2 seconds (cached API response)
- [ ] Images lazy-loaded (only load visible cards)
- [ ] Pagination prevents loading all books at once

---

## Technical Implementation

### API Endpoint

```
GET /api/v1/books
Query Params:
  - page: integer (default 0)
  - size: integer (default 20)
  - genre: string (optional, e.g., "Fantasy")
  - sort: string (optional: "scenarios" | "conversations" | "newest" | "alphabetical")

Response 200 OK:
{
  "content": [
    {
      "id": "uuid",
      "title": "Harry Potter and the Philosopher's Stone",
      "author": "J.K. Rowling",
      "genre": "Fantasy",
      "coverImageUrl": "https://...",
      "scenarioCount": 24,
      "conversationCount": 156
    },
    ...
  ],
  "pageable": {
    "pageNumber": 0,
    "pageSize": 20
  },
  "totalElements": 156,
  "totalPages": 8
}
```

### Vue Component Structure

```
BookBrowsePage.vue (Page)
├── BookFilterBar.vue (Filters + Sort)
├── BookGrid.vue (Grid Container)
│   └── BookCard.vue (Individual Card)
└── PaginationControls.vue (Pagination)
```

### Backend Service (Spring Boot)

```java
@RestController
@RequestMapping("/api/v1/books")
public class BookController {

    @Autowired
    private BookService bookService;

    @GetMapping
    public Page<BookResponse> getBooks(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "20") int size,
        @RequestParam(required = false) String genre,
        @RequestParam(required = false) String sort
    ) {
        return bookService.findAll(page, size, genre, sort);
    }
}
```

**Service Logic:**

- Query `novels` table with optional genre filter
- Join with `scenarios` to count scenarios per book
- Join with `conversations` to count conversations per book
- Apply sorting logic:
  - `scenarios`: ORDER BY scenarioCount DESC
  - `conversations`: ORDER BY conversationCount DESC
  - `newest`: ORDER BY created_at DESC
  - `alphabetical`: ORDER BY title ASC

### Database Query Optimization

```sql
-- Optimized query with aggregations
SELECT
    n.id, n.title, n.author, n.genre, n.cover_image_url,
    COUNT(DISTINCT s.id) as scenario_count,
    COALESCE(SUM(s.conversation_count), 0) as conversation_count
FROM novels n
LEFT JOIN scenarios s ON s.book_id = n.id
WHERE n.genre = ? OR ? IS NULL
GROUP BY n.id
ORDER BY
    CASE WHEN ? = 'scenarios' THEN scenario_count END DESC,
    CASE WHEN ? = 'conversations' THEN conversation_count END DESC,
    CASE WHEN ? = 'newest' THEN n.created_at END DESC,
    CASE WHEN ? = 'alphabetical' THEN n.title END ASC
LIMIT ? OFFSET ?;
```

**Required Indexes:**

- `idx_scenarios_book_id` ON scenarios(book_id)
- `idx_novels_genre` ON novels(genre)
- `idx_novels_created_at` ON novels(created_at)

---

## Dependencies

**Depends On:**

- Epic 0 (Spring Boot, Vue.js, PostgreSQL setup)
- `novels` table exists with sample data

**Blocks:**

- Story 3.2 (Book Detail Page)
- Story 3.3 (Scenario Browse - now within books)

---

## Testing Checklist

### Backend Tests

- [ ] **GET /api/v1/books - Basic List**

  - Returns 20 books with default pagination
  - Each book has required fields (id, title, author, genre, scenarioCount, conversationCount)
  - No quality_score in response

- [ ] **Genre Filtering**

  - Filter by "Fantasy" returns only Fantasy books
  - Filter by "Sci-Fi" returns only Sci-Fi books
  - Invalid genre returns empty list

- [ ] **Sorting**

  - sort=scenarios: Books ordered by scenario count DESC
  - sort=conversations: Books ordered by conversation count DESC
  - sort=newest: Books ordered by created_at DESC
  - sort=alphabetical: Books ordered by title ASC

- [ ] **Pagination**

  - page=0, size=20 returns first 20 books
  - page=1, size=20 returns next 20 books
  - totalElements matches total books in database
  - totalPages calculated correctly

- [ ] **Performance**
  - Query executes in < 50ms for 1000 books
  - Indexes are used (check EXPLAIN plan)

### Frontend Tests

- [ ] **Book Grid Rendering**

  - Books display in grid layout
  - Correct number of columns per breakpoint
  - Book cards show all required information

- [ ] **Filter Interaction**

  - Genre filter updates URL query param
  - Selecting genre triggers API call
  - Loading state shows while fetching
  - Results update correctly

- [ ] **Sort Interaction**

  - Sort dropdown updates URL query param
  - Selecting sort option triggers API call
  - Results reorder correctly

- [ ] **Pagination Interaction**

  - Clicking "Next" loads page 2
  - Clicking page number loads that page
  - Current page is highlighted
  - "Prev" disabled on page 1

- [ ] **Empty States**

  - No books: Shows empty state message
  - No results from filter: Shows "no results" message

- [ ] **Mobile Responsive**
  - Single column on mobile
  - Filter becomes bottom sheet
  - Touch targets are adequate (min 44px)

### Integration Tests

- [ ] **End-to-End Flow**
  - User lands on /books
  - Filters by "Fantasy"
  - Sorts by "Most Scenarios"
  - Clicks a book card
  - Navigates to Book Detail page (Story 3.2)

---

## Definition of Done

- [ ] Backend API returns paginated book list with aggregated counts
- [ ] Genre filtering works correctly
- [ ] Sorting by scenarios/conversations/newest/alphabetical works
- [ ] Frontend displays books in responsive grid
- [ ] Filter and sort UI updates results instantly
- [ ] Pagination controls work correctly
- [ ] No quality_score displayed anywhere
- [ ] Mobile responsive (tested on 375px width)
- [ ] All tests pass (backend + frontend + integration)
- [ ] Code reviewed and merged
- [ ] Deployed to staging environment

---

## Notes

**Design Reference:**

- Similar to Goodreads book browse page
- Card-based design with clear hierarchy
- Emphasis on book covers (visual discovery)

**Performance:**

- Lazy load book cover images (IntersectionObserver)
- Cache API response for 5 minutes (reduce server load)
- Use skeleton cards for perceived performance

**Future Enhancements (Deferred):**

- Search by book title/author (Story 3.6)
- "Trending" badge for popular books
- "New" badge for recently added books
- Infinite scroll option (currently pagination)
