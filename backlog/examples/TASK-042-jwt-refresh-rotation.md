---
id: TASK-042
status: todo
priority: high
depends_on: [TASK-038, TASK-039]
tags: [auth, api, security]
assigned_role: executor
requires_approval: false
estimated_complexity: medium
---

# Implement JWT refresh token rotation

## Objective
Implement automatic refresh token rotation for the auth module.
When a refresh token is used, issue a new refresh token and invalidate the old one.
No changes to access token logic.

### Not Included
- Access token format changes
- Database schema migration
- Admin panel UI for token management

## Context
Current auth uses static refresh tokens that never expire.
Security audit flagged this as HIGH risk (finding SEC-2026-017).
Existing auth code: `src/auth/jwt.service.ts`, `src/auth/auth.controller.ts`.
Reference implementation: `src/oauth/token-rotation.example.ts` (not in prod).

## Tech Stack & Constraints
- Runtime: Node.js 20 LTS
- Framework: NestJS 10.x
- Validation: Zod 3.23
- Testing: Jest 29.7 + supertest
- Token library: `jsonwebtoken @9.0.2` (do NOT upgrade)

## Input/Output Contracts

```typescript
// Refresh endpoint input
const RefreshInput = z.object({
  refreshToken: z.string().uuid(),
  deviceId: z.string().max(64),
});

// Refresh endpoint output
type RefreshOutput = {
  accessToken: string;   // New access token, 15min TTL
  refreshToken: string;  // NEW refresh token (rotated)
  expiresIn: number;     // Seconds until access token expires
};
```

## Acceptance Criteria

| ID | Input | Expected Behavior | Verification |
|----|-------|-------------------|--------------|
| AC1 | Valid unused refresh token | Returns new access + new refresh; old invalidated | `POST /auth/refresh` → 200 + DB check |
| AC2 | Already-used refresh token | Returns 401; all device tokens revoked | Reuse token → 401 |
| AC3 | Expired refresh token (>30d) | Returns 401; no cascade revocation | exp=2026-01-01 → 401 |
| AC4 | Invalid UUID format | Returns 400 with field error | Zod validation error |
| AC5 | Concurrent refresh (race) | Exactly one succeeds, other 401 | Parallel requests test |

## Boundaries

| Tier | Rules |
|------|-------|
| ✅ Always | Invalidate old token BEFORE issuing new; log rotation events with device_id |
| ⚠️ Ask First | Changing TTL values; adding claims to access token |
| 🚫 Never | Store refresh tokens plaintext; log token values; modify access token structure |

## Test Plan
- Unit: `npm test -- jwt.service.spec.ts -t "refresh rotation"`
- Integration: `npm run test:e2e -- auth-refresh.e2e-spec.ts`
- Self-verify: Run ALL 5 ACs above. Cite specific test names and pass/fail.

### Prohibited Completion Phrases
- "tests should pass"
- "looks correct"
- "follows best practices"
- "implementation seems fine"
