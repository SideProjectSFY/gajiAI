# Story 6.1: User Registration & Authentication Backend

**Epic**: Epic 6 - User Authentication & Social Features  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Implement JWT-based authentication with Spring Boot Security, including user registration, login, and token refresh endpoints.

## Dependencies

**Blocks**:

- Story 6.2: User Authentication Frontend (needs auth API)
- Story 6.3-6.9: All social features (require authenticated users)
- All other epics (need user authentication)

**Requires**:

- Story 0.1: Spring Boot Backend Setup
- Story 0.3: PostgreSQL Database Setup

## Acceptance Criteria

- [ ] `users` table created with UUID primary key, email (unique), password_hash, username, profile_image_url, created_at
- [ ] POST /api/auth/register endpoint validates email/password, hashes password with BCrypt, returns JWT token
- [ ] POST /api/auth/login endpoint validates credentials, returns access token + refresh token
- [ ] POST /api/auth/refresh endpoint validates refresh token, returns new access token
- [ ] POST /api/auth/logout endpoint blacklists refresh token
- [ ] Email validation: valid format, unique constraint enforced
- [ ] Password requirements: min 8 chars, 1 uppercase, 1 lowercase, 1 number
- [ ] JWT access token expires in 1 hour, refresh token expires in 7 days
- [ ] Spring Security filters validate JWT on protected endpoints
- [ ] @CurrentUser annotation injects authenticated user in controllers
- [ ] Unit tests >80% coverage on auth service

## Technical Notes

**JWT Payload**:

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "username": "hermione_granger",
  "iat": 1705320000,
  "exp": 1705323600
}
```

**Security Configuration**:

- Public endpoints: /api/auth/\*, /api/scenarios (GET), /api/conversations (GET)
- Protected endpoints: All POST/PUT/DELETE, user-specific GET requests
- CORS enabled for Vue.js frontend (http://localhost:5173)

## QA Checklist

### Functional Testing

- [ ] Register new user with valid email/password
- [ ] Register with duplicate email returns 409 Conflict
- [ ] Login with valid credentials returns tokens
- [ ] Login with invalid credentials returns 401 Unauthorized
- [ ] Refresh token generates new access token
- [ ] Logout invalidates refresh token
- [ ] Protected endpoint rejects unauthenticated request

### Password Security

- [ ] Password hashed with BCrypt (12 rounds)
- [ ] Raw password never stored or logged
- [ ] Password validation enforces complexity rules
- [ ] Weak passwords rejected (e.g., "12345678")

### JWT Validation

- [ ] Expired access token returns 401
- [ ] Invalid signature returns 401
- [ ] Tampered payload returns 401
- [ ] @CurrentUser correctly extracts user from token
- [ ] Refresh token blacklist prevents reuse after logout

### Performance

- [ ] Registration < 200ms
- [ ] Login < 150ms
- [ ] JWT validation < 10ms per request
- [ ] Database query uses index on email column

### Security

- [ ] SQL injection prevented
- [ ] XSS attacks prevented in email/username fields
- [ ] Rate limiting: 5 failed login attempts → 15 min lockout
- [ ] HTTPS enforced in production

## Estimated Effort

10 hours
