# Gaji Platform: Frontend Engineer Work Guide 🎨

**Last Updated**: 2025-11-19  
**Version**: 1.0  
**Engineer**: Frontend Engineer (Vue.js/TypeScript/PandaCSS)

---

## 📋 Overview

이 문서는 **Frontend Engineer** 전용 작업 가이드입니다. Vue.js Application, UI/UX, API 연동, 사용자 인터랙션 구현 등 모든 프론트엔드 작업이 포함됩니다.

**담당 영역**:

- Vue 3 Application (:3000)
- TypeScript, Vite Build System
- PandaCSS (Zero-runtime CSS-in-JS)
- PrimeVue (UI Component Library)
- Pinia (State Management)
- Axios (Single API Client)

**핵심 목표**:

- 페이지 로딩 <1초 (FCP)
- API 응답 처리 <500ms
- 반응형 디자인 (Mobile-first)
- 접근성 준수 (WCAG 2.1 AA)

---

## 🎯 Role & Responsibilities

### 주요 책임

1. **Vue.js Application 개발**: SPA 구조, 라우팅, 상태 관리
2. **UI/UX 구현**: PandaCSS + PrimeVue 기반 컴포넌트 개발
3. **API 연동**: Spring Boot Backend와 통신 (Axios)
4. **반응형 디자인**: 모바일-퍼스트, 다양한 디바이스 지원
5. **성능 최적화**: Code splitting, Lazy loading, Caching

### 기술 스택

- **Framework**: Vue 3 (Composition API), TypeScript
- **Build**: Vite 5+
- **Styling**: PandaCSS (Zero-runtime), Custom theme
- **Components**: PrimeVue 4+ (Button, Dialog, DataTable, etc.)
- **State**: Pinia (Store)
- **HTTP**: Axios (Single API client, JWT interceptor)
- **Router**: Vue Router 4
- **Form**: VeeValidate + Zod (Validation)

---

## 📅 Day-by-Day Work Schedule

### Day 1-2: Vue.js Frontend Setup (12h)

#### Day 1: 프로젝트 초기화 & 기본 설정 (6h)

**Story 0.4: Vue.js Frontend Setup**

**09:00-12:00 (3h): 프로젝트 생성 & 의존성 설치**

```bash
# 1. Vue 3 프로젝트 생성 (0.5h)
pnpm create vite@latest gaji-frontend -- --template vue-ts
cd gaji-frontend

# 2. 의존성 설치 (0.5h)
pnpm add vue-router@4 pinia axios
pnpm add -D @pandacss/dev vite-plugin-inspect

# 3. PandaCSS 설정 (1h)
pnpm panda init --postcss

# panda.config.ts
import { defineConfig } from '@pandacss/dev'

export default defineConfig({
  preflight: true,
  include: ['./src/**/*.{js,jsx,ts,tsx,vue}'],
  exclude: [],
  theme: {
    extend: {
      tokens: {
        colors: {
          primary: { value: '#3b82f6' },
          secondary: { value: '#8b5cf6' },
          success: { value: '#10b981' },
          danger: { value: '#ef4444' },
        }
      }
    }
  },
  outdir: 'styled-system',
})

# vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  css: {
    postcss: {
      plugins: [require('@pandacss/dev/postcss')()]
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
```

**13:00-15:00 (2h): PrimeVue & 프로젝트 구조**

```bash
# PrimeVue 설치 (1h)
pnpm add primevue primeicons

# src/main.ts
import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import 'primevue/resources/themes/lara-light-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import App from './App.vue'

const app = createApp(App)
app.use(PrimeVue)
app.mount('#app')

# 프로젝트 구조 설정 (1h)
mkdir -p src/{components,views,stores,services,utils,types}

# 구조:
# src/
# ├── components/         # 재사용 컴포넌트
# │   ├── common/        # Button, Card, Input 등
# │   ├── layout/        # Header, Footer, Sidebar
# │   └── features/      # 기능별 컴포넌트
# ├── views/             # 페이지 컴포넌트
# ├── stores/            # Pinia stores
# ├── services/          # API 서비스
# ├── utils/             # 유틸리티 함수
# └── types/             # TypeScript types
```

**16:00-18:00 (2h): Axios 설정 & Vue Router**

```typescript
// src/services/api.ts (1h)
import axios, { type AxiosInstance } from "axios";
import { useAuthStore } from "@/stores/auth";

const apiClient: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: JWT 토큰 자동 첨부
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: 에러 처리
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      const authStore = useAuthStore();
      authStore.logout();
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// src/router/index.ts (1h)
import { createRouter, createWebHistory } from "vue-router";
import HomePage from "@/views/HomePage.vue";
import NotFoundPage from "@/views/NotFoundPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: HomePage,
    },
    {
      path: "/books",
      name: "Books",
      component: () => import("@/views/BooksPage.vue"),
    },
    {
      path: "/:pathMatch(.*)*",
      name: "NotFound",
      component: NotFoundPage,
    },
  ],
});

export default router;
```

**체크포인트 (Day 1)**:

- [ ] `pnpm dev` 실행 성공 (port 3000)
- [ ] PandaCSS 스타일 적용 확인
- [ ] PrimeVue 컴포넌트 렌더링 확인 (Button 테스트)
- [ ] Axios API client 설정 완료

**의존성**:

- ⚠️ Story 0.1 (Spring Boot) 완료 후 API 호출 가능

---

#### Day 2: Pinia Store & 기본 레이아웃 (6h)

**09:00-11:00 (2h): Pinia 상태 관리 설정**

```typescript
// src/stores/auth.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { User } from "@/types/user";

export const useAuthStore = defineStore("auth", () => {
  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem("token"));

  // Getters
  const isAuthenticated = computed(() => !!token.value);
  const currentUser = computed(() => user.value);

  // Actions
  function setToken(newToken: string) {
    token.value = newToken;
    localStorage.setItem("token", newToken);
  }

  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem("token");
  }

  return { user, token, isAuthenticated, currentUser, setToken, logout };
});

// src/stores/scenario.ts
export const useScenarioStore = defineStore("scenario", () => {
  const scenarios = ref<Scenario[]>([]);
  const selectedScenario = ref<Scenario | null>(null);

  async function fetchScenarios() {
    // API 호출
  }

  return { scenarios, selectedScenario, fetchScenarios };
});
```

**11:00-13:00 (2h): 전역 레이아웃 컴포넌트**

```vue
<!-- src/components/layout/AppLayout.vue -->
<script setup lang="ts">
import { css } from "@/styled-system/css";
import AppHeader from "./AppHeader.vue";
import AppFooter from "./AppFooter.vue";
</script>

<template>
  <div :class="layoutClass">
    <AppHeader />
    <main :class="mainClass">
      <slot />
    </main>
    <AppFooter />
  </div>
</template>

<script lang="ts">
const layoutClass = css({
  display: "flex",
  flexDirection: "column",
  minHeight: "100vh",
  backgroundColor: "gray.50",
});

const mainClass = css({
  flex: 1,
  padding: "2rem",
  maxWidth: "1280px",
  margin: "0 auto",
  width: "100%",
});
</script>
```

**14:00-16:00 (2h): 네비게이션 바**

```vue
<!-- src/components/layout/AppHeader.vue -->
<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import Button from "primevue/button";
import { css } from "@/styled-system/css";

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push("/login");
};
</script>

<template>
  <header :class="headerClass">
    <div :class="containerClass">
      <router-link to="/" :class="logoClass"> Gaji Platform </router-link>

      <nav :class="navClass">
        <router-link to="/books" :class="linkClass">Books</router-link>
        <router-link to="/scenarios" :class="linkClass">Scenarios</router-link>

        <div v-if="authStore.isAuthenticated" :class="authClass">
          <span>{{ authStore.currentUser?.username }}</span>
          <Button label="Logout" @click="handleLogout" />
        </div>
        <div v-else>
          <Button label="Login" @click="router.push('/login')" />
        </div>
      </nav>
    </div>
  </header>
</template>

<script lang="ts">
const headerClass = css({
  backgroundColor: "white",
  boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  padding: "1rem 0",
});

const containerClass = css({
  maxWidth: "1280px",
  margin: "0 auto",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "0 2rem",
});

const logoClass = css({
  fontSize: "1.5rem",
  fontWeight: "bold",
  color: "primary",
  textDecoration: "none",
});

const navClass = css({
  display: "flex",
  gap: "2rem",
  alignItems: "center",
});

const linkClass = css({
  textDecoration: "none",
  color: "gray.700",
  _hover: { color: "primary" },
});
</script>
```

**16:00-18:00 (2h): 기본 페이지 스켈레톤**

```vue
<!-- src/views/HomePage.vue -->
<script setup lang="ts">
import Card from "primevue/card";
import Button from "primevue/button";
import { useRouter } from "vue-router";

const router = useRouter();
</script>

<template>
  <div>
    <h1>Welcome to Gaji Platform</h1>
    <p>Explore "what if" scenarios from your favorite books.</p>

    <div :class="cardGridClass">
      <Card>
        <template #title>Browse Books</template>
        <template #content>
          <p>Discover 10+ classic novels</p>
        </template>
        <template #footer>
          <Button label="Browse" @click="router.push('/books')" />
        </template>
      </Card>

      <Card>
        <template #title>Create Scenarios</template>
        <template #content>
          <p>Create your own "what if" scenarios</p>
        </template>
        <template #footer>
          <Button label="Create" @click="router.push('/scenarios/new')" />
        </template>
      </Card>
    </div>
  </div>
</template>

<!-- src/views/NotFoundPage.vue -->
<template>
  <div :class="notFoundClass">
    <h1>404 - Page Not Found</h1>
    <Button label="Go Home" @click="router.push('/')" />
  </div>
</template>
```

**체크포인트 (Day 2)**:

- [ ] 기본 레이아웃 렌더링 확인
- [ ] 네비게이션 작동 (Vue Router)
- [ ] 반응형 디자인 (모바일 대응)
- [ ] Pinia store 동작 확인

**의존성**: ❌ 없음 (독립적 UI 작업)

---

### Day 3-4: 독립적 UI 작업 (6h)

#### Day 3-4: 공통 컴포넌트 개발 (6h)

**작업 내용**:

1. **공통 컴포넌트 라이브러리** (4h)

   - `LoadingSpinner.vue`
   - `ErrorAlert.vue`
   - `ConfirmDialog.vue`
   - `EmptyState.vue`

2. **폼 컴포넌트** (2h)
   - `FormInput.vue` (VeeValidate 통합)
   - `FormTextarea.vue`
   - `FormSelect.vue`

```vue
<!-- src/components/common/LoadingSpinner.vue -->
<script setup lang="ts">
import ProgressSpinner from "primevue/progressspinner";
</script>

<template>
  <div :class="spinnerClass">
    <ProgressSpinner />
  </div>
</template>
```

**체크포인트 (Day 3-4)**:

- [ ] 공통 컴포넌트 5개 이상 완성
- [ ] Storybook 또는 컴포넌트 테스트 페이지 작성
- [ ] 반응형 디자인 확인

---

### Day 5-7: Epic 1 - Scenario System UI (30h)

#### Day 5-6: Scenario Creation Modal (12h)

**Story 1.2: Unified Scenario Creation Modal**

**09:00-13:00 (4h): 시나리오 폼 컴포넌트**

```vue
<!-- src/components/features/ScenarioForm.vue -->
<script setup lang="ts">
import { ref } from "vue";
import Dialog from "primevue/dialog";
import Dropdown from "primevue/dropdown";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Button from "primevue/button";
import { useScenarioStore } from "@/stores/scenario";

const scenarioStore = useScenarioStore();
const visible = ref(false);
const scenarioType = ref<
  "CHARACTER_CHANGE" | "EVENT_ALTERATION" | "SETTING_MODIFICATION"
>("CHARACTER_CHANGE");

const typeOptions = [
  { label: "Character Change", value: "CHARACTER_CHANGE" },
  { label: "Event Alteration", value: "EVENT_ALTERATION" },
  { label: "Setting Modification", value: "SETTING_MODIFICATION" },
];

// Form data
const formData = ref({
  novelId: "",
  characterName: "",
  originalTrait: "",
  changedTrait: "",
  reasoning: "",
});

const handleSubmit = async () => {
  // API 호출: POST /api/v1/scenarios
  try {
    await scenarioStore.createScenario(formData.value);
    visible.value = false;
    // Success message
  } catch (error) {
    // Error handling
  }
};
</script>

<template>
  <Button label="Create Scenario" @click="visible = true" />

  <Dialog
    v-model:visible="visible"
    header="Create What-If Scenario"
    :modal="true"
    :style="{ width: '50vw' }"
  >
    <div :class="formClass">
      <!-- Scenario Type Selection -->
      <div :class="fieldClass">
        <label>Scenario Type</label>
        <Dropdown
          v-model="scenarioType"
          :options="typeOptions"
          optionLabel="label"
          optionValue="value"
        />
      </div>

      <!-- Character Change Form -->
      <template v-if="scenarioType === 'CHARACTER_CHANGE'">
        <div :class="fieldClass">
          <label>Character Name</label>
          <InputText
            v-model="formData.characterName"
            placeholder="e.g., Elizabeth Bennet"
          />
        </div>

        <div :class="fieldClass">
          <label>Original Trait</label>
          <InputText
            v-model="formData.originalTrait"
            placeholder="e.g., Prideful"
          />
        </div>

        <div :class="fieldClass">
          <label>Changed Trait</label>
          <InputText
            v-model="formData.changedTrait"
            placeholder="e.g., Modest"
          />
        </div>

        <div :class="fieldClass">
          <label>Reasoning</label>
          <Textarea
            v-model="formData.reasoning"
            rows="4"
            placeholder="Why this change?"
          />
        </div>
      </template>

      <!-- Event/Setting Forms similar structure -->

      <div :class="actionsClass">
        <Button label="Cancel" @click="visible = false" severity="secondary" />
        <Button label="Create" @click="handleSubmit" />
      </div>
    </div>
  </Dialog>
</template>
```

**14:00-18:00 (4h): Character Change 폼**

- 캐릭터 자동완성 (VectorDB 검색 연동)
- Trait 입력 validation
- Reasoning textarea 확장

**Day 6 (4h): Event/Setting 폼 & API 연동**

```typescript
// src/services/scenarioService.ts
import apiClient from "./api";
import type { Scenario, CreateScenarioRequest } from "@/types/scenario";

export const scenarioService = {
  async create(data: CreateScenarioRequest): Promise<Scenario> {
    const response = await apiClient.post<Scenario>("/scenarios", data);
    return response.data;
  },

  async validate(scenarioId: string): Promise<ValidationResult> {
    const response = await apiClient.post(
      `/ai/scenarios/${scenarioId}/validate`
    );
    return response.data;
  },

  async list(filters?: ScenarioFilters): Promise<Scenario[]> {
    const response = await apiClient.get("/scenarios", { params: filters });
    return response.data;
  },
};

// Pinia Store
export const useScenarioStore = defineStore("scenario", () => {
  const scenarios = ref<Scenario[]>([]);

  async function createScenario(data: CreateScenarioRequest) {
    const newScenario = await scenarioService.create(data);
    scenarios.value.push(newScenario);
    return newScenario;
  }

  return { scenarios, createScenario };
});
```

**체크포인트 (Day 5-6)**:

- [ ] 시나리오 생성 폼 동작 (3가지 타입 지원)
- [ ] API 호출 성공 (`POST /api/v1/scenarios`)
- [ ] Validation UI 표시
- [ ] Success 후 리다이렉트 동작

**의존성**:

- ✅ Story 1.1 (Backend API) 완료 필요

---

#### Day 7: Validation 결과 UI & Integration Testing (6h)

**09:00-11:00 (2h): Validation 결과 UI**

```vue
<!-- src/components/features/ValidationResult.vue -->
<script setup lang="ts">
import { computed } from "vue";
import Card from "primevue/card";
import ProgressBar from "primevue/progressbar";
import Message from "primevue/message";

interface Props {
  validationResult: {
    quality_score: number;
    issues: string[];
    suggestions: string[];
  };
}

const props = defineProps<Props>();

const scoreColor = computed(() => {
  if (props.validationResult.quality_score >= 80) return "success";
  if (props.validationResult.quality_score >= 60) return "warning";
  return "danger";
});
</script>

<template>
  <Card>
    <template #title>Validation Result</template>
    <template #content>
      <div>
        <label>Quality Score</label>
        <ProgressBar
          :value="validationResult.quality_score"
          :severity="scoreColor"
        />
      </div>

      <div v-if="validationResult.issues.length > 0">
        <h3>Issues</h3>
        <Message
          v-for="issue in validationResult.issues"
          :key="issue"
          severity="warn"
        >
          {{ issue }}
        </Message>
      </div>

      <div v-if="validationResult.suggestions.length > 0">
        <h3>Suggestions</h3>
        <Message
          v-for="suggestion in validationResult.suggestions"
          :key="suggestion"
          severity="info"
        >
          {{ suggestion }}
        </Message>
      </div>
    </template>
  </Card>
</template>
```

**11:00-13:00 (2h): Integration Testing**

- 시나리오 생성 → 검증 → 저장 플로우 E2E 테스트
- Backend/AI Engineer와 협업 테스트

**14:00-16:00 (2h): 에러 처리 & UX 개선**

- Loading 상태 표시
- Error alert 표시
- Success toast 표시

**체크포인트 (Day 7)**:

- [ ] Validation 결과 UI 동작
- [ ] 전체 플로우 통합 테스트 통과
- [ ] 에러 처리 완료

---

### Day 8-11: Epic 4 - Conversation System UI (24h)

#### Day 8-9: Chat UI & Message Streaming (12h)

**Story 4.3: Conversation Forking UI**

**Day 8 (6h): Chat 컴포넌트 기본 구조**

```vue
<!-- src/components/features/ChatInterface.vue -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import InputText from "primevue/inputtext";
import Button from "primevue/button";
import { useConversationStore } from "@/stores/conversation";

interface Props {
  conversationId: string;
}

const props = defineProps<Props>();
const conversationStore = useConversationStore();

const messages = ref<Message[]>([]);
const userInput = ref("");
const isStreaming = ref(false);
const pollingInterval = ref<number | null>(null);

// Long Polling (2초 간격)
const startPolling = (taskId: string) => {
  pollingInterval.value = setInterval(async () => {
    const taskStatus = await conversationStore.getTaskStatus(taskId);

    if (taskStatus.status === "completed") {
      messages.value.push({
        role: "assistant",
        content: taskStatus.response,
      });
      stopPolling();
    }
  }, 2000) as unknown as number;
};

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
    pollingInterval.value = null;
  }
};

const handleSend = async () => {
  if (!userInput.value.trim()) return;

  // Add user message
  messages.value.push({
    role: "user",
    content: userInput.value,
  });

  // Call API: POST /api/v1/conversations/{id}/messages
  isStreaming.value = true;
  const response = await conversationStore.sendMessage(
    props.conversationId,
    userInput.value
  );

  // Start polling for AI response
  startPolling(response.task_id);

  userInput.value = "";
};

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <div :class="chatClass">
    <!-- Messages -->
    <div :class="messagesClass">
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="messageClass(msg.role)"
      >
        <div :class="messageBubbleClass">
          {{ msg.content }}
        </div>
      </div>

      <div v-if="isStreaming" :class="streamingClass">
        <ProgressSpinner />
        <span>AI is thinking...</span>
      </div>
    </div>

    <!-- Input -->
    <div :class="inputClass">
      <InputText
        v-model="userInput"
        placeholder="Type your message..."
        @keyup.enter="handleSend"
        :class="inputFieldClass"
      />
      <Button
        label="Send"
        icon="pi pi-send"
        @click="handleSend"
        :disabled="isStreaming"
      />
    </div>
  </div>
</template>
```

**Day 9 (6h): Fork UI & API 연동**

```vue
<!-- src/components/features/ForkButton.vue -->
<script setup lang="ts">
import { ref } from "vue";
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import { useConversationStore } from "@/stores/conversation";

interface Props {
  conversationId: string;
  totalMessages: number;
}

const props = defineProps<Props>();
const conversationStore = useConversationStore();

const showDialog = ref(false);
const messageCountToCopy = ref(Math.min(6, props.totalMessages));

const handleFork = async () => {
  // API: POST /api/v1/conversations/{id}/fork
  const newConversation = await conversationStore.forkConversation(
    props.conversationId,
    messageCountToCopy.value
  );

  // Redirect to new conversation
  router.push(`/conversations/${newConversation.id}`);
};
</script>

<template>
  <Button
    label="Fork Conversation"
    icon="pi pi-code-branch"
    @click="showDialog = true"
  />

  <Dialog v-model:visible="showDialog" header="Fork Conversation" :modal="true">
    <div>
      <p>
        Copy the first <strong>{{ messageCountToCopy }}</strong> messages to
        create a new conversation branch.
      </p>
      <p>(Maximum: {{ Math.min(6, totalMessages) }} messages)</p>

      <Slider
        v-model="messageCountToCopy"
        :min="1"
        :max="Math.min(6, totalMessages)"
      />
    </div>

    <template #footer>
      <Button label="Cancel" @click="showDialog = false" severity="secondary" />
      <Button label="Fork" @click="handleFork" />
    </template>
  </Dialog>
</template>
```

**체크포인트 (Day 8-9)**:

- [ ] Chat UI 동작 (메시지 송수신)
- [ ] Long Polling 동작 (2초 간격)
- [ ] Fork UI 동작 (min(6, total) 메시지 복사)
- [ ] API 연동 완료

**의존성**:

- ✅ Story 4.1 (Backend API) 완료 필요
- ✅ Story 4.2 (AI Streaming) 완료 필요

---

#### Day 10-11: Chat UX 개선 & 성능 최적화 (12h)

**Day 10 (6h): UX 개선**

1. **Message 렌더링 최적화** (2h)

   - Virtual scrolling (큰 대화 목록)
   - Markdown 렌더링 (AI 응답)
   - Code highlighting

2. **Typing indicator** (2h)

   - 실시간 타이핑 표시
   - Streaming 중 애니메이션

3. **Message actions** (2h)
   - Copy message
   - Regenerate response
   - Delete message

**Day 11 (6h): 성능 최적화**

1. **Code splitting** (2h)

   - Lazy loading routes
   - Dynamic imports

2. **Caching** (2h)

   - Axios response caching
   - LocalStorage for conversations

3. **Image optimization** (2h)
   - Lazy loading images
   - WebP format support

**체크포인트 (Day 10-11)**:

- [ ] Chat UX 개선 완료
- [ ] 성능 최적화 완료 (Lighthouse score >90)

---

### Day 12-13: Epic 3 - Discovery UI (26h)

#### Day 12: Book Browse & Detail Pages (16h)

**Story 3.1: Book Browse Page (8h)**

```vue
<!-- src/views/BooksPage.vue -->
<script setup lang="ts">
import { ref, onMounted } from "vue";
import DataView from "primevue/dataview";
import Card from "primevue/card";
import Paginator from "primevue/paginator";
import { useBookStore } from "@/stores/book";

const bookStore = useBookStore();
const books = ref([]);
const loading = ref(true);

// Pagination
const currentPage = ref(0);
const rowsPerPage = ref(12);

onMounted(async () => {
  loading.value = true;
  await bookStore.fetchBooks();
  books.value = bookStore.books;
  loading.value = false;
});

const onPageChange = (event: any) => {
  currentPage.value = event.page;
};
</script>

<template>
  <div>
    <h1>Browse Books</h1>

    <LoadingSpinner v-if="loading" />

    <DataView
      v-else
      :value="books"
      :layout="'grid'"
      :paginator="true"
      :rows="rowsPerPage"
    >
      <template #grid="{ data }">
        <div :class="bookCardClass">
          <Card>
            <template #header>
              <img :src="data.coverImage" :alt="data.title" />
            </template>
            <template #title>{{ data.title }}</template>
            <template #subtitle>{{ data.author }}</template>
            <template #content>
              <p>{{ data.summary }}</p>
            </template>
            <template #footer>
              <Button
                label="View Details"
                @click="router.push(`/books/${data.id}`)"
              />
            </template>
          </Card>
        </div>
      </template>
    </DataView>

    <Paginator
      :rows="rowsPerPage"
      :totalRecords="books.length"
      @page="onPageChange"
    />
  </div>
</template>
```

**Story 3.2: Book Detail Page (10h)**

```vue
<!-- src/views/BookDetailPage.vue -->
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import Card from "primevue/card";
import TabView from "primevue/tabview";
import TabPanel from "primevue/tabpanel";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import { useBookStore } from "@/stores/book";

const route = useRoute();
const bookStore = useBookStore();

const book = ref<Book | null>(null);
const scenarios = ref<Scenario[]>([]);

onMounted(async () => {
  const bookId = route.params.id as string;
  book.value = await bookStore.getBook(bookId);
  scenarios.value = await bookStore.getBookScenarios(bookId);
});
</script>

<template>
  <div v-if="book">
    <!-- Book Header -->
    <div :class="headerClass">
      <img :src="book.coverImage" :alt="book.title" />
      <div>
        <h1>{{ book.title }}</h1>
        <h2>{{ book.author }}</h2>
        <p>{{ book.summary }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <TabView>
      <TabPanel header="Scenarios">
        <DataTable :value="scenarios" paginator :rows="10">
          <Column field="title" header="Scenario Title" />
          <Column field="type" header="Type" />
          <Column field="createdAt" header="Created" />
          <Column>
            <template #body="{ data }">
              <Button
                label="View"
                @click="router.push(`/scenarios/${data.id}`)"
              />
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <TabPanel header="Characters">
        <!-- Characters list -->
      </TabPanel>

      <TabPanel header="Locations">
        <!-- Locations list -->
      </TabPanel>
    </TabView>
  </div>
</template>
```

**체크포인트 (Day 12)**:

- [ ] Book Browse Page 동작 (카드 레이아웃, Pagination)
- [ ] Book Detail Page 동작 (Tabs, Scenario 리스트)
- [ ] API 연동 완료

---

#### Day 13: Scenario Browse & Search UI (10h)

**Story 3.3: Scenario Browse UI (8h)**

```vue
<!-- src/views/ScenariosPage.vue -->
<script setup lang="ts">
import { ref, onMounted } from "vue";
import DataView from "primevue/dataview";
import Dropdown from "primevue/dropdown";
import MultiSelect from "primevue/multiselect";
import { useScenarioStore } from "@/stores/scenario";

const scenarioStore = useScenarioStore();
const scenarios = ref([]);

// Filters
const typeFilter = ref(null);
const novelFilter = ref([]);

const typeOptions = [
  { label: "All", value: null },
  { label: "Character Change", value: "CHARACTER_CHANGE" },
  { label: "Event Alteration", value: "EVENT_ALTERATION" },
  { label: "Setting Modification", value: "SETTING_MODIFICATION" },
];

const applyFilters = async () => {
  scenarios.value = await scenarioStore.fetchScenarios({
    type: typeFilter.value,
    novels: novelFilter.value,
  });
};

onMounted(async () => {
  await applyFilters();
});
</script>

<template>
  <div>
    <h1>Browse Scenarios</h1>

    <!-- Filters -->
    <div :class="filtersClass">
      <Dropdown
        v-model="typeFilter"
        :options="typeOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Filter by Type"
        @change="applyFilters"
      />

      <MultiSelect
        v-model="novelFilter"
        :options="novelOptions"
        optionLabel="title"
        optionValue="id"
        placeholder="Filter by Novel"
        @change="applyFilters"
      />
    </div>

    <!-- Scenarios Grid -->
    <DataView :value="scenarios" :layout="'grid'">
      <template #grid="{ data }">
        <ScenarioCard :scenario="data" />
      </template>
    </DataView>
  </div>
</template>
```

**체크포인트 (Day 13)**:

- [ ] Scenario Browse UI 동작 (필터링, 카드 레이아웃)
- [ ] Search UI 동작 (검색, 고급 필터)

**의존성**:

- ✅ Epic 0, 1 완료

---

### Day 14: Epic 5 - Tree Visualization (20h)

**Story 5.1-5.2: D3.js Tree Component (14h)**

```vue
<!-- src/components/features/ConversationTree.vue -->
<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import * as d3 from "d3";
import type { ConversationNode } from "@/types/conversation";

interface Props {
  conversationId: string;
}

const props = defineProps<Props>();
const treeContainer = ref<HTMLElement | null>(null);

const fetchTreeData = async (convId: string) => {
  // API: GET /api/v1/conversations/{id}/tree
  const response = await apiClient.get(`/conversations/${convId}/tree`);
  return response.data;
};

const renderTree = (data: ConversationNode) => {
  if (!treeContainer.value) return;

  // D3.js tree layout
  const width = 800;
  const height = 600;

  const svg = d3
    .select(treeContainer.value)
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const g = svg.append("g").attr("transform", "translate(40,0)");

  // Tree layout
  const tree = d3.tree<ConversationNode>().size([height, width - 160]);

  const root = d3.hierarchy(data);
  tree(root);

  // Links
  g.selectAll(".link")
    .data(root.links())
    .enter()
    .append("path")
    .attr("class", "link")
    .attr(
      "d",
      d3
        .linkHorizontal()
        .x((d: any) => d.y)
        .y((d: any) => d.x)
    );

  // Nodes
  const node = g
    .selectAll(".node")
    .data(root.descendants())
    .enter()
    .append("g")
    .attr("class", "node")
    .attr("transform", (d: any) => `translate(${d.y},${d.x})`);

  node.append("circle").attr("r", 5);

  node
    .append("text")
    .attr("dy", 3)
    .attr("x", (d: any) => (d.children ? -8 : 8))
    .style("text-anchor", (d: any) => (d.children ? "end" : "start"))
    .text((d: any) => d.data.content.slice(0, 30) + "...");

  // Zoom & Pan
  const zoom = d3
    .zoom()
    .scaleExtent([0.5, 2])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svg.call(zoom as any);
};

onMounted(async () => {
  const treeData = await fetchTreeData(props.conversationId);
  renderTree(treeData);
});
</script>

<template>
  <div ref="treeContainer" :class="treeClass"></div>
</template>

<style scoped>
.link {
  fill: none;
  stroke: #ccc;
  stroke-width: 2px;
}

.node circle {
  fill: #3b82f6;
  stroke: #1e40af;
  stroke-width: 2px;
}

.node text {
  font-size: 12px;
  font-family: sans-serif;
}
</style>
```

**Story 5.3: Navigation (6h)**

- 노드 클릭 → 해당 메시지로 이동
- 하이라이트 효과
- Minimap

**체크포인트 (Day 14)**:

- [ ] D3.js Tree 렌더링 동작
- [ ] Zoom/Pan 기능 동작
- [ ] 노드 클릭 네비게이션 동작

**의존성**:

- ✅ Epic 4 완료 (Conversation API)

---

## 🚦 Daily Integration Checkpoints

### 매일 오후 6시: Frontend 통합 테스트

**Day 1-2**:

- [ ] Vue 앱 :3000 실행 확인
- [ ] PandaCSS 스타일 적용 확인
- [ ] PrimeVue 컴포넌트 렌더링 확인

**Day 3-4**:

- [ ] 기본 레이아웃 렌더링
- [ ] 네비게이션 작동
- [ ] 반응형 디자인 확인

**Day 5-7**:

- [ ] 시나리오 생성 폼 동작
- [ ] API 호출 성공
- [ ] Validation UI 표시

**Day 8-11**:

- [ ] Chat UI 동작
- [ ] Long Polling 동작 (2초)
- [ ] Fork 성공

**Day 12-13**:

- [ ] Book Browse/Detail 페이지 동작
- [ ] Scenario Browse 동작
- [ ] Search 동작

**Day 14**:

- [ ] Conversation Tree 렌더링
- [ ] Zoom/Pan 동작
- [ ] 전체 User Journey 테스트 통과

---

## 🔧 Troubleshooting Guide

### 이슈 1: Axios 401 Unauthorized

**원인**: JWT 토큰 만료 또는 미설정  
**해결**:

```typescript
// Check authStore token
const authStore = useAuthStore();
console.log("Token:", authStore.token);

// Refresh token logic
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try refresh token
      await authStore.refreshToken();
      // Retry request
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

### 이슈 2: PandaCSS 스타일 미적용

**원인**: PostCSS 설정 누락  
**해결**:

```bash
# postcss.config.js 확인
module.exports = {
  plugins: {
    '@pandacss/dev/postcss': {},
  },
}

# panda.config.ts include 경로 확인
include: ['./src/**/*.{js,jsx,ts,tsx,vue}']
```

### 이슈 3: Vite Proxy CORS 에러

**원인**: Backend CORS 설정 또는 Vite proxy 설정 오류  
**해결**:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '/api/v1')
    }
  }
}
```

### 이슈 4: PrimeVue 컴포넌트 렌더링 안됨

**원인**: PrimeVue CSS 미import  
**해결**:

```typescript
// main.ts
import "primevue/resources/themes/lara-light-blue/theme.css";
import "primevue/resources/primevue.min.css";
import "primeicons/primeicons.css";
```

### 이슈 5: Router Navigation Guard 무한 루프

**원인**: 잘못된 redirect 로직  
**해결**:

```typescript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Avoid infinite loop
    if (to.path !== "/login") {
      next("/login");
    } else {
      next();
    }
  } else {
    next();
  }
});
```

### 이슈 6: Long Polling Memory Leak

**원인**: Polling interval 미정리  
**해결**:

```typescript
// Component unmount 시 정리
onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
  }
});
```

---

## 📈 Success Metrics (KPIs)

### 성능 목표

- **FCP (First Contentful Paint)**: <1초
- **LCP (Largest Contentful Paint)**: <2.5초
- **API Response Handling**: <500ms
- **Bundle Size**: <200KB (gzipped)

### 품질 목표

- **Lighthouse Score**: >90 (Performance, Accessibility, Best Practices)
- **TypeScript Coverage**: 100% (strict mode)
- **Component Tests**: >80% coverage
- **Responsive Design**: 100% (mobile, tablet, desktop)

### 사용자 경험 목표

- **Form Validation**: Instant feedback (<100ms)
- **Loading States**: 모든 비동기 작업
- **Error Handling**: User-friendly messages
- **Accessibility**: WCAG 2.1 AA 준수

---

## 📚 Documentation Checklist

### 컴포넌트 문서

- [ ] 공통 컴포넌트 Props/Events 문서화
- [ ] Storybook 또는 컴포넌트 가이드 작성

### API 연동 문서

- [ ] API Service 함수 목록
- [ ] Request/Response 타입 정의
- [ ] Error Handling 가이드

### 스타일 가이드

- [ ] PandaCSS Token 사용 가이드
- [ ] 색상/타이포그래피/간격 표준
- [ ] 반응형 디자인 브레이크포인트

### 배포 가이드

- [ ] Build & Deploy 절차
- [ ] ENV 변수 설정 가이드
- [ ] 성능 최적화 체크리스트

---

**Document Owner**: Frontend Engineer  
**Last Updated**: 2025-11-19  
**Next Review**: Day 7 (Epic 1 완성 후)
