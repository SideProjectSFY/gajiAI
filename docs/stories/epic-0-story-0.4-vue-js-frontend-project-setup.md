# Story 0.4: Vue.js Frontend Project Setup (Pattern B - Single API Client)

**Epic**: Epic 0 - Project Setup & Infrastructure  
**Priority**: P0 - Critical  
**Status**: Completed  
**Estimated Effort**: 6 hours

## Description

Initialize Vue 3 + TypeScript + Vite frontend project with **PandaCSS**, **PrimeVue**, Pinia, and **single API client** (Spring Boot only). Implements **Pattern B** where frontend communicates ONLY with Spring Boot API Gateway.

## Dependencies

**Blocks**:

- Story 1.2-1.4: Scenario creation UI (needs frontend foundation)
- Story 4.3: Conversation Chat Interface (needs Vue components + SSE)
- Story 6.2: User Authentication Frontend (needs router and Pinia)
- All frontend stories

**Requires**:

- Story 0.1: Spring Boot Backend (API Gateway endpoints to consume)
- Story 0.5: Docker Configuration (Nginx reverse proxy for production)

## Acceptance Criteria

- [x] Vue 3 project initialized with Vite 5+ build tool
- [x] Package manager: **pnpm** (faster than npm/yarn, uses hard links)
- [x] TypeScript 5+ configured with strict mode enabled
- [x] Dependencies configured:
  - Vue Router 4+ (routing)
  - Pinia (state management)
  - **PandaCSS** (CSS-in-JS with static extraction)
  - **PrimeVue 4+** (UI component library)
  - Axios (HTTP client - Spring Boot ONLY)
  - VueUse (composition utilities)
  - date-fns (date formatting)
- [x] Project structure:
  ```
  frontend/
  ├── src/
  │   ├── assets/          # Static assets
  │   ├── components/      # Reusable components
  │   │   ├── common/      # Generic components
  │   │   ├── scenario/    # Scenario-related
  │   │   ├── conversation/# Conversation-related
  │   │   └── user/        # User-related
  │   ├── views/           # Page components
  │   ├── router/          # Route definitions
  │   ├── stores/          # Pinia stores
  │   ├── services/
  │   │   └── api.ts       # Axios instance (Spring Boot only)
  │   ├── types/           # TypeScript types
  │   ├── utils/           # Utility functions
  │   └── styles/          # Global styles
  ├── styled-system/       # Panda CSS generated files (gitignored)
  ├── panda.config.ts      # Panda CSS configuration
  ├── package.json
  └── .env.development
  ```
- [x] **PandaCSS configured** (`panda.config.ts`):
  - Custom theme (colors, typography, spacing)
  - Static extraction for zero-runtime CSS
  - TypeScript support for styled props
  - Output: `styled-system/` directory (generated, gitignored)
- [x] **PrimeVue integrated**:
  - Component library for UI elements (Button, Dialog, DataTable, etc.)
  - Styled with PandaCSS (NO default PrimeVue theme)
  - Tree-shaking enabled for smaller bundle size
- [x] Vue Router configured:
  - **Protected routes** (require authentication):
    - `/scenarios/create` - Scenario creation
    - `/conversations/:id` - Conversation chat
    - `/profile` - User profile
  - **Public routes**:
    - `/` - Home/landing page
    - `/login` - Login
    - `/register` - Registration
    - `/scenarios` - Browse scenarios
  - 404 page (`/404`)
  - Navigation guards for auth checking
- [x] Pinia stores initialized:
  - `useAuthStore` - User authentication state (JWT token, refresh token)
  - `useUserStore` - Current user profile data
  - `useScenarioStore` - Scenario browsing/creation state
  - `useConversationStore` - Conversation management with SSE streaming
- [x] **Single Axios instance** configured (`services/api.ts`):
  - Base URL: `http://localhost:8080/api/v1`
  - Request interceptor: Add JWT token from `useAuthStore`
  - Response interceptor: Handle 401 errors, auto-refresh token
  - SSE support for streaming AI responses
- [x] **Environment variables**:
  - `.env.development`: `VITE_API_BASE_URL=http://localhost:8080/api/v1`
  - `.env.production`: `VITE_API_BASE_URL=https://api.gaji.app/api/v1`
- [x] TypeScript strict mode enabled (`tsconfig.json`)
- [x] ESLint + Prettier configured
- [x] Application runs on port 3000 (Vite default)
- [x] **pnpm commands**:
  - `pnpm dev` - Run development server (port 3000)
  - `pnpm build` - Build for production
  - `pnpm prepare` - Generate Panda CSS (codegen)

## Technical Notes

**Single endpoint Implementation**:

- Frontend → Spring Boot ONLY (single API client)
- All AI requests go through Spring Boot proxy (`/api/v1/ai/*`)
- **Security Benefit**: No FastAPI URL or Gemini API keys exposed to browser
- **Simplicity**: Single API client, single authentication flow

**PandaCSS Benefits**:

- **Zero-runtime CSS**: All styling extracted at build time
- **Type-safe styling**: TypeScript autocomplete for style props
- **Smaller bundle**: ~40% smaller than Panda

**Example Axios Configuration** (`services/api.ts`):

```typescript
import axios from "axios";
import { useAuthStore } from "@/stores/auth";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api/v1",
  timeout: 60000, // 60s for AI operations
});

api.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`;
  }
  return config;
});

export default api;
```

## QA Checklist

### Functional Testing

- [x] Vue app starts with `pnpm dev` on port 3000
- [x] TypeScript compilation succeeds
- [x] PandaCSS codegen runs successfully
- [x] PrimeVue components render correctly
- [x] Router navigation works
- [x] Protected routes redirect to /login

### Configuration Testing

- [x] Environment variables loaded
- [x] VITE_API_BASE_URL points to Spring Boot
- [x] TypeScript strict mode catches errors
- [x] ESLint catches code quality issues

### Code Quality

- [x] All components use `<script setup>` syntax
- [x] Type annotations on all functions
- [x] No `any` types
- [x] ESLint passes

### Security

- [x] No API keys in frontend code
- [x] JWT tokens stored securely

## Estimated Effort

6 hours
