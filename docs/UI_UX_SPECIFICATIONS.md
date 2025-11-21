# UI/UX Specifications - Gaji Interactive Fiction Platform

**Version**: 1.0  
**Last Updated**: 2025-11-13  
**Design System**: PrimeVue 3.x + PandaCSS  
**Target Frameworks**: Vue.js 3.x, Vite 5.x

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [User Personas](#user-personas)
3. [User Journey Maps](#user-journey-maps)
4. [Design System](#design-system)
5. [Component Library](#component-library)
6. [Screen Specifications](#screen-specifications)
7. [Responsive Design](#responsive-design)
8. [Accessibility](#accessibility)
9. [Interaction Patterns](#interaction-patterns)
10. [Visual Design](#visual-design)

---

## Design Philosophy

### Core Principles

1. **Book-Centric Discovery**: Users explore books first, then scenarios within each book
2. **Mobile-First**: Design for mobile experience, enhance for desktop
3. **Progressive Disclosure**: Show essential information first, reveal complexity on demand
4. **Feedback-Rich**: Provide immediate visual feedback for all user actions
5. **Content-Focused**: Minimize chrome, maximize content visibility

### Design Goals

- **Intuitive Scenario Creation**: Users should create "What If" scenarios in < 60 seconds with validation (min 10 chars per field)
- **Engaging Conversations**: Chat interface feels natural and responsive with scenario context visible
- **Discoverable Books**: Book-centric navigation makes finding stories obvious
- **Social First**: Following, liking, and sharing feel native

---

## User Personas

### Persona 1: The Creative Explorer (Primary)

**Name**: Sarah, 28, Marketing Manager  
**Goals**:

- Explore books she loves through alternate scenarios
- Create unique scenarios within her favorite books and share with friends
- Discover creative interpretations from community

**Pain Points**:

- Overwhelmed by too many scenario options
- Uncertain how to start creating scenarios with proper content
- Wants inspiration from others' work

**Design Needs**:

- Guided scenario creation with validation (min 10 chars)
- Book-centric browsing with featured scenarios
- Simple fork/like interactions
- Social feed of followed users

---

### Persona 2: The Deep Diver (Secondary)

**Name**: Alex, 34, Software Developer  
**Goals**:

- Create complex meta-scenarios (scenarios of scenarios)
- Engage in long philosophical conversations with AI characters
- Explore scenario tree structures

**Pain Points**:

- Needs advanced filtering and search
- Wants to track conversation branches
- Requires memo system for notes

**Design Needs**:

- Advanced search/filter UI
- Conversation tree visualization
- Book-based organization
- Keyboard shortcuts

---

### Persona 3: The Casual Reader (Tertiary)

**Name**: Michael, 22, University Student  
**Goals**:

- Quick entertainment during breaks
- Read interesting scenarios created by others
- Occasionally try conversations

**Pain Points**:

- Doesn't want to create account immediately
- Short attention span
- Prefers browsing to creating

**Design Needs**:

- Browse books and scenarios without login
- One-click book preview
- Guest conversation mode (future)
- Minimal onboarding friction

---

## User Journey Maps

### Journey 1: Create First Scenario

**User Goal**: Create "Hermione in Slytherin" scenario

| Step | User Action             | Screen                 | UI Elements                      | Emotions     |
| ---- | ----------------------- | ---------------------- | -------------------------------- | ------------ |
| 1    | Land on homepage        | Homepage               | Hero section, featured scenarios | Curious      |
| 2    | Click "Create Scenario" | -                      | CTA button                       | Interested   |
| 3    | Select novel            | Scenario Wizard Step 1 | Novel search/autocomplete        | Engaged      |
| 4    | Choose scenario type    | Scenario Wizard Step 2 | Radio cards with icons           | Confident    |
| 5    | Fill parameters         | Scenario Wizard Step 3 | Form with guided inputs          | Creative     |
| 6    | Preview scenario        | Scenario Wizard Step 4 | Preview card                     | Excited      |
| 7    | Publish                 | -                      | Submit button                    | Accomplished |
| 8    | View created scenario   | Scenario Detail        | Full scenario page               | Proud        |

**Success Metrics**:

- Completion rate > 70%
- Time to create < 2 minutes
- Abandonment rate < 20% (Step 3)

---

### Journey 2: Explore & Fork Conversation

**User Goal**: Find interesting conversation, create fork with own twist

| Step | User Action           | Screen                     | UI Elements                           | Emotions  |
| ---- | --------------------- | -------------------------- | ------------------------------------- | --------- |
| 1    | Browse scenarios      | Browse Page                | Card grid, filters                    | Browsing  |
| 2    | Click scenario        | Scenario Detail            | Hero, conversations list              | Intrigued |
| 3    | Read top conversation | Conversation Detail        | Message thread                        | Engaged   |
| 4    | Click "Fork"          | -                          | Fork button (header)                  | Inspired  |
| 5    | Enter fork title      | Fork Modal                 | Title input, message preview          | Creative  |
| 6    | Confirm fork          | -                          | Submit button                         | Confident |
| 7    | Redirect to fork      | Conversation Detail (Fork) | New conversation with copied messages | Excited   |
| 8    | Send first message    | -                          | Message input, AI response            | Satisfied |

**Success Metrics**:

- Fork rate per conversation > 5%
- Time to fork < 30 seconds
- Follow-up message rate after fork > 80%

---

### Journey 3: Discovery Through Social

**User Goal**: Find scenarios from favorite creators

| Step | User Action             | Screen                | UI Elements              | Emotions  |
| ---- | ----------------------- | --------------------- | ------------------------ | --------- |
| 1    | Click user profile      | User Profile          | Avatar, bio, stats       | Curious   |
| 2    | View scenarios tab      | Profile Scenarios Tab | Scenario cards           | Browsing  |
| 3    | Follow user             | -                     | Follow button            | Connected |
| 4    | Return to feed          | Homepage/Feed         | Followed users' activity | Satisfied |
| 5    | Like scenario from feed | -                     | Like button on card      | Engaged   |
| 6    | Browse liked scenarios  | Profile > Liked Tab   | Saved scenarios          | Organized |

**Success Metrics**:

- Follow conversion > 15% from profile visits
- Like rate > 25% from feed
- Return rate for feed > 60% daily active users

---

## Design System

### Color Palette (PandaCSS Tokens)

```typescript
// Primary Brand Colors
colors: {
  brand: {
    50: '#e8f5f0',   // Lightest green
    100: '#c1e6d9',
    200: '#9ad7c2',
    300: '#73c8ab',
    400: '#4cb994',
    500: '#1F7D51',  // Primary brand color (forest green)
    600: '#1a6a45',
    700: '#155739',
    800: '#10442d',
    900: '#0b3121',  // Darkest green
  },

  // Secondary/Accent Colors
  accent: {
    50: '#fef9e7',   // Lightest gold
    100: '#fcf0c2',
    200: '#fae79d',
    300: '#f8de78',
    400: '#f6d553',
    500: '#DEAD5C',  // Secondary brand color (gold)
    600: '#c8924d',
    700: '#a3783e',
    800: '#7e5d2f',
    900: '#594220',  // Darkest gold
  },

  // Neutral Grays
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },

  // Semantic Colors
  success: {
    500: '#10b981',  // Green
    600: '#059669',
  },
  error: {
    500: '#ef4444',  // Red
    600: '#dc2626',
  },
  warning: {
    500: '#f59e0b',  // Amber
    600: '#d97706',
  },
  info: {
    500: '#3b82f6',  // Blue
    600: '#2563eb',
  },
}
```

### Typography

```typescript
fonts: {
  heading: '"Inter", "Helvetica Neue", Arial, sans-serif',
  body: '"Inter", "Helvetica Neue", Arial, sans-serif',
  mono: '"Fira Code", "Monaco", "Courier New", monospace',
}

fontSizes: {
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  '3xl': '1.875rem',// 30px
  '4xl': '2.25rem', // 36px
  '5xl': '3rem',    // 48px
}

fontWeights: {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
}
```

### Spacing Scale

```typescript
spacing: {
  px: '1px',
  0: '0',
  0.5: '0.125rem',  // 2px
  1: '0.25rem',     // 4px
  2: '0.5rem',      // 8px
  3: '0.75rem',     // 12px
  4: '1rem',        // 16px
  5: '1.25rem',     // 20px
  6: '1.5rem',      // 24px
  8: '2rem',        // 32px
  10: '2.5rem',     // 40px
  12: '3rem',       // 48px
  16: '4rem',       // 64px
  20: '5rem',       // 80px
  24: '6rem',       // 96px
}
```

### Breakpoints (Mobile-First)

```typescript
breakpoints: {
  sm: '640px',   // Small tablets
  md: '768px',   // Tablets
  lg: '1024px',  // Laptops
  xl: '1280px',  // Desktops
  '2xl': '1536px', // Large desktops
}
```

### Border Radius

```typescript
radii: {
  none: '0',
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  full: '9999px',   // Circular
}
```

### Shadows

```typescript
shadows: {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
}
```

---

## Component Library

### PrimeVue Components Used

#### Layout Components

- **Card** (`p-card`): Scenario cards, conversation cards
- **Panel** (`p-panel`): Collapsible sections
- **Divider** (`p-divider`): Content separation
- **ScrollPanel** (`p-scroll-panel`): Message list, tree view

#### Navigation

- **Menubar** (`p-menubar`): Main navigation
- **TabView** (`p-tab-view`): Profile tabs, scenario tabs
- **Breadcrumb** (`p-breadcrumb`): Nested navigation

#### Form Components

- **InputText** (`p-input-text`): Text inputs
- **Textarea** (`p-textarea`): Long text (descriptions, messages)
- **Dropdown** (`p-dropdown`): Select dropdowns
- **AutoComplete** (`p-auto-complete`): Novel search
- **RadioButton** (`p-radio-button`): Scenario type selection
- **Checkbox** (`p-checkbox`): Filter options
- **Button** (`p-button`): All CTAs

#### Data Display

- **DataView** (`p-data-view`): Scenario grid/list view
- **Paginator** (`p-paginator`): Pagination
- **Tag** (`p-tag`): Tags, badges
- **Avatar** (`p-avatar`): User avatars
- **Tree** (`p-tree`): Scenario tree, conversation tree

#### Overlay

- **Dialog** (`p-dialog`): Modals (fork, delete confirm)
- **OverlayPanel** (`p-overlay-panel`): Dropdowns, tooltips
- **Toast** (`p-toast`): Notifications
- **ConfirmDialog** (`p-confirm-dialog`): Confirmations

#### Misc

- **Skeleton** (`p-skeleton`): Loading states
- **ProgressSpinner** (`p-progress-spinner`): Async operations
- **FileUpload** (`p-file-upload`): Avatar upload

---

## Screen Specifications

### 1. Homepage / Landing

**Purpose**: Welcome users, showcase platform, drive sign-ups

**Layout** (Mobile-First):

```
┌─────────────────────────────────┐
│ [Logo]         [Login] [SignUp] │ ← Header (sticky)
├─────────────────────────────────┤
│                                 │
│  📖 Explore Infinite            │ ← Hero Section
│     Story Possibilities         │
│                                 │
│  [Create Scenario] [Browse]     │ ← CTAs
│                                 │
├─────────────────────────────────┤
│ ⭐ Featured Scenarios            │ ← Featured Grid
│                                 │
│ ┌───────┐ ┌───────┐ ┌───────┐  │
│ │ Card  │ │ Card  │ │ Card  │  │ (Horizontal scroll on mobile)
│ └───────┘ └───────┘ └───────┘  │
│                                 │
├─────────────────────────────────┤
│ 🔥 Trending Conversations        │ ← Trending List
│                                 │
│ 1. Hermione in Slytherin...     │
│ 2. Gatsby's California Dream... │
│ 3. Pride & Prejudice Reversed...│
│                                 │
└─────────────────────────────────┘
```

**Desktop Enhancements**:

- Hero section full-width with background illustration
- Featured books with scenarios: 3-column grid (instead of scroll)
- Trending conversations: 2-column layout with preview

**Components**:

- Header: Custom navigation bar
- Hero: Custom hero component with gradient background
- Featured: `DataView` with `grid` layout (book-centric)
- Trending: `DataView` with `list` layout

---

### 2. Book Browse Page

**Purpose**: Discover books and their scenarios through filtering and search

**Layout** (Mobile):

```
┌─────────────────────────────────┐
│ [Search: "harry potter"]       │ ← Search Bar
│ [Filters ▼]                    │ ← Filter Toggle
├─────────────────────────────────┤
│ Showing 23 books                │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 📘 Harry Potter Series      │ │ ← Book Card
│ │ by J.K. Rowling             │ │
│ │ 45 scenarios | 230 convos   │ │
│ │                             │ │
│ │ [Explore Scenarios →]       │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ � Pride and Prejudice      │ │
│ │ by Jane Austen              │ │
│ │ 18 scenarios | 92 convos    │ │
│ │                             │ │
│ │ [Explore Scenarios →]       │ │
│ └─────────────────────────────┘ │
│                                 │
│ [Load More]                     │
└─────────────────────────────────┘
```

**Filter Panel** (Expandable):

```
┌─────────────────────────────────┐
│ 📂 Filters                       │
│                                 │
│ 📚 Genre:                       │
│ ☐ Fantasy (23)                  │
│ ☐ Romance (15)                  │
│ ☐ Classic (32)                  │
│ ☐ Mystery (8)                   │
│                                 │
│ 🔥 Popularity:                  │
│ ⚫ All                          │
│ ⚪ Most Scenarios               │
│ ⚪ Most Active                  │
│                                 │
│ [Apply] [Reset]                 │
└─────────────────────────────────┘
```

**Desktop Layout**:

```
┌───────────┬─────────────────────────────────────────────┐
│           │ [Search Bar]                  [View: Grid]  │
│           ├─────────────────────────────────────────────┤
│  Filters  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │
│  (Sidebar)│ │Book │ │Book │ │Book │ │Book │  3-col grid│
│           │ └─────┘ └─────┘ └─────┘ └─────┘            │
│  📚 Genre │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐            │
│  🔥 Pop   │ │Book │ │Book │ │Book │ │Book │            │
│           │ └─────┘ └─────┘ └─────┘ └─────┘            │
│           │                                             │
│           │ [← Previous] [1] [2] [3] [Next →]          │
└───────────┴─────────────────────────────────────────────┘
```

**Components**:

- Search: `AutoComplete` with debounce
- Filters: Custom filter panel with `Checkbox`, `RadioButton`
- Results: `DataView` with `grid`/`list` toggle (book cards)
- Pagination: `Paginator`

---

### 3. Book Detail Page (with Scenarios)

**Purpose**: Display book info and its scenarios, enable scenario creation

**Layout** (Mobile):

```
┌─────────────────────────────────┐
│ ← Back to Books                 │ ← Breadcrumb
├─────────────────────────────────┤
│ 📘 Harry Potter Series          │ ← Book Cover/Title
│ by J.K. Rowling                 │ ← Author
│                                 │
│ 45 scenarios | 230 conversations│ ← Stats Row
│                                 │
│ [+ Create Scenario]             │ ← Primary Action
│                                 │
├─────────────────────────────────┤
│ 📝 Scenarios (45)               │ ← Scenarios Tab
│                                 │
│ [Filter: All ▼]                 │ ← Scenario Type Filter
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Hermione in Slytherin       │ │ ← Scenario Card
│ │ By @hermione_fan · 2d ago   │ │
│ │ 💬 12 convos | 🍴 5 forks    │ │
│ │ [View →]                    │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ Draco Redeemed              │ │
│ │ By @draco_stan · 5d ago     │ │
│ │ 💬 8 convos | 🍴 3 forks     │ │
│ │ [View →]                    │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Desktop Enhancements**:

- Book cover image on left
- 2-column scenario grid
- Sticky "Create Scenario" button

**Components**:

- Header: Book info with stats
- Create Button: Primary CTA button (opens modal)
- Scenarios: `DataView` with `grid` layout
- Filter: `Dropdown` for scenario type

**Note**: Quality scores removed in v1.1 - scenarios ranked by engagement metrics (forks, conversations) only

---

### 4. Scenario Detail Page

**Purpose**: Display scenario details, list conversations, enable forking

**Layout** (Mobile):

```
┌─────────────────────────────────┐
│ ← Back to Book                  │ ← Breadcrumb
├─────────────────────────────────┤
│ 📘 Book: Harry Potter           │ ← Book Context
│                                 │
│ Hermione in Slytherin           │ ← Title (h1)
│ By @hermione_fan · 2 days ago   │ ← Meta
│                                 │
│ 💬 12 conversations | 🍴 5 forks│ ← Stats (no quality)
│                                 │
│ [Start Chat] [🍴 Fork] [Share]  │ ← Action Buttons
│                                 │
├─────────────────────────────────┤
│ 📝 Scenario Details              │ ← Collapsible Panel
│                                 │
│ 👤 Character Changes:           │
│ Hermione sorted into Slytherin  │
│ instead of Gryffindor           │
│                                 │
│ 🎬 Event Alterations:           │
│ Troll incident: saved by Draco  │
│ and Pansy instead               │
│                                 │
│ 🌍 Setting Modifications:       │
│ (None)                          │
├─────────────────────────────────┤
│ 💬 Conversations (12)            │ ← Conversations List
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 📖 Hermione's First Day     │ │ ← Conversation Card
│ │ By @user1 · 1 day ago       │ │
│ │ 8 messages | ❤️ 23           │ │
│ │ [Read →]                    │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 📖 Befriending Draco        │ │
│ │ ...                         │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**Scenario Fork Button**: Opens creation modal with this book pre-selected

**Desktop Enhancements**:

- 2-column layout: Details (left) + Conversations (right)
- Sticky scenario summary on scroll

**Components**:

- Header: Book context + scenario info
- Actions: `Button` group (Start Chat, Fork, Share)
- Details: `Panel` (collapsible) showing 3 scenario types
- Conversations: `DataView` with `list` layout

---

### 5. Conversation Detail Page

**Purpose**: Display conversation messages with scenario context, enable messaging and forking

**Layout** (Mobile):

```
┌─────────────────────────────────┐
│ ← Back | [Fork Chat] [Like]    │ ← Header Actions
├─────────────────────────────────┤
│ 📘 Book: Harry Potter           │ ← Book Context
│ Scenario: Hermione in Slytherin │ ← Scenario Context
│                                 │
│ [View Scenario Details ▼]       │ ← Expandable Scenario
│                                 │
│ Hermione's First Day            │ ← Conversation Title
│ By @hermione_fan                │ ← Creator
│                                 │
├─────────────────────────────────┤
│ 💬 Messages                      │ ← Message Thread
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 👤 You                      │ │ ← User Message
│ │ How would Hermione react to │ │
│ │ being sorted into Slytherin?│ │
│ │ 2 hours ago                 │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 🤖 Hermione Granger         │ │ ← AI Message
│ │ I was shocked at first. The │ │
│ │ Sorting Hat saw my ambition │ │
│ │ and cunning, traits I never │ │
│ │ fully acknowledged...       │ │
│ │ 2 hours ago                 │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 👤 You                      │ │
│ │ How did Draco react?        │ │
│ │ 1 hour ago                  │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 🤖 Hermione Granger         │ │
│ │ ▮ (typing...)              │ │ ← Typing Indicator
│ └─────────────────────────────┘ │
│                                 │
├─────────────────────────────────┤
│ [Type your message...]          │ ← Message Input
│                            [→]  │ (Sticky bottom)
└─────────────────────────────────┘
```

**Expandable Scenario Details**:

```
┌─────────────────────────────────┐
│ [View Scenario Details ▼]       │ ← Click to expand
├─────────────────────────────────┤
│ 👤 Character Changes:           │ ← Scenario context
│ Hermione sorted into Slytherin  │
│                                 │
│ 🎬 Event Alterations:           │
│ Troll incident: saved by Draco  │
│                                 │
│ 🌍 Setting Modifications:       │
│ (None)                          │
└─────────────────────────────────┘
```

**Message States**:

- **User Message**: Right-aligned, blue background
- **AI Message**: Left-aligned, gray background
- **Typing Indicator**: Animated dots "..."
- **Streaming Message**: Text appears word-by-word

**Desktop Layout**:

```
┌───────────┬─────────────────────────────────┬───────────┐
│ Scenario  │ 💬 Messages                      │ 🌳 Tree   │
│ Context   │                                 │ (Sidebar) │
│           │ ┌─────────────────────────────┐ │           │
│ 📘 Book:  │ │ 👤 You                      │ │ [Tree]    │
│ Harry     │ │ Message text...             │ │ View      │
│ Potter    │ └─────────────────────────────┘ │           │
│           │                                 │ [Expand]  │
│ Scenario: │ ┌─────────────────────────────┐ │           │
│ Hermione  │ │ 🤖 Hermione                 │ │           │
│ in        │ │ Response text...            │ │           │
│ Slytherin │ └─────────────────────────────┘ │           │
│           │                                 │           │
│ [Details] │ [Type message...]          [→] │           │
└───────────┴─────────────────────────────────┴───────────┘
```

**Components**:

- Scenario Context: Expandable panel showing book + scenario details
- Message Thread: `ScrollPanel` with custom message components
- Message Input: `Textarea` with auto-resize
- Streaming: Custom component with SSE integration
- Tree View: Conversation tree visualization (sidebar on desktop)

---

### 5. Scenario Creation Modal

**Purpose**: Create scenarios with validation (min 10 chars per field, at least 1 filled)

**Trigger**: Click "Create Scenario" button from Book Detail page

**Modal Layout** (Mobile):

```
┌─────────────────────────────────┐
│ 📝 Create Scenario       [X]    │ ← Modal Header
├─────────────────────────────────┤
│                                 │
│ � Book: Harry Potter           │ ← Selected Book (read-only)
│                                 │
│ Scenario Title: *               │
│ ┌─────────────────────────────┐ │
│ │ Hermione in Slytherin       │ │ ← Input
│ └─────────────────────────────┘ │
│                                 │
│ ━━━ Scenario Details ━━━        │
│ (At least one required, min 10  │
│  characters each)               │
│                                 │
│ 👤 Character Changes:           │
│ ┌─────────────────────────────┐ │
│ │ Hermione sorted into        │ │ ← Textarea
│ │ Slytherin instead of        │ │   (min 10 chars)
│ │ Gryffindor                  │ │   15/10 chars
│ └─────────────────────────────┘ │
│                                 │
│ 🎬 Event Alterations:           │
│ ┌─────────────────────────────┐ │
│ │ Troll incident: saved by    │ │ ← Textarea
│ │ Draco instead               │ │   (min 10 chars)
│ └─────────────────────────────┘ │   32/10 chars
│                                 │
│ 🌍 Setting Modifications:       │
│ ┌─────────────────────────────┐ │
│ │                             │ │ ← Textarea (empty OK)
│ └─────────────────────────────┘ │   0/10 chars
│                                 │
│ ⚠️ Please fill at least one     │ ← Validation message
│    field with 10+ characters    │   (shows on error)
│                                 │
│ [Cancel]            [Create]    │
└─────────────────────────────────┘
```

**Validation Rules**:

- Title: Required, max 100 chars
- At least ONE of (Character/Event/Setting) must be filled
- Each filled field must have ≥ 10 characters
- Real-time character counter
- Submit button disabled until valid

**Error States**:

```
❌ All fields empty or < 10 chars:
   "Please provide at least one scenario type with 10+ characters"

❌ Title empty:
   "Scenario title is required"
```

│ Timeline Point: _ │
│ ┌─────────────────────────────┐ │
│ │ Chapter 5, Summer 1922 │ │
│ └─────────────────────────────┘ │
│ │
│ Alteration Type: _ │
│ [Prevent ▼] (Dropdown) │
│ │
│ Original Outcome: │
│ ┌─────────────────────────────┐ │
│ │ They reunite and rekindle │ │ ← Textarea
│ │ romance │ │
│ └─────────────────────────────┘ │
│ │
│ New Outcome: \* │
│ ┌─────────────────────────────┐ │
│ │ Gatsby moves to California, │ │
│ │ never looks back │ │
│ └─────────────────────────────┘ │
│ │
│ [← Back] [Next →]│
└─────────────────────────────────┘

```

**Step 4: Preview & Publish**:

```

┌─────────────────────────────────┐
│ Create New Scenario (4/4) │
│ ━━━━━━━━━━━━━━━━━━ │
│ │
│ 👀 Preview Your Scenario │
│ │
│ ┌─────────────────────────────┐ │
│ │ 📘 The Great Gatsby │ │ ← Scenario Preview Card
│ │ │ │
│ │ Gatsby Never Met Daisy │ │ (Title auto-generated)
│ │ │ │
│ │ Type: Event Alteration │ │
│ │ Event: Gatsby and Daisy... │ │
│ │ New Outcome: Gatsby moves...│ │
│ └─────────────────────────────┘ │
│ │
│ Privacy: │
│ ⚫ Public ⚪ Private │ ← Radio Buttons
│ │
│ [← Back] [🚀 Publish] │
└─────────────────────────────────┘

```

**Components**:

- Modal Container: `Dialog` component
- Form Fields: `InputText`, `Textarea` with character counters
- Validation: Real-time validation with error messages
- Submit: `Button` (disabled until valid)

---

### 6. Fork Chat Modal

**Purpose**: Fork existing conversation with original scenario context visible

**Trigger**: Click "Fork Chat" button from Conversation page

**Modal Layout** (Mobile):

```

┌─────────────────────────────────┐
│ 🍴 Fork Conversation [X] │ ← Modal Header
├─────────────────────────────────┤
│ │
│ 📘 Original Book: │
│ Harry Potter │
│ │
│ 📝 Original Scenario: │ ← Read-only context
│ ┌─────────────────────────────┐ │
│ │ 👤 Character Changes: │ │
│ │ Hermione sorted into │ │
│ │ Slytherin instead of │ │
│ │ Gryffindor │ │
│ │ │ │
│ │ 🎬 Event Alterations: │ │
│ │ Troll incident: saved by │ │
│ │ Draco instead │ │
│ │ │ │
│ │ 🌍 Setting Modifications: │ │
│ │ (None) │ │
│ └─────────────────────────────┘ │
│ │
│ ━━━ Your Fork ━━━ │
│ │
│ Fork Title: \* │
│ ┌─────────────────────────────┐ │
│ │ Hermione in Slytherin + │ │ ← Input
│ │ Head Girl │ │
│ └─────────────────────────────┘ │
│ │
│ ✏️ Edit Scenario (Optional): │
│ │
│ 👤 Character Changes: │
│ ┌─────────────────────────────┐ │
│ │ Hermione sorted into │ │ ← Pre-filled, editable
│ │ Slytherin AND becomes │ │ (min 10 chars)
│ │ Head Girl in Year 7 │ │
│ └─────────────────────────────┘ │ 52/10 chars
│ │
│ 🎬 Event Alterations: │
│ ┌─────────────────────────────┐ │
│ │ Troll incident: saved by │ │ ← Pre-filled, editable
│ │ Draco instead │ │
│ └─────────────────────────────┘ │ 32/10 chars
│ │
│ 🌍 Setting Modifications: │
│ ┌─────────────────────────────┐ │
│ │ │ │ ← Empty, can add
│ └─────────────────────────────┘ │ 0/10 chars
│ │
│ ℹ️ Will copy last 6 messages │ ← Info message
│ │
│ [Cancel] [Fork & Start] │
└─────────────────────────────────┘

```

**Features**:
- Shows original scenario in read-only section
- Pre-fills edit fields with original content
- Allows modifications (or keep as-is)
- Same validation: at least 1 field with 10+ chars
- Character counters for each field

**Components**:

- Modal: `Dialog` component
- Original Context: Read-only display panel
- Edit Fields: `Textarea` components with pre-filled values
- Validation: Same as creation modal
- Submit: `Button` with fork icon

---

### 7. User Profile Page

**Purpose**: Display user activity, scenarios, conversations, followers

**Layout** (Mobile):

```

┌─────────────────────────────────┐
│ ← Back │
├─────────────────────────────────┤
│ ┌───────────┐ │ ← Avatar
│ │ Avatar │ │
│ └───────────┘ │
│ │
│ @hermione_fan │ ← Username (h1)
│ │
│ Slytherin Hermione enthusiast. │ ← Bio
│ Exploring alternate timelines. │
│ │
│ 👥 234 followers · 89 following │ ← Stats
│ 📖 12 scenarios · 💬 45 convos │
│ │
│ [Follow] [Share] │ ← Actions (if not self)
│ [Edit Profile] │ (if self)
│ │
├─────────────────────────────────┤
│ ┌─────┬─────┬─────┐ │ ← Tabs (Memo removed)
│ │Scen │Conv │Liked│ │
│ └─────┴─────┴─────┘ │
│ │
│ 📖 Scenarios (12) │ ← Active Tab Content
│ │
│ ┌─────────────────────────────┐ │
│ │ 📘 Book: Harry Potter │ │ ← Scenario Card
│ │ Hermione in Slytherin │ │
│ │ 💬 12 | 🍴 5 │ │
│ │ 2 days ago │ │
│ └─────────────────────────────┘ │
│ │
│ ┌─────────────────────────────┐ │
│ │ 📘 Book: Harry Potter │ │
│ │ Draco Redeemed │ │
│ │ 💬 8 | 🍴 3 │ │
│ │ 1 week ago │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘

```

**Tabs**:

1. **Scenarios**: User's created scenarios
2. **Conversations**: User's conversations
3. **Liked**: Liked conversations (private if not self)

**Note**: Memo tab removed per requirements

**Edit Profile Modal** (if self):

```

┌─────────────────────────────────┐
│ ✏️ Edit Profile [X] │
├─────────────────────────────────┤
│ │
│ Avatar: │
│ ┌───────────┐ [Upload New] │
│ │ Current │ │
│ │ Avatar │ │
│ └───────────┘ │
│ │
│ Username: @hermione_fan │ (Read-only)
│ │
│ Bio: │
│ ┌─────────────────────────────┐ │
│ │ Slytherin Hermione │ │ ← Editable Textarea
│ │ enthusiast. Exploring │ │ (500 char max)
│ │ alternate timelines. │ │
│ └─────────────────────────────┘ │
│ 45 / 500 characters │
│ │
│ [Cancel] [Save] │
└─────────────────────────────────┘

```

**Desktop Layout**:

```

┌───────────────────────────────────────────────────┐
│ ← Back │
├─────────────────┬─────────────────────────────────┤
│ │ │
│ ┌───────────┐ │ @hermione_fan │
│ │ Avatar │ │ │
│ └───────────┘ │ Slytherin Hermione enthusiast. │
│ │ Exploring alternate timelines. │
│ [Edit Profile] │ │
│ [Share] │ 👥 234 · 89 | 📖 12 · 💬 45 │
│ │ │
│ │ ┌──┬──┬──┬──┐ │
│ │ │Sc│Co│Li│Me│ │
│ │ └──┴──┴──┴──┘ │
│ │ │
│ │ ┌───┐ ┌───┐ ┌───┐ │
│ │ │ S │ │ S │ │ S │ 2-col grid │
│ │ └───┘ └───┘ └───┘ │
│ │ ┌───┐ ┌───┐ ┌───┐ │
│ │ │ S │ │ S │ │ S │ │
│ │ └───┘ └───┘ └───┘ │
└─────────────────┴─────────────────────────────────┘

```

**Components**:

- Avatar: `Avatar` with upload button
- Stats: Custom stat counters
- Tabs: `TabView`
- Content: `DataView` with `grid` layout
- Edit Modal: `Dialog` with `FileUpload`

---

## Responsive Design

### Mobile-First Breakpoints

**Base (< 640px): Mobile**

- Single column layouts
- Bottom navigation
- Hamburger menu
- Cards stack vertically
- Modal fills screen

**SM (640px - 767px): Large Mobile**

- 2-column grids for cards
- Expanded filter panels
- Larger touch targets

**MD (768px - 1023px): Tablets**

- 3-column grids
- Side navigation appears
- Multi-column layouts
- Split views for detail pages

**LG (1024px+): Desktop**

- 4-column grids
- Persistent sidebars
- Hover states
- Keyboard shortcuts

### Responsive Patterns

**Navigation**:

- Mobile: Bottom tab bar + hamburger menu
- Desktop: Top menubar + sidebar

**Cards**:

- Mobile: 1 column, full width
- Tablet: 2 columns
- Desktop: 3-4 columns

**Forms**:

- Mobile: Stacked labels above inputs
- Desktop: Inline labels (left of inputs)

**Modals**:

- Mobile: Full-screen takeover
- Desktop: Centered overlay (max 600px width)

---

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast**:

- Text: Minimum 4.5:1 ratio
- Large text (18px+): Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 ratio

**Keyboard Navigation**:

- All interactive elements reachable via Tab
- Logical tab order (top to bottom, left to right)
- Focus indicators visible (2px outline)
- Escape closes modals
- Enter/Space activates buttons

**Screen Reader Support**:

- Semantic HTML (`<nav>`, `<main>`, `<article>`)
- ARIA labels for icon-only buttons
- ARIA live regions for dynamic content (streaming messages)
- Form labels associated with inputs

**Focus Management**:

- Focus trapped in modals
- Focus returned after modal close
- Skip to main content link
- Focus outlines: 2px solid brand-500

**Touch Targets**:

- Minimum 44x44px for all interactive elements
- Increased spacing between buttons

---

## Interaction Patterns

### Loading States

**Skeleton Screens**:

```

┌─────────────────────────────────┐
│ ████████ │ ← Title
│ ████ │ ← Meta
│ │
│ ████████████████ │ ← Description
│ ████████ │
│ │
│ [████] [████] [████] │ ← Buttons
└─────────────────────────────────┘

````

**Spinners**:

- Page load: Full-screen spinner with logo
- Button actions: Inline spinner in button
- Infinite scroll: Footer spinner

**Streaming Messages**:

- Typing indicator (3 animated dots)
- Text appears word-by-word
- Scroll follows new content

### Animations

**Transitions** (using PandaCSS):

```typescript
transition: {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
}
````

**Micro-Interactions**:

- Button hover: Scale 1.02, shadow increase
- Card hover: Lift (shadow increase)
- Like button: Heart scale + color change
- Fork button: Icon rotation
- Input focus: Border glow

**Page Transitions**:

- Fade in: 200ms
- Slide in (modals): 300ms from bottom (mobile), center (desktop)

### Error Handling

**Inline Validation**:

```
Email: *
┌─────────────────────────────────┐
│ not-an-email                    │ ← Input (red border)
└─────────────────────────────────┘
❌ Please enter a valid email address ← Error message (red)
```

**Toast Notifications**:

- Success: Green toast, top-right, 3s auto-dismiss
- Error: Red toast, top-right, 5s auto-dismiss, manual close
- Info: Blue toast, top-right, 3s auto-dismiss

**Empty States**:

```
┌─────────────────────────────────┐
│                                 │
│         🔍                      │ ← Illustration
│                                 │
│   No scenarios found            │ ← Heading
│   Try adjusting your filters    │ ← Suggestion
│                                 │
│   [Create New Scenario]         │ ← CTA
│                                 │
└─────────────────────────────────┘
```

---

## Visual Design

### Iconography

**Icon Library**: Heroicons (Outline for UI, Solid for filled states)

**Common Icons**:

- 🔍 Search
- ➕ Create/Add
- 🍴 Fork
- ❤️ Like (outline) / ❤️ (solid when liked)
- 💬 Conversation
- 📖 Scenario
- 👤 User
- ⚙️ Settings
- 🔔 Notifications
- 📝 Memo

### Illustrations

**Placeholder Illustrations** (using unDraw or custom):

- Empty states (no scenarios, no conversations)
- Hero section background
- Error pages (404, 500)

### Card Designs

**Scenario Card** (Detailed - v1.1):

```
┌─────────────────────────────────┐
│ 📘 Harry Potter                 │ ← Book badge (top-left)
│                                 │
│ Hermione Sorted into Slytherin  │ ← Title (bold, 18px)
│                                 │
│ What if Hermione was sorted     │ ← Description (truncated)
│ into Slytherin instead of...    │
│                                 │
│ 👤 @hermione_fan · 2 days ago   │ ← Creator + timestamp
│                                 │
│ 💬 12 convos | 🍴 5 forks        │ ← Stats row (quality score removed)
│                                 │
│ [Read More]               [❤️]  │ ← Actions
└─────────────────────────────────┘
```

**Version 1.1 Changes**: Quality score removed - scenarios now ranked by engagement metrics (conversations, forks) only

**Visual Hierarchy**:

- Book badge: Small, colored, top-left
- Title: Bold, 18px
- Description: Regular, 14px, gray-700
- Meta: Small, 12px, gray-500
- Stats: Conversation/fork counts emphasized

---

## Design Handoff

### Developer Resources

**Figma Files** (Future):

- Component library
- Responsive wireframes
- Interactive prototypes

**Design Tokens** (PandaCSS):

- Exported from Figma or manually defined
- Located in `panda.config.ts`

**Component Props**:

- PrimeVue documentation: https://primevue.org/
- Custom component storybook (future)

### QA Checklist

- [ ] All screens responsive (mobile, tablet, desktop)
- [ ] Color contrast meets WCAG AA
- [ ] Keyboard navigation works
- [ ] Screen reader tested (VoiceOver, NVDA)
- [ ] Loading states implemented
- [ ] Error states handled
- [ ] Empty states designed
- [ ] Touch targets minimum 44px
- [ ] Focus indicators visible
- [ ] Animations smooth (60fps)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-13  
**Maintained By**: Design Team  
**Feedback**: #gaji-design on Slack
