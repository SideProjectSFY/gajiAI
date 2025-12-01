# API Documentation

**Project**: Gaji - Interactive Fiction Platform  
**Last Updated**: 2025-11-13  
**API Version**: v1

---

## Service Architecture

This project uses a **Microservice Architecture (MSA)** with strict database access separation:

- **Spring Boot (Port 8080)**: PostgreSQL ONLY (metadata, user data, social features)
- **FastAPI (Port 8000)**: VectorDB ONLY (novel content, embeddings, semantic search)

### Base URLs

| Service     | Base URL                    | Database Access      |
| ----------- | --------------------------- | -------------------- |
| Spring Boot | `http://localhost:8080/api` | PostgreSQL (MyBatis) |
| FastAPI     | `http://localhost:8000/api` | VectorDB (ChromaDB)  |

### Internal APIs

Both services expose **internal endpoints** for cross-service communication:

- **Spring Boot Internal API**: `/api/internal/*` (called by FastAPI for PostgreSQL data)
- **FastAPI Internal API**: `/api/ai/*` (called by Spring Boot for VectorDB queries)

**Frontend** calls both services directly:

- Spring Boot: User management, scenario CRUD, social features
- FastAPI: AI conversation, novel ingestion, semantic search

---

## Table of Contents

### Spring Boot APIs (PostgreSQL)

1. [Authentication](#authentication)
2. [Scenarios](#scenarios)
3. [Conversations - Metadata](#conversations-metadata)
4. [Users](#users)
5. [Social Features](#social-features)
6. [Internal API - Spring Boot](#internal-api-spring-boot)

### FastAPI APIs (VectorDB)

7. [Novel Ingestion](#novel-ingestion-fastapi)
8. [AI Conversation](#ai-conversation-fastapi)
9. [Semantic Search](#semantic-search-fastapi)
10. [Character Extraction](#character-extraction-fastapi)
11. [Internal API - FastAPI](#internal-api-fastapi)

### Cross-Cutting Concerns

12. [Error Handling](#error-handling)
13. [Performance Targets](#performance-targets)
14. [Code Examples](#code-examples)

---

## Spring Boot APIs (PostgreSQL)

> **Database Access**: PostgreSQL ONLY via MyBatis. For VectorDB queries, Spring Boot calls FastAPI `/api/ai/*`.

## Authentication

### Register User

Create a new user account.

**Endpoint**: `POST /api/auth/register`  
**Authentication**: None (Public)  
**Performance**: < 200ms

#### Request

```json
{
  "email": "user@example.com",
  "username": "hermione_fan",
  "password": "SecurePassword123!"
}
```

**Validation Rules**:

- Email: Valid format, unique, max 255 chars
- Username: 3-50 chars, alphanumeric + underscore, unique
- Password: Min 8 chars, at least 1 uppercase, 1 lowercase, 1 number

#### Response (201 Created)

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "hermione_fan",
    "created_at": "2025-11-13T10:30:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

#### Errors

- `400 Bad Request`: Validation failed
- `409 Conflict`: Email or username already exists
- `500 Internal Server Error`: Server error

---

### Login

Authenticate existing user.

**Endpoint**: `POST /api/auth/login`  
**Authentication**: None (Public)  
**Performance**: < 100ms

#### Request

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

#### Response (200 OK)

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "hermione_fan",
    "bio": "Slytherin Hermione enthusiast",
    "avatar_url": "https://example.com/avatar.jpg"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

#### Errors

- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded (5 attempts per 15 minutes)

---

### Refresh Token

Obtain new access token using refresh token.

**Endpoint**: `POST /api/auth/refresh`  
**Authentication**: None (Requires valid refresh token)  
**Performance**: < 50ms

#### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

#### Errors

- `401 Unauthorized`: Invalid or expired refresh token
- `403 Forbidden`: Token has been blacklisted

---

### Logout

Blacklist refresh token.

**Endpoint**: `POST /api/auth/logout`  
**Authentication**: Required (Bearer token)  
**Performance**: < 50ms

#### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Response (200 OK)

```json
{
  "message": "Logged out successfully"
}
```

---

## Scenarios

### Create Scenario

Create a new What If scenario.

**Endpoint**: `POST /api/scenarios`  
**Authentication**: Required  
**Performance**: < 200ms

#### Request

```json
{
  "base_story": "harry_potter",
  "scenario_type": "CHARACTER_CHANGE",
  "parameters": {
    "character": "Hermione Granger",
    "property": "house",
    "original_value": "Gryffindor",
    "new_value": "Slytherin",
    "change_point": "Sorting Hat ceremony",
    "ripple_effects": ["Different friend group", "Changed house dynamics"]
  }
}
```

**Scenario Types**:

- `CHARACTER_CHANGE`: Alter character properties
- `EVENT_ALTERATION`: Change key events
- `SETTING_MODIFICATION`: Modify settings/world

**JSONB Parameters** (flexible schema per type):

**CHARACTER_CHANGE**:

```json
{
  "character": "string",
  "property": "house|personality|skill|backstory",
  "original_value": "string",
  "new_value": "string",
  "change_point": "string",
  "ripple_effects": ["string"]
}
```

**EVENT_ALTERATION**:

```json
{
  "event": "string",
  "timeline_point": "string",
  "alteration_type": "prevent|accelerate|relocate|outcome_change",
  "original_outcome": "string",
  "new_outcome": "string",
  "affected_characters": ["string"]
}
```

**SETTING_MODIFICATION**:

```json
{
  "setting_element": "location|era|magic_system|technology",
  "scope": "global|regional|local",
  "change_description": "string",
  "impact_level": "minor|moderate|major"
}
```

#### Response (201 Created)

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "base_story": "harry_potter",
  "scenario_type": "CHARACTER_CHANGE",
  "parameters": {
    "character": "Hermione Granger",
    "property": "house",
    "original_value": "Gryffindor",
    "new_value": "Slytherin",
    "change_point": "Sorting Hat ceremony",
    "ripple_effects": ["Different friend group", "Changed house dynamics"]
  },
  "quality_score": 0.0,
  "creator_id": "550e8400-e29b-41d4-a716-446655440000",
  "fork_count": 0,
  "conversation_count": 0,
  "created_at": "2025-11-13T10:30:00Z",
  "updated_at": "2025-11-13T10:30:00Z"
}
```

#### Errors

- `400 Bad Request`: Invalid parameters or scenario type
- `401 Unauthorized`: Missing or invalid token
- `422 Unprocessable Entity`: JSONB schema validation failed

---

### Get Scenario

Retrieve single scenario by ID.

**Endpoint**: `GET /api/scenarios/{id}`  
**Authentication**: None (Public)  
**Performance**: < 100ms

#### Response (200 OK)

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "base_story": "harry_potter",
  "parent_scenario_id": null,
  "scenario_type": "CHARACTER_CHANGE",
  "parameters": {
    "character": "Hermione Granger",
    "property": "house",
    "new_value": "Slytherin"
  },
  "quality_score": 0.85,
  "creator": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "hermione_fan",
    "avatar_url": "https://example.com/avatar.jpg"
  },
  "fork_count": 12,
  "conversation_count": 45,
  "created_at": "2025-11-13T10:30:00Z",
  "updated_at": "2025-11-13T11:00:00Z"
}
```

#### Errors

- `404 Not Found`: Scenario does not exist or is deleted

---

### List Scenarios

List scenarios with pagination and optional filtering.

**Endpoint**: `GET /api/scenarios`  
**Authentication**: None (Public)  
**Performance**: < 200ms (with 1000 scenarios)

#### Query Parameters

| Parameter       | Type    | Default           | Description                 |
| --------------- | ------- | ----------------- | --------------------------- |
| `page`          | integer | 0                 | Page number (0-indexed)     |
| `size`          | integer | 20                | Items per page (max 100)    |
| `base_story`    | string  | -                 | Filter by base story        |
| `scenario_type` | string  | -                 | Filter by type              |
| `min_quality`   | decimal | -                 | Min quality score (0.0-1.0) |
| `creator_id`    | UUID    | -                 | Filter by creator           |
| `sort`          | string  | `created_at,desc` | Sort field and direction    |

#### Example Request

```bash
GET /api/scenarios?base_story=harry_potter&scenario_type=CHARACTER_CHANGE&min_quality=0.7&page=0&size=20&sort=quality_score,desc
```

#### Response (200 OK)

```json
{
  "content": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "base_story": "harry_potter",
      "scenario_type": "CHARACTER_CHANGE",
      "parameters": {
        "character": "Hermione Granger",
        "property": "house",
        "new_value": "Slytherin"
      },
      "quality_score": 0.85,
      "creator": {
        "username": "hermione_fan",
        "avatar_url": "https://example.com/avatar.jpg"
      },
      "fork_count": 12,
      "created_at": "2025-11-13T10:30:00Z"
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 156,
    "total_pages": 8
  }
}
```

---

### Update Scenario

Update existing scenario (creator only).

**Endpoint**: `PUT /api/scenarios/{id}`  
**Authentication**: Required (Creator only)  
**Performance**: < 150ms

#### Request

```json
{
  "parameters": {
    "character": "Hermione Granger",
    "property": "house",
    "original_value": "Gryffindor",
    "new_value": "Slytherin",
    "change_point": "Sorting Hat ceremony",
    "ripple_effects": [
      "Different friend group",
      "Changed house dynamics",
      "Academic rivalry with Draco"
    ]
  }
}
```

**Note**: Only `parameters` field can be updated. `base_story` and `scenario_type` are immutable.

#### Response (200 OK)

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "base_story": "harry_potter",
  "scenario_type": "CHARACTER_CHANGE",
  "parameters": {
    "character": "Hermione Granger",
    "property": "house",
    "new_value": "Slytherin",
    "ripple_effects": [
      "Different friend group",
      "Changed house dynamics",
      "Academic rivalry with Draco"
    ]
  },
  "updated_at": "2025-11-13T12:00:00Z"
}
```

#### Errors

- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not the creator
- `404 Not Found`: Scenario not found

---

### Delete Scenario

Soft delete scenario (creator only).

**Endpoint**: `DELETE /api/scenarios/{id}`  
**Authentication**: Required (Creator only)  
**Performance**: < 100ms

#### Response (204 No Content)

No body returned.

#### Errors

- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not the creator
- `404 Not Found`: Scenario not found

---

### Fork Scenario

Create a meta-scenario (scenario of a scenario).

**Endpoint**: `POST /api/scenarios/{id}/fork`  
**Authentication**: Required  
**Performance**: < 200ms

#### Request

```json
{
  "scenario_type": "EVENT_ALTERATION",
  "parameters": {
    "event": "Hermione befriends Draco in Slytherin common room",
    "timeline_point": "Year 1, October",
    "alteration_type": "outcome_change",
    "original_outcome": "Hermione isolated from Slytherin clique",
    "new_outcome": "Hermione and Draco form unlikely alliance",
    "affected_characters": ["Hermione Granger", "Draco Malfoy"]
  }
}
```

**Fork Logic**:

- Unlimited depth meta-timelines supported
- Parent scenario ID automatically set
- Fork counter incremented on parent
- Circular references prevented by trigger

#### Response (201 Created)

```json
{
  "id": "9f8e7d6c-5b4a-3210-9876-fedcba098765",
  "base_story": "harry_potter",
  "parent_scenario_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "scenario_type": "EVENT_ALTERATION",
  "parameters": {
    "event": "Hermione befriends Draco in Slytherin common room",
    "timeline_point": "Year 1, October",
    "new_outcome": "Hermione and Draco form unlikely alliance"
  },
  "quality_score": 0.0,
  "creator_id": "550e8400-e29b-41d4-a716-446655440000",
  "fork_count": 0,
  "created_at": "2025-11-13T13:00:00Z"
}
```

#### Errors

- `400 Bad Request`: Circular reference detected
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Parent scenario not found

---

## Conversations

### Create Conversation

Start a new conversation based on a scenario.

**Endpoint**: `POST /api/conversations`  
**Authentication**: Required  
**Performance**: < 150ms

#### Request

```json
{
  "scenario_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "title": "Hermione's First Day in Slytherin"
}
```

#### Response (201 Created)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "parent_conversation_id": null,
  "scenario_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Hermione's First Day in Slytherin",
  "like_count": 0,
  "created_at": "2025-11-13T14:00:00Z",
  "updated_at": "2025-11-13T14:00:00Z"
}
```

#### Errors

- `400 Bad Request`: Missing scenario_id
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Scenario not found

---

### Get Conversation

Retrieve conversation with all messages.

**Endpoint**: `GET /api/conversations/{id}`  
**Authentication**: None (Public)  
**Performance**: < 100ms

#### Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "parent_conversation_id": null,
  "scenario": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "base_story": "harry_potter",
    "scenario_type": "CHARACTER_CHANGE",
    "parameters": {
      "character": "Hermione Granger",
      "new_value": "Slytherin"
    }
  },
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "hermione_fan",
    "avatar_url": "https://example.com/avatar.jpg"
  },
  "title": "Hermione's First Day in Slytherin",
  "like_count": 23,
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "How would Hermione react to being sorted into Slytherin?",
      "created_at": "2025-11-13T14:01:00Z"
    },
    {
      "id": "msg-002",
      "role": "assistant",
      "content": "Hermione would initially feel shocked and conflicted...",
      "created_at": "2025-11-13T14:01:15Z"
    }
  ],
  "created_at": "2025-11-13T14:00:00Z",
  "updated_at": "2025-11-13T14:05:00Z"
}
```

---

### List Conversations

List user's conversations or public conversations.

**Endpoint**: `GET /api/conversations`  
**Authentication**: Optional (Required for personal conversations)  
**Performance**: < 200ms

#### Query Parameters

| Parameter     | Type    | Default           | Description                                |
| ------------- | ------- | ----------------- | ------------------------------------------ |
| `page`        | integer | 0                 | Page number                                |
| `size`        | integer | 20                | Items per page (max 100)                   |
| `user_id`     | UUID    | -                 | Filter by user (requires auth if not self) |
| `scenario_id` | UUID    | -                 | Filter by scenario                         |
| `sort`        | string  | `updated_at,desc` | Sort field and direction                   |

#### Response (200 OK)

```json
{
  "content": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Hermione's First Day in Slytherin",
      "scenario": {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "base_story": "harry_potter"
      },
      "user": {
        "username": "hermione_fan"
      },
      "like_count": 23,
      "message_count": 8,
      "updated_at": "2025-11-13T14:05:00Z"
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 42,
    "total_pages": 3
  }
}
```

---

### Update Conversation

Update conversation title.

**Endpoint**: `PUT /api/conversations/{id}`  
**Authentication**: Required (Owner only)  
**Performance**: < 100ms

#### Request

```json
{
  "title": "Hermione's Slytherin Journey - Chapter 1"
}
```

#### Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Hermione's Slytherin Journey - Chapter 1",
  "updated_at": "2025-11-13T15:00:00Z"
}
```

#### Errors

- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not the owner
- `404 Not Found`: Conversation not found

---

### Delete Conversation

Delete conversation and all messages.

**Endpoint**: `DELETE /api/conversations/{id}`  
**Authentication**: Required (Owner only)  
**Performance**: < 150ms

#### Response (204 No Content)

No body returned.

**Note**: Cascading delete removes all `conversation_message_links` and orphaned messages.

#### Errors

- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not the owner
- `404 Not Found`: Conversation not found

---

### Send Message

Send message and receive AI-generated response asynchronously.

**Endpoint**: `POST /api/conversations/{id}/messages`  
**Authentication**: Required (Owner only)  
**Performance**: Async (returns 202 immediately, response via SSE)

#### Request

```json
{
  "content": "What happens when Hermione meets Draco in the Slytherin common room?"
}
```

#### Response (202 Accepted)

```json
{
  "message_id": "msg-003",
  "stream_url": "/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890/stream"
}
```

**SSE Stream** (at `stream_url`):

```
event: message_chunk
data: {"content": "Hermione enters", "delta": "Hermione enters"}

event: message_chunk
data: {"content": "Hermione enters the Slytherin", "delta": " the Slytherin"}

event: message_complete
data: {"message_id": "msg-004", "role": "assistant", "content": "Full response..."}
```

#### Errors

- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not the owner
- `404 Not Found`: Conversation not found
- `429 Too Many Requests`: Rate limit (10 messages per minute)

---

### Fork Conversation

Create a forked conversation from existing one (ROOT conversations only).

**Endpoint**: `POST /api/conversations/{id}/fork`  
**Authentication**: Required  
**Performance**: < 200ms

**Fork Rules**:

- Only ROOT conversations can be forked (`parent_conversation_id IS NULL`)
- Creates a new conversation with max depth = 1
- Automatically copies `min(6, total_message_count)` most recent messages
- Fork cannot be forked again

#### Request

```json
{
  "title": "Alternative: Hermione Befriends Draco"
}
```

#### Response (201 Created)

```json
{
  "id": "fork-b2c3d4e5-f6a7-8901-bcde-f23456789012",
  "parent_conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "scenario_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Alternative: Hermione Befriends Draco",
  "messages": [
    {
      "id": "msg-005",
      "role": "user",
      "content": "How would Hermione react to being sorted into Slytherin?",
      "created_at": "2025-11-13T16:00:00Z"
    },
    {
      "id": "msg-006",
      "role": "assistant",
      "content": "Hermione would initially feel shocked...",
      "created_at": "2025-11-13T16:00:15Z"
    }
  ],
  "like_count": 0,
  "created_at": "2025-11-13T16:00:00Z"
}
```

**Message Copy Logic**:

```
copied_count = min(6, parent_total_message_count)
messages = SELECT * FROM messages
           WHERE conversation_id = parent_id
           ORDER BY created_at DESC
           LIMIT copied_count
```

#### Errors

- `400 Bad Request`: Conversation is already a fork (max depth = 1)
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Parent conversation not found

---

## Users

### Get User Profile

Retrieve public user profile.

**Endpoint**: `GET /api/users/{username}`  
**Authentication**: None (Public)  
**Performance**: < 100ms

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "hermione_fan",
  "bio": "Slytherin Hermione enthusiast. What if scenarios are my passion.",
  "avatar_url": "https://example.com/avatar.jpg",
  "follower_count": 234,
  "following_count": 89,
  "scenario_count": 12,
  "conversation_count": 45,
  "joined_at": "2025-10-01T08:00:00Z"
}
```

#### Errors

- `404 Not Found`: User does not exist

---

### Update Profile

Update own user profile.

**Endpoint**: `PUT /api/users/profile`  
**Authentication**: Required  
**Performance**: < 150ms

#### Request

```json
{
  "bio": "Updated bio: Exploring alternate timelines in Harry Potter universe",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

**Note**: Email and username cannot be changed via this endpoint.

#### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "hermione_fan",
  "email": "user@example.com",
  "bio": "Updated bio: Exploring alternate timelines in Harry Potter universe",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "updated_at": "2025-11-13T17:00:00Z"
}
```

#### Errors

- `401 Unauthorized`: Not authenticated
- `400 Bad Request`: Validation failed (bio > 500 chars)

---

### Upload Avatar

Upload user avatar image.

**Endpoint**: `POST /api/users/profile/avatar`  
**Authentication**: Required  
**Performance**: < 500ms  
**Content-Type**: `multipart/form-data`

#### Request

```
Content-Type: multipart/form-data
------WebKitFormBoundary
Content-Disposition: form-data; name="avatar"; filename="avatar.jpg"
Content-Type: image/jpeg

[binary image data]
------WebKitFormBoundary--
```

**File Constraints**:

- Max size: 5 MB
- Allowed formats: JPG, PNG, GIF, WEBP
- Auto-resize to 400x400 px

#### Response (200 OK)

```json
{
  "avatar_url": "https://cdn.example.com/avatars/550e8400-e29b-41d4-a716-446655440000.jpg",
  "uploaded_at": "2025-11-13T17:30:00Z"
}
```

#### Errors

- `400 Bad Request`: File too large or invalid format
- `401 Unauthorized`: Not authenticated
- `413 Payload Too Large`: File > 5 MB

---

## Social Features

### Follow User

Follow another user.

**Endpoint**: `POST /api/users/{id}/follow`  
**Authentication**: Required  
**Performance**: < 100ms  
**Idempotent**: Yes (no error if already following)

#### Response (200 OK)

```json
{
  "follower_id": "550e8400-e29b-41d4-a716-446655440000",
  "following_id": "661e9511-f30c-52e5-b827-557766551111",
  "created_at": "2025-11-13T18:00:00Z",
  "is_mutual": false
}
```

#### Errors

- `400 Bad Request`: Cannot follow yourself
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User not found

---

### Unfollow User

Unfollow a user.

**Endpoint**: `DELETE /api/users/{id}/unfollow`  
**Authentication**: Required  
**Performance**: < 100ms  
**Idempotent**: Yes (no error if not following)

#### Response (200 OK)

```json
{
  "message": "Unfollowed successfully"
}
```

#### Errors

- `401 Unauthorized`: Not authenticated
- `404 Not Found`: User not found

---

### Get Followers

Get user's followers list.

**Endpoint**: `GET /api/users/{id}/followers`  
**Authentication**: None (Public)  
**Performance**: < 200ms

#### Query Parameters

| Parameter | Type    | Default | Description              |
| --------- | ------- | ------- | ------------------------ |
| `page`    | integer | 0       | Page number              |
| `size`    | integer | 20      | Items per page (max 100) |

#### Response (200 OK)

```json
{
  "content": [
    {
      "id": "follower-001",
      "username": "harry_fan",
      "avatar_url": "https://example.com/avatar1.jpg",
      "is_mutual": true,
      "followed_at": "2025-11-10T10:00:00Z"
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 234,
    "total_pages": 12
  }
}
```

---

### Get Following

Get list of users that a user follows.

**Endpoint**: `GET /api/users/{id}/following`  
**Authentication**: None (Public)  
**Performance**: < 200ms

#### Query Parameters

Same as followers endpoint.

#### Response (200 OK)

```json
{
  "content": [
    {
      "id": "following-001",
      "username": "ron_fan",
      "avatar_url": "https://example.com/avatar2.jpg",
      "is_mutual": false,
      "followed_at": "2025-11-09T15:00:00Z"
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 89,
    "total_pages": 5
  }
}
```

---

### Check Follow Status

Check if authenticated user follows another user.

**Endpoint**: `GET /api/users/{id}/is-following`  
**Authentication**: Required  
**Performance**: < 50ms

#### Response (200 OK)

```json
{
  "is_following": true,
  "is_mutual": true,
  "followed_at": "2025-11-10T10:00:00Z"
}
```

---

### Like Conversation

Like a conversation.

**Endpoint**: `POST /api/conversations/{id}/like`  
**Authentication**: Required  
**Performance**: < 100ms  
**Idempotent**: Yes (no error if already liked)

#### Response (200 OK)

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "liked_at": "2025-11-13T19:00:00Z",
  "total_likes": 24
}
```

**Note**: Trigger automatically increments `conversations.like_count`.

#### Errors

- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Conversation not found

---

### Unlike Conversation

Remove like from conversation.

**Endpoint**: `DELETE /api/conversations/{id}/unlike`  
**Authentication**: Required  
**Performance**: < 100ms  
**Idempotent**: Yes (no error if not liked)

#### Response (200 OK)

```json
{
  "message": "Unliked successfully",
  "total_likes": 23
}
```

**Note**: Trigger automatically decrements `conversations.like_count`.

---

### Check If Liked

Check if authenticated user liked a conversation.

**Endpoint**: `GET /api/conversations/{id}/liked`  
**Authentication**: Required  
**Performance**: < 50ms

#### Response (200 OK)

```json
{
  "is_liked": true,
  "liked_at": "2025-11-13T19:00:00Z"
}
```

---

### Get Liked Conversations

Get conversations liked by authenticated user.

**Endpoint**: `GET /api/users/me/liked-conversations`  
**Authentication**: Required  
**Performance**: < 200ms

#### Query Parameters

| Parameter | Type    | Default | Description              |
| --------- | ------- | ------- | ------------------------ |
| `page`    | integer | 0       | Page number              |
| `size`    | integer | 20      | Items per page (max 100) |

#### Response (200 OK)

```json
{
  "content": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "Hermione's First Day in Slytherin",
      "scenario": {
        "base_story": "harry_potter"
      },
      "user": {
        "username": "hermione_fan"
      },
      "like_count": 24,
      "liked_at": "2025-11-13T19:00:00Z"
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 78,
    "total_pages": 4
  }
}
```

---

### Get Conversation Memo

Retrieve personal memo for a conversation.

**Endpoint**: `GET /api/conversations/{id}/memo`  
**Authentication**: Required  
**Performance**: < 50ms

#### Response (200 OK)

```json
{
  "memo_text": "Interesting exploration of Hermione's adaptability. Should explore Draco relationship more.",
  "created_at": "2025-11-13T20:00:00Z",
  "updated_at": "2025-11-13T20:15:00Z"
}
```

#### Response (404 Not Found) - No Memo

```json
{
  "message": "No memo found for this conversation"
}
```

---

### Save Conversation Memo

Create or update personal memo.

**Endpoint**: `POST /api/conversations/{id}/memo`  
**Authentication**: Required  
**Performance**: < 100ms

#### Request

```json
{
  "memo_text": "Updated memo: Focus on house dynamics in next conversation fork."
}
```

**Constraints**:

- Max length: 1000 characters
- Markdown supported

#### Response (200 OK)

```json
{
  "memo_text": "Updated memo: Focus on house dynamics in next conversation fork.",
  "created_at": "2025-11-13T20:00:00Z",
  "updated_at": "2025-11-13T20:30:00Z"
}
```

#### Errors

- `400 Bad Request`: Memo > 1000 characters
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Conversation not found

---

### Delete Conversation Memo

Delete personal memo.

**Endpoint**: `DELETE /api/conversations/{id}/memo`  
**Authentication**: Required  
**Performance**: < 50ms

#### Response (204 No Content)

No body returned.

#### Errors

- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Conversation or memo not found

---

## FastAPI APIs (VectorDB)

> **Database Access**: VectorDB (ChromaDB) ONLY. For PostgreSQL queries, FastAPI calls Spring Boot `/api/internal/*`.

### Novel Ingestion (FastAPI)

#### Ingest Novel from Gutenberg Dataset

Batch import novel from Project Gutenberg dataset (not real-time API).

**Endpoint**: `POST /api/ai/novels/ingest`  
**Service**: FastAPI (Port 8000)  
**Authentication**: Admin only  
**Performance**: Async (returns job ID immediately)

**Request**:

```json
{
  "novel_file_path": "/data/gutenberg/pg1234.txt",
  "metadata": {
    "title": "Pride and Prejudice",
    "author": "Jane Austen",
    "publication_year": 1813,
    "genre": "Romance"
  }
}
```

**Response (202 Accepted)**:

```json
{
  "job_id": "ingest-550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "estimated_duration_minutes": 15,
  "message": "Novel ingestion started. Check status at /api/ai/novels/status/{job_id}"
}
```

**What Happens Internally**:

```python
# FastAPI ai-backend/app/services/novel_ingestion.py
async def ingest_novel(file_path: str, metadata: dict):
    # 1. Parse Gutenberg file
    text = parse_gutenberg_file(file_path)

    # 2. Save metadata to PostgreSQL via Spring Boot
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://spring-boot:8080/api/internal/novels",
            json=metadata
        )
        novel_id = UUID(response.json()["id"])

    # 3. Chunk text (200-500 words per passage)
    passages = chunk_text(text, chunk_size=300)

    # 4. Generate embeddings via Gemini Embedding API
    embeddings = await generate_embeddings(passages)  # 768 dims

    # 5. Store in VectorDB (FastAPI only)
    chroma = chromadb.PersistentClient(path="./chroma_data")
    passages_collection = chroma.get_collection("novel_passages")
    passages_collection.add(
        ids=[f"{novel_id}-{i}" for i in range(len(passages))],
        embeddings=embeddings,
        documents=passages,
        metadatas=[{"novel_id": str(novel_id), "chunk_index": i} for i in range(len(passages))]
    )

    # 6. Extract characters via Gemini 2.5 Flash
    characters = await extract_characters_with_llm(text)
    characters_collection = chroma.get_collection("characters")
    # ... store in VectorDB

    # 7. Update PostgreSQL status via Spring Boot
    await client.patch(
        f"http://spring-boot:8080/api/internal/novels/{novel_id}",
        json={"ingestion_status": "completed"}
    )
```

---

#### Check Ingestion Status

**Endpoint**: `GET /api/ai/novels/status/{job_id}`  
**Service**: FastAPI  
**Authentication**: Required  
**Performance**: < 50ms

**Response (200 OK)**:

```json
{
  "job_id": "ingest-550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "novel_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "progress": {
    "passages_processed": 1200,
    "characters_extracted": 45,
    "locations_extracted": 12,
    "events_extracted": 67
  },
  "completed_at": "2025-11-13T11:00:00Z"
}
```

**Status Values**: `pending`, `processing`, `completed`, `failed`

---

### Semantic Search (FastAPI)

#### Search Similar Passages

Semantic search for novel passages using VectorDB cosine similarity.

**Endpoint**: `POST /api/ai/search/passages`  
**Service**: FastAPI (Port 8000)  
**Authentication**: Required  
**Performance**: < 300ms

**Request**:

```json
{
  "query": "Hermione's bravery and intelligence",
  "novel_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "top_k": 10,
  "filters": {
    "min_similarity": 0.7
  }
}
```

**Response (200 OK)**:

```json
{
  "passages": [
    {
      "id": "7c9e6679-0-145",
      "text": "Hermione raised her hand before Harry could finish...",
      "similarity_score": 0.89,
      "chunk_index": 145,
      "metadata": {
        "novel_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "novel_title": "Harry Potter and the Philosopher's Stone"
      }
    }
  ],
  "total_results": 10,
  "query_embedding_time_ms": 45,
  "search_time_ms": 102
}
```

**How Spring Boot Uses This**:

```java
// Spring Boot core-backend/src/main/java/service/ScenarioService.java
@Service
public class ScenarioService {
    @Autowired
    private WebClient aiServiceClient;

    public Scenario createScenario(CreateScenarioRequest request) {
        // Spring Boot calls FastAPI for VectorDB query
        PassageSearchResponse passages = aiServiceClient.post()
            .uri("/api/ai/search/passages")
            .bodyValue(Map.of(
                "query", request.getScenarioDescription(),
                "novel_id", request.getNovelId(),
                "top_k", 10
            ))
            .retrieve()
            .bodyToMono(PassageSearchResponse.class)
            .block();

        // Save to PostgreSQL with VectorDB passage IDs
        Scenario scenario = new Scenario();
        scenario.setVectordbPassageIds(passages.getPassageIds());
        return scenarioRepository.save(scenario);  // PostgreSQL
    }
}
```

---

### AI Conversation (FastAPI)

#### Send Message to AI Character

Generate AI response using RAG + Gemini 2.5 Flash.

**Endpoint**: `POST /api/ai/conversations/{conversation_id}/messages`  
**Service**: FastAPI (Port 8000)  
**Authentication**: Required  
**Performance**: < 3s (SSE streaming)

**Request**:

```json
{
  "content": "Hermione, what house would you truly choose?",
  "scenario_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

**Response (Server-Sent Events)**:

```
event: message
data: {"type": "start", "message_id": "msg-123"}

event: message
data: {"type": "token", "content": "You know"}

event: message
data: {"type": "token", "content": ", Harry"}

event: message
data: {"type": "token", "content": ", I've always"}

event: message
data: {"type": "complete", "message_id": "msg-123", "total_tokens": 245}
```

**RAG Pipeline (FastAPI Only)**:

```python
# FastAPI ai-backend/app/services/rag_service.py
class RAGService:
    async def generate_response(self, conversation_id: UUID, user_message: str):
        # 1. Get scenario from Spring Boot (PostgreSQL)
        async with httpx.AsyncClient() as client:
            scenario = await client.get(
                f"http://spring-boot:8080/api/internal/scenarios/{scenario_id}"
            )

        # 2. Search VectorDB for relevant passages (FastAPI only)
        chroma = chromadb.PersistentClient(path="./chroma_data")
        passages = chroma.get_collection("novel_passages")
        results = passages.query(
            query_texts=[user_message],
            where={"novel_id": scenario["novel_id"]},
            n_results=20
        )

        # 3. Get character from VectorDB (FastAPI only)
        characters = chroma.get_collection("characters")
        character = characters.get(ids=[scenario["character_vectordb_id"]])

        # 4. Build prompt with RAG context
        prompt = f"""
        Character: {character["name"]}
        Personality: {character["personality"]}
        Scenario: {scenario["description"]}

        Relevant passages:
        {results["documents"]}

        User: {user_message}
        Assistant:
        """

        # 5. Call Gemini 2.5 Flash
        async for token in gemini_client.generate_stream(prompt):
            yield token

        # 6. Save message to PostgreSQL via Spring Boot
        await client.post(
            f"http://spring-boot:8080/api/internal/conversations/{conversation_id}/messages",
            json={"role": "assistant", "content": full_response}
        )
```

---

### Character Extraction (FastAPI)

#### Extract Characters from Novel

Use Gemini 2.5 Flash to extract character entities and traits.

**Endpoint**: `POST /api/ai/characters/extract`  
**Service**: FastAPI  
**Authentication**: Admin only  
**Performance**: Async (10-30 minutes for full novel)

**Request**:

```json
{
  "novel_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "extraction_mode": "full"
}
```

**Response (202 Accepted)**:

```json
{
  "job_id": "extract-chars-550e8400",
  "status": "processing",
  "estimated_duration_minutes": 20
}
```

**Extracted Data Stored in VectorDB**:

```python
# FastAPI stores in VectorDB characters collection
characters_collection.add(
    ids=["char-hermione-granger"],
    metadatas=[{
        "name": "Hermione Granger",
        "novel_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "role": "main",
        "personality_traits": ["intelligent", "brave", "perfectionist"],
        "first_appearance_chapter": 6
    }],
    documents=["Hermione Granger is a muggle-born witch..."]
)
```

---

## Internal APIs

### Internal API - Spring Boot

> **Purpose**: Allow FastAPI to query PostgreSQL metadata without direct DB access.  
> **Base URL**: `http://spring-boot:8080/api/internal/*`  
> **Authentication**: Internal service token (not exposed to frontend)

#### Get Novel Metadata

**Endpoint**: `GET /api/internal/novels/{novel_id}`  
**Caller**: FastAPI  
**Performance**: < 50ms

**Response (200 OK)**:

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "title": "Harry Potter and the Philosopher's Stone",
  "author": "J.K. Rowling",
  "publication_year": 1997,
  "ingestion_status": "completed",
  "vectordb_collection_id": "novel_passages"
}
```

---

#### Create Novel Metadata

**Endpoint**: `POST /api/internal/novels`  
**Caller**: FastAPI (during ingestion)  
**Performance**: < 100ms

**Request**:

```json
{
  "title": "Pride and Prejudice",
  "author": "Jane Austen",
  "publication_year": 1813,
  "genre": "Romance",
  "ingestion_status": "processing"
}
```

**Response (201 Created)**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Pride and Prejudice",
  "created_at": "2025-11-13T10:00:00Z"
}
```

---

#### Update Novel Status

**Endpoint**: `PATCH /api/internal/novels/{novel_id}`  
**Caller**: FastAPI (after ingestion complete)  
**Performance**: < 50ms

**Request**:

```json
{
  "ingestion_status": "completed",
  "total_passages": 1200,
  "total_characters": 45
}
```

---

### Internal API - FastAPI

> **Purpose**: Allow Spring Boot to query VectorDB without direct DB access.  
> **Base URL**: `http://fastapi:8000/api/ai/*`  
> **Authentication**: Internal service token (not exposed to frontend)

#### Search Passages (Internal)

**Endpoint**: `POST /api/ai/search/passages`  
**Caller**: Spring Boot (for scenario creation, conversation context)  
**Performance**: < 300ms

(Same as public `/api/ai/search/passages` but with internal auth token)

---

#### Get Character by VectorDB ID

**Endpoint**: `GET /api/ai/characters/{vectordb_id}`  
**Caller**: Spring Boot (for conversation setup)  
**Performance**: < 100ms

**Response (200 OK)**:

```json
{
  "id": "char-hermione-granger",
  "name": "Hermione Granger",
  "description": "Muggle-born witch, Gryffindor student...",
  "personality_traits": ["intelligent", "brave", "perfectionist"],
  "novel_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"
}
```

---

## Search & Discovery

### Browse Scenarios

Browse scenarios with advanced filtering.

**Endpoint**: `GET /api/scenarios/search`  
**Authentication**: None (Public)  
**Performance**: < 200ms

**Note**: This endpoint combines filtering and full-text search capabilities.

#### Query Parameters

| Parameter       | Type    | Default          | Description                                                   |
| --------------- | ------- | ---------------- | ------------------------------------------------------------- |
| `q`             | string  | -                | Full-text search query (pg_trgm)                              |
| `base_story`    | string  | -                | Filter by base story                                          |
| `scenario_type` | string  | -                | Filter by type                                                |
| `min_quality`   | decimal | -                | Min quality score (0.0-1.0)                                   |
| `creator_id`    | UUID    | -                | Filter by creator                                             |
| `has_forks`     | boolean | -                | Filter by fork status                                         |
| `page`          | integer | 0                | Page number                                                   |
| `size`          | integer | 20               | Items per page (max 100)                                      |
| `sort`          | string  | `relevance,desc` | Sort field (relevance, quality_score, created_at, fork_count) |

#### Example Request

```bash
GET /api/scenarios/search?q=hermione+slytherin&base_story=harry_potter&min_quality=0.7&sort=quality_score,desc
```

#### Response (200 OK)

```json
{
  "content": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "base_story": "harry_potter",
      "scenario_type": "CHARACTER_CHANGE",
      "parameters": {
        "character": "Hermione Granger",
        "new_value": "Slytherin"
      },
      "quality_score": 0.85,
      "fork_count": 12,
      "relevance_score": 0.92,
      "creator": {
        "username": "hermione_fan"
      }
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 23,
    "total_pages": 2
  },
  "facets": {
    "scenario_types": {
      "CHARACTER_CHANGE": 15,
      "EVENT_ALTERATION": 6,
      "SETTING_MODIFICATION": 2
    },
    "quality_ranges": {
      "0.8-1.0": 12,
      "0.6-0.8": 8,
      "0.4-0.6": 3
    }
  }
}
```

---

### Get Scenario Forks

Get direct children of a scenario.

**Endpoint**: `GET /api/scenarios/{id}/forks`  
**Authentication**: None (Public)  
**Performance**: < 150ms

#### Query Parameters

| Parameter | Type    | Default | Description              |
| --------- | ------- | ------- | ------------------------ |
| `page`    | integer | 0       | Page number              |
| `size`    | integer | 20      | Items per page (max 100) |

#### Response (200 OK)

```json
{
  "parent": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "base_story": "harry_potter",
    "scenario_type": "CHARACTER_CHANGE"
  },
  "forks": [
    {
      "id": "9f8e7d6c-5b4a-3210-9876-fedcba098765",
      "scenario_type": "EVENT_ALTERATION",
      "parameters": {
        "event": "Hermione befriends Draco"
      },
      "fork_count": 3,
      "created_at": "2025-11-13T13:00:00Z"
    }
  ],
  "page": {
    "number": 0,
    "size": 20,
    "total_elements": 12,
    "total_pages": 1
  }
}
```

---

### Get Scenario Fork Tree

Get full recursive tree structure.

**Endpoint**: `GET /api/scenarios/{id}/fork-tree`  
**Authentication**: None (Public)  
**Performance**: < 300ms (depth < 5), < 500ms (depth >= 5)

#### Query Parameters

| Parameter   | Type    | Default | Description         |
| ----------- | ------- | ------- | ------------------- |
| `max_depth` | integer | 10      | Max recursion depth |

#### Response (200 OK)

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "base_story": "harry_potter",
  "scenario_type": "CHARACTER_CHANGE",
  "parameters": {
    "character": "Hermione Granger",
    "new_value": "Slytherin"
  },
  "fork_count": 12,
  "children": [
    {
      "id": "9f8e7d6c-5b4a-3210-9876-fedcba098765",
      "scenario_type": "EVENT_ALTERATION",
      "parameters": {
        "event": "Hermione befriends Draco"
      },
      "fork_count": 3,
      "children": [
        {
          "id": "child-level-2",
          "scenario_type": "SETTING_MODIFICATION",
          "parameters": {
            "setting_element": "Slytherin common room dynamics"
          },
          "fork_count": 0,
          "children": []
        }
      ]
    }
  ],
  "depth": 3,
  "total_descendants": 15
}
```

**Note**: Uses PostgreSQL recursive CTE for efficient tree traversal.

---

## Tree Visualization

### Get Conversation Tree

Get nested conversation tree structure.

**Endpoint**: `GET /api/conversations/{id}/tree`  
**Authentication**: None (Public)  
**Performance**: < 150ms

**Note**: Conversations have max fork depth = 1, so tree is shallow.

#### Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Hermione's First Day in Slytherin",
  "scenario_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user": {
    "username": "hermione_fan"
  },
  "like_count": 24,
  "message_count": 8,
  "children": [
    {
      "id": "fork-b2c3d4e5-f6a7-8901-bcde-f23456789012",
      "title": "Alternative: Hermione Befriends Draco",
      "user": {
        "username": "draco_fan"
      },
      "like_count": 15,
      "message_count": 6,
      "children": []
    },
    {
      "id": "fork-c3d4e5f6-a7b8-9012-cdef-g34567890123",
      "title": "Alternative: Hermione Leads Slytherin Study Group",
      "user": {
        "username": "slytherin_scholar"
      },
      "like_count": 8,
      "message_count": 4,
      "children": []
    }
  ],
  "depth": 1,
  "total_descendants": 2
}
```

#### Errors

- `404 Not Found`: Conversation not found

---

## Error Handling

### Standard Error Response

All errors follow this structure:

```json
{
  "timestamp": "2025-11-13T20:00:00Z",
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed for field 'email': must be a valid email address",
  "path": "/api/auth/register",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### HTTP Status Codes

| Code | Meaning               | Usage                                    |
| ---- | --------------------- | ---------------------------------------- |
| 200  | OK                    | Successful GET, PUT, DELETE              |
| 201  | Created               | Successful POST (resource created)       |
| 202  | Accepted              | Async processing initiated               |
| 204  | No Content            | Successful DELETE (no body)              |
| 400  | Bad Request           | Validation error, malformed request      |
| 401  | Unauthorized          | Missing or invalid authentication        |
| 403  | Forbidden             | Authenticated but not authorized         |
| 404  | Not Found             | Resource does not exist                  |
| 409  | Conflict              | Duplicate resource (email, username)     |
| 413  | Payload Too Large     | File upload > max size                   |
| 422  | Unprocessable Entity  | Semantic validation error (JSONB schema) |
| 429  | Too Many Requests     | Rate limit exceeded                      |
| 500  | Internal Server Error | Server error                             |
| 503  | Service Unavailable   | Maintenance or overload                  |

### Rate Limiting

| Endpoint                           | Limit        | Window     |
| ---------------------------------- | ------------ | ---------- |
| `/api/auth/login`                  | 5 requests   | 15 minutes |
| `/api/auth/register`               | 3 requests   | 1 hour     |
| `/api/conversations/{id}/messages` | 10 requests  | 1 minute   |
| All other POST/PUT/DELETE          | 100 requests | 1 minute   |
| All GET                            | 300 requests | 1 minute   |

**Rate Limit Headers**:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699891200
```

---

## Performance Targets

| Operation                        | Target   | Measured At |
| -------------------------------- | -------- | ----------- |
| Single entity retrieval (by ID)  | < 100ms  | P95         |
| List queries (20 items)          | < 200ms  | P95         |
| Full-text search                 | < 300ms  | P95         |
| Recursive tree queries (depth 5) | < 500ms  | P95         |
| Create/Update operations         | < 200ms  | P95         |
| Message streaming (first chunk)  | < 1000ms | P95         |
| File upload (avatar)             | < 500ms  | P95         |

**Performance Optimizations**:

- GIN index on JSONB columns
- B-tree indexes on foreign keys and frequently filtered columns
- Trigram indexes for full-text search (`pg_trgm`)
- Recursive CTE for tree queries
- Database connection pooling (HikariCP)
- Redis caching for frequently accessed data (future)

---

## Code Examples

### JavaScript/TypeScript (Frontend)

#### Authentication

```typescript
// Register
const register = async (email: string, username: string, password: string) => {
  const response = await fetch("http://localhost:8080/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });

  if (!response.ok) {
    throw new Error(`Registration failed: ${response.statusText}`);
  }

  const data = await response.json();
  localStorage.setItem("access_token", data.tokens.access_token);
  localStorage.setItem("refresh_token", data.tokens.refresh_token);
  return data.user;
};

// Login
const login = async (email: string, password: string) => {
  const response = await fetch("http://localhost:8080/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  localStorage.setItem("access_token", data.tokens.access_token);
  localStorage.setItem("refresh_token", data.tokens.refresh_token);
  return data.user;
};

// Authenticated Request Helper
const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem("access_token");

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (response.status === 401) {
    // Token expired, refresh
    await refreshToken();
    // Retry request
    return authFetch(url, options);
  }

  return response;
};

// Refresh Token
const refreshToken = async () => {
  const refresh_token = localStorage.getItem("refresh_token");

  const response = await fetch("http://localhost:8080/api/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token }),
  });

  const data = await response.json();
  localStorage.setItem("access_token", data.access_token);
};
```

#### Create Scenario

```typescript
const createScenario = async (scenarioData: {
  base_story: string;
  scenario_type: string;
  parameters: object;
}) => {
  const response = await authFetch("http://localhost:8080/api/scenarios", {
    method: "POST",
    body: JSON.stringify(scenarioData),
  });

  if (!response.ok) {
    throw new Error("Failed to create scenario");
  }

  return await response.json();
};

// Usage
const scenario = await createScenario({
  base_story: "harry_potter",
  scenario_type: "CHARACTER_CHANGE",
  parameters: {
    character: "Hermione Granger",
    property: "house",
    original_value: "Gryffindor",
    new_value: "Slytherin",
  },
});
```

#### Message Streaming (SSE)

```typescript
const streamMessage = async (conversationId: string, content: string) => {
  // Send message
  const response = await authFetch(
    `http://localhost:8080/api/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ content }),
    }
  );

  const { stream_url } = await response.json();

  // Connect to SSE stream
  const eventSource = new EventSource(`http://localhost:8080${stream_url}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
    },
  });

  eventSource.addEventListener("message_chunk", (event) => {
    const data = JSON.parse(event.data);
    console.log("Chunk:", data.delta);
    // Update UI with delta
  });

  eventSource.addEventListener("message_complete", (event) => {
    const data = JSON.parse(event.data);
    console.log("Complete message:", data.content);
    eventSource.close();
  });

  eventSource.onerror = (error) => {
    console.error("SSE error:", error);
    eventSource.close();
  };
};
```

### cURL Examples

#### Create Scenario

```bash
curl -X POST http://localhost:8080/api/scenarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "base_story": "harry_potter",
    "scenario_type": "CHARACTER_CHANGE",
    "parameters": {
      "character": "Hermione Granger",
      "property": "house",
      "new_value": "Slytherin"
    }
  }'
```

#### Search Scenarios

```bash
curl -X GET "http://localhost:8080/api/scenarios/search?q=hermione+slytherin&min_quality=0.7&sort=quality_score,desc"
```

#### Fork Conversation

```bash
curl -X POST http://localhost:8080/api/conversations/a1b2c3d4-e5f6-7890-abcd-ef1234567890/fork \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Alternative: Hermione Befriends Draco"
  }'
```

#### Upload Avatar

```bash
curl -X POST http://localhost:8080/api/users/profile/avatar \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "avatar=@/path/to/avatar.jpg"
```

---

## Versioning

**Current Version**: v1  
**Versioning Strategy**: URL-based (e.g., `/api/v1/scenarios`, `/api/v2/scenarios`)

**Backward Compatibility**:

- Minor changes: Additive only (new fields, new endpoints)
- Breaking changes: New major version with 6-month deprecation period

**Deprecation Notice Example**:

```
X-API-Deprecated: true
X-API-Sunset: 2026-05-13T00:00:00Z
X-API-Migration: https://docs.gaji.com/api/v2-migration
```

---

## Support & Resources

- **OpenAPI Spec**: `/api/v1/openapi.json`
- **Swagger UI**: `http://localhost:8080/swagger-ui.html`
- **Architecture**: `/docs/architecture.md`
- **ERD**: `/docs/ERD.md`
- **Story Files**: `/docs/stories/`
- **Issues**: GitHub Issues
- **Questions**: Team Slack #gaji-api

---

**Last Updated**: 2025-11-13  
**Maintained By**: Gaji Engineering Team
