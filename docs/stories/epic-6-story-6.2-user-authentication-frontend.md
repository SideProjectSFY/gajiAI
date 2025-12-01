# Story 6.2: User Authentication Frontend

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 8 hours

## Description

Build Vue 3 login/register pages with form validation, JWT token management in memory (no localStorage), and Vue Router navigation guards for protected routes.

## Dependencies

**Blocks**:

- Story 6.3: User Profile Page
- Story 6.5: Follow/Unfollow UI
- Story 6.7: Like Button UI
- Story 6.9: Memo UI

**Requires**:

- Story 6.1: User Authentication Backend (JWT endpoints)

## Acceptance Criteria

- [ ] `/login` and `/register` pages with clean form UI
- [ ] Registration form: username, email, password, confirm password
- [ ] Login form: email, password, "Remember me" checkbox
- [ ] Client-side validation: email format, password strength (8+ chars), matching passwords
- [ ] Form error messages displayed inline
- [ ] JWT tokens stored in memory (Pinia store), NOT localStorage
- [ ] Axios interceptor adds JWT to Authorization header
- [ ] Vue Router navigation guards protect authenticated routes
- [ ] Redirect to `/login` on 401 Unauthorized
- [ ] Successful login redirects to `/` or original destination
- [ ] Logout clears tokens and redirects to `/login`
- [ ] Unit tests >80% coverage

## Technical Notes

**Pinia Auth Store**:

```typescript
// stores/auth.ts
import { defineStore } from "pinia";
import api from "@/services/api";

interface User {
  id: string;
  username: string;
  email: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    currentUser: (state) => state.user,
  },

  actions: {
    async register(username: string, email: string, password: string) {
      try {
        const response = await api.post("/auth/register", {
          username,
          email,
          password,
        });

        this.user = response.data.user;
        this.accessToken = response.data.accessToken;
        this.refreshToken = response.data.refreshToken;

        return { success: true };
      } catch (error: any) {
        return {
          success: false,
          message: error.response?.data?.message || "Registration failed",
        };
      }
    },

    async login(email: string, password: string, rememberMe: boolean = false) {
      try {
        const response = await api.post("/auth/login", {
          email,
          password,
          rememberMe,
        });

        this.user = response.data.user;
        this.accessToken = response.data.accessToken;
        this.refreshToken = response.data.refreshToken;

        return { success: true };
      } catch (error: any) {
        return {
          success: false,
          message: error.response?.data?.message || "Login failed",
        };
      }
    },

    async refreshAccessToken() {
      if (!this.refreshToken) {
        throw new Error("No refresh token available");
      }

      try {
        const response = await api.post("/auth/refresh", {
          refreshToken: this.refreshToken,
        });

        this.accessToken = response.data.accessToken;
        return true;
      } catch (error) {
        this.logout();
        return false;
      }
    },

    async logout() {
      try {
        await api.post("/auth/logout", {
          refreshToken: this.refreshToken,
        });
      } catch (error) {
        console.error("Logout failed:", error);
      } finally {
        this.user = null;
        this.accessToken = null;
        this.refreshToken = null;
      }
    },
  },
});
```

**Axios Interceptor**:

```typescript
// services/api.ts
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import router from "@/router";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api",
  timeout: 10000,
});

// Request interceptor: Add JWT token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const authStore = useAuthStore();
      const refreshed = await authStore.refreshAccessToken();

      if (refreshed) {
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`;
        return api(originalRequest);
      } else {
        // Refresh failed, redirect to login
        router.push("/login");
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

**Vue Router Navigation Guards**:

```typescript
// router/index.ts
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/LoginPage.vue"),
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/RegisterPage.vue"),
  },
  {
    path: "/",
    name: "Home",
    component: () => import("@/views/HomePage.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/scenarios",
    name: "Scenarios",
    component: () => import("@/views/ScenariosPage.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Save original destination for redirect after login
    next({ name: "Login", query: { redirect: to.fullPath } });
  } else if (
    (to.name === "Login" || to.name === "Register") &&
    authStore.isAuthenticated
  ) {
    // Already logged in, redirect to home
    next({ name: "Home" });
  } else {
    next();
  }
});

export default router;
```

**Login Page Component**:

```vue
<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>Welcome Back</h1>
      <p class="subtitle">Log in to continue your "What If" adventures</p>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="your@email.com"
            required
            :class="{ 'input-error': errors.email }"
          />
          <span v-if="errors.email" class="error-message">{{
            errors.email
          }}</span>
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            required
            :class="{ 'input-error': errors.password }"
          />
          <span v-if="errors.password" class="error-message">{{
            errors.password
          }}</span>
        </div>

        <div class="form-group checkbox">
          <input id="remember" v-model="form.rememberMe" type="checkbox" />
          <label for="remember">Remember me</label>
        </div>

        <button type="submit" :disabled="isLoading" class="btn-primary">
          {{ isLoading ? "Logging in..." : "Log In" }}
        </button>

        <p class="form-footer">
          Don't have an account?
          <router-link to="/register" class="link">Sign up</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = reactive({
  email: "",
  password: "",
  rememberMe: false,
});

const errors = reactive({
  email: "",
  password: "",
});

const isLoading = ref(false);

const validateForm = (): boolean => {
  errors.email = "";
  errors.password = "";

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(form.email)) {
    errors.email = "Invalid email format";
    return false;
  }

  if (form.password.length < 8) {
    errors.password = "Password must be at least 8 characters";
    return false;
  }

  return true;
};

const handleLogin = async () => {
  if (!validateForm()) return;

  isLoading.value = true;

  const result = await authStore.login(
    form.email,
    form.password,
    form.rememberMe
  );

  isLoading.value = false;

  if (result.success) {
    const redirect = (route.query.redirect as string) || "/";
    router.push(redirect);
  } else {
    errors.password = result.message || "Login failed";
  }
};
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-card {
  background: white;
  border-radius: 12px;
  padding: 3rem;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.auth-card h1 {
  font-size: 28px;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input[type="email"],
.form-group input[type="password"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.input-error {
  border-color: #f44336 !important;
}

.error-message {
  color: #f44336;
  font-size: 12px;
  margin-top: 0.25rem;
  display: block;
}

.checkbox {
  display: flex;
  align-items: center;
}

.checkbox input {
  margin-right: 0.5rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 14px;
}

.link {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  text-decoration: underline;
}
</style>
```

**Register Page Component**:

```vue
<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>Create Account</h1>
      <p class="subtitle">Start exploring "What If" scenarios</p>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="johndoe"
            required
            :class="{ 'input-error': errors.username }"
          />
          <span v-if="errors.username" class="error-message">{{
            errors.username
          }}</span>
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="your@email.com"
            required
            :class="{ 'input-error': errors.email }"
          />
          <span v-if="errors.email" class="error-message">{{
            errors.email
          }}</span>
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            required
            :class="{ 'input-error': errors.password }"
          />
          <span v-if="errors.password" class="error-message">{{
            errors.password
          }}</span>
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            placeholder="••••••••"
            required
            :class="{ 'input-error': errors.confirmPassword }"
          />
          <span v-if="errors.confirmPassword" class="error-message">
            {{ errors.confirmPassword }}
          </span>
        </div>

        <button type="submit" :disabled="isLoading" class="btn-primary">
          {{ isLoading ? "Creating Account..." : "Sign Up" }}
        </button>

        <p class="form-footer">
          Already have an account?
          <router-link to="/login" class="link">Log in</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const errors = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const isLoading = ref(false);

const validateForm = (): boolean => {
  errors.username = "";
  errors.email = "";
  errors.password = "";
  errors.confirmPassword = "";

  if (form.username.length < 3) {
    errors.username = "Username must be at least 3 characters";
    return false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(form.email)) {
    errors.email = "Invalid email format";
    return false;
  }

  if (form.password.length < 8) {
    errors.password = "Password must be at least 8 characters";
    return false;
  }

  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
    return false;
  }

  return true;
};

const handleRegister = async () => {
  if (!validateForm()) return;

  isLoading.value = true;

  const result = await authStore.register(
    form.username,
    form.email,
    form.password
  );

  isLoading.value = false;

  if (result.success) {
    router.push("/");
  } else {
    errors.email = result.message || "Registration failed";
  }
};
</script>
```

## QA Checklist

### Functional Testing

- [ ] Registration creates new user and logs in automatically
- [ ] Login with valid credentials works correctly
- [ ] Logout clears tokens and redirects to login
- [ ] "Remember me" persists refresh token (longer TTL)
- [ ] Redirect to original destination after login works
- [ ] Navigation guard blocks unauthenticated access
- [ ] Token refresh works on 401 response

### Validation Testing

- [ ] Email format validation works
- [ ] Password length validation (≥8 chars)
- [ ] Confirm password matching validation
- [ ] Username length validation (≥3 chars)
- [ ] Error messages display inline
- [ ] Form submission disabled during loading

### Security Testing

- [ ] Tokens stored ONLY in memory (Pinia), NOT localStorage
- [ ] Tokens cleared on logout
- [ ] Axios interceptor adds Authorization header correctly
- [ ] 401 response triggers token refresh attempt
- [ ] Failed refresh redirects to login

### UI/UX Testing

- [ ] Login/register pages responsive on mobile
- [ ] Form inputs have proper labels and placeholders
- [ ] Loading state shows during API calls
- [ ] Error messages clear and actionable

### Performance

- [ ] Login completes < 500ms
- [ ] Registration completes < 800ms
- [ ] Token refresh happens transparently (< 300ms)

## Estimated Effort

8 hours
