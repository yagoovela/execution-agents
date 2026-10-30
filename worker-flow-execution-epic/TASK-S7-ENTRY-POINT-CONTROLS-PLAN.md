# TASK-S7 — Entry-Point Controls — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the two live unauthenticated spend vectors in S7 Parts 1 + 3 — retire `POST /flux/api-v2-webhook` with `410 Gone`, and gate the email trigger with a per-flow address-token so possession of the trigger address is the credential.

**Architecture:** Two independent changes shipped in the same release. Part 1 is a controller-only delete-and-return-410. Part 3 adds one column (`flows.email_trigger_token`), replaces the address parsing in `MailService`, deletes the forgeable `From`-header check, and adds a rotation endpoint. Frontend and docs updated in the same release.

**Tech Stack:** NestJS + TypeORM + Jest (back), React + Vitest (front), Mintlify (docs).

**Reference spec:** [TASK-S7-ENTRY-POINT-CONTROLS-DESIGN.md](./TASK-S7-ENTRY-POINT-CONTROLS-DESIGN.md).

**User-specific plan conventions:**
- No `git commit` steps in the plan — the user manages git manually after implementation.
- No `pnpm build` / lint / type-check verification steps — the user runs those locally.
- Tests are run with `pnpm test -- --testPathPattern=<file>` on back and `pnpm vitest run --project unit <file>` on front.

---

## File Structure

**Files created:**
- `back/src/utils/generate-email-trigger-token.ts` — token generator + constant-time compare helper.
- `back/src/utils/generate-email-trigger-token.spec.ts` — unit tests for the helper.
- `back/src/database/migrations/1789000000000-AddFlowEmailTriggerToken.ts` — schema + backfill + NOT NULL.
- `back/src/app-api/folw/dto/rotate-email-trigger-token.dto.ts` — response DTO for the rotation endpoint.

**Files modified:**
- `back/src/entities/flow.entity.ts` — add `emailTriggerToken` column.
- `back/src/app-api/folw/flow.service.ts` — inject token generation into `createFlowWithNodesAndEdges`; add `rotateEmailTriggerToken(flowId, userId)` method.
- `back/src/app-api/folw/flow.controller.ts` — add `POST /flow/:id/rotate-email-trigger-token` endpoint.
- `back/src/app-api/mail/mail.service.ts` — replace address parsing + delete `From`-header check.
- `back/src/app-api/mail/mail.service.spec.ts` — new tests for token validation; delete tests for the old `From` check.
- `back/src/app-api/flux/flux.controller.ts` — replace `apiWebhook` body with `410 Gone`.
- `back/src/app-api/flux/flux.controller.api-v2-queue.spec.ts` — delete old-behavior tests, add 410 test.
- `front/` — flow settings page: replace webhook URL card with API guidance; replace email trigger card with token address + rotate button. (Exact file paths located during Task 12.)
- `docs/` — Mintlify: delete `/api-v2-webhook` page; expand `/api-v2` page with callback pattern; rewrite email trigger page. (Exact file paths located during Task 15.)

---

## PART 1 — Retire `/api-v2-webhook`

### Task 1: Add failing test for `410 Gone` on `/api-v2-webhook`

**Files:**
- Modify: `back/src/app-api/flux/flux.controller.api-v2-queue.spec.ts`

- [ ] **Step 1: Read the existing spec file to understand its setup pattern**

Run: view `back/src/app-api/flux/flux.controller.api-v2-queue.spec.ts` end-to-end. Note the mocks, imports, and how `FluxController` is instantiated. The new test must use the same setup so the change plugs cleanly into the file's existing `describe(...)` block.

- [ ] **Step 2: Add a new `describe` block for the retired route**

Append the following at the bottom of the spec file, before its final `});` if any:

```ts
import { HttpStatus } from '@nestjs/common';

describe('FluxController - retired /api-v2-webhook', () => {
  it('returns 410 Gone with a migration message', async () => {
    const controller = new FluxController(
      { enqueueApiV2Job: jest.fn() } as any, // apiV2Queue — not used by the retired handler
    );
    // Manually assign the injected properties the handler references (only loggerService here).
    (controller as any).loggerService = {
      log: jest.fn(),
      error: jest.fn(),
    };

    const res: any = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    const req: any = {
      ip: '1.2.3.4',
      get: jest.fn().mockReturnValue('test-agent/1.0'),
    };

    await controller.apiWebhook(res, req, {}, { flowId: 'any-value' });

    expect(res.status).toHaveBeenCalledWith(HttpStatus.GONE);
    expect(res.json).toHaveBeenCalledWith({
      status: 'error',
      data: {
        message:
          'This endpoint has been retired. Use POST /flux/api-v2 with callback_url and poll GET /flux/executions/:id for status.',
      },
    });
    expect((controller as any).loggerService.log).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Retired route hit: /flux/api-v2-webhook',
      }),
    );
  });
});
```

Import `FluxController` at the top of the file if it isn't already imported. Import `HttpStatus` from `@nestjs/common`.

- [ ] **Step 3: Run the new test — expect it to fail**

Run: `cd back && pnpm test -- --testPathPattern=flux.controller.api-v2-queue.spec.ts`
Expected: the new "returns 410 Gone with a migration message" test FAILS (the current handler returns 200, not 410).

### Task 2: Replace `apiWebhook` handler body with `410 Gone`

**Files:**
- Modify: `back/src/app-api/flux/flux.controller.ts:465-572`

- [ ] **Step 1: Replace the whole `apiWebhook` method**

Delete the current `apiWebhook` decorator block and body (from `@ApiSingleDto({ status: 200, ...` at line 465 through the closing `}` of the method at line 572) and replace with:

```ts
  @ApiSingleDto({
    status: 410,
    description: 'Retired route — use POST /flux/api-v2 with callback_url',
    type: MessageDto,
  })
  @Post('/api-v2-webhook')
  async apiWebhook(
    @Res() res: Response,
    @Req() req: Request,
    @Body() _body: unknown,
    @Query() query: any,
  ) {
    this.loggerService.log({
      message: 'Retired route hit: /flux/api-v2-webhook',
      metadata: {
        other: {
          flowId: query?.flowId,
          ip: req.ip,
          userAgent: req.get('user-agent'),
        },
      },
    });
    return res.status(HttpStatus.GONE).json({
      status: 'error',
      data: {
        message:
          'This endpoint has been retired. Use POST /flux/api-v2 with callback_url and poll GET /flux/executions/:id for status.',
      },
    });
  }
```

Notes:
- The `@Public()` decorator is removed — the handler no longer performs any work that would require bypassing the global auth guard.
- The 6-million-ms `@SetRequestTimeout` decorator is removed — a 410 has no async work.
- The `Body` param is preserved as `unknown` and prefixed with `_` since the retired handler must still accept whatever the client sends.

- [ ] **Step 2: Re-run the spec — expect the new test to pass**

Run: `cd back && pnpm test -- --testPathPattern=flux.controller.api-v2-queue.spec.ts`
Expected: the "returns 410 Gone" test PASSES.

- [ ] **Step 3: Verify the rest of the same spec file still passes**

Some tests in `flux.controller.api-v2-queue.spec.ts` may exercise the old `apiWebhook` behavior (enqueuing a job, resolving a flow, etc.). Read each remaining test — if it asserts the old 200 + enqueue path, mark it for deletion in Task 3.

### Task 3: Delete tests that exercised the old `apiWebhook` 200 behavior

**Files:**
- Modify: `back/src/app-api/flux/flux.controller.api-v2-queue.spec.ts`

- [ ] **Step 1: Identify and delete stale tests**

For every `it(...)` or `describe(...)` block in the file that assumes `apiWebhook` returns 200, enqueues an `apiV2Job`, or resolves a flow — delete the block. Keep the new "returns 410 Gone" test from Task 1.

- [ ] **Step 2: Run the file — expect only the 410 test remains**

Run: `cd back && pnpm test -- --testPathPattern=flux.controller.api-v2-queue.spec.ts`
Expected: all remaining tests PASS. Count of passing tests should be exactly the tests you kept (at minimum the 410 test).

---

## PART 3 — Address-token for the email trigger

### Task 4: Token helper + failing tests

**Files:**
- Create: `back/src/utils/generate-email-trigger-token.ts`
- Create: `back/src/utils/generate-email-trigger-token.spec.ts`

- [ ] **Step 1: Write the failing tests**

Create `back/src/utils/generate-email-trigger-token.spec.ts`:

```ts
import {
  generateEmailTriggerToken,
  timingSafeEqualStrings,
} from './generate-email-trigger-token';

describe('generateEmailTriggerToken', () => {
  it('returns a base64url string of at least 40 characters', () => {
    const token = generateEmailTriggerToken();
    expect(token).toMatch(/^[A-Za-z0-9_-]+$/);
    expect(token.length).toBeGreaterThanOrEqual(40);
  });

  it('returns a different value on each call', () => {
    const a = generateEmailTriggerToken();
    const b = generateEmailTriggerToken();
    expect(a).not.toBe(b);
  });
});

describe('timingSafeEqualStrings', () => {
  it('returns true for equal strings', () => {
    expect(timingSafeEqualStrings('abc', 'abc')).toBe(true);
  });

  it('returns false for different strings of equal length', () => {
    expect(timingSafeEqualStrings('abc', 'abd')).toBe(false);
  });

  it('returns false for strings of different length without throwing', () => {
    expect(timingSafeEqualStrings('abc', 'abcd')).toBe(false);
  });

  it('returns false when either argument is empty', () => {
    expect(timingSafeEqualStrings('', 'abc')).toBe(false);
    expect(timingSafeEqualStrings('abc', '')).toBe(false);
    expect(timingSafeEqualStrings('', '')).toBe(false);
  });
});
```

- [ ] **Step 2: Run the tests — expect all to fail**

Run: `cd back && pnpm test -- --testPathPattern=generate-email-trigger-token.spec.ts`
Expected: module not found / all tests FAIL.

- [ ] **Step 3: Implement the helper**

Create `back/src/utils/generate-email-trigger-token.ts`:

```ts
import { randomBytes, timingSafeEqual } from 'crypto';

const TOKEN_BYTES = 32;

export function generateEmailTriggerToken(): string {
  return randomBytes(TOKEN_BYTES).toString('base64url');
}

export function timingSafeEqualStrings(a: string, b: string): boolean {
  if (!a || !b) return false;
  if (a.length !== b.length) return false;
  return timingSafeEqual(Buffer.from(a), Buffer.from(b));
}
```

- [ ] **Step 4: Re-run the tests — expect all to pass**

Run: `cd back && pnpm test -- --testPathPattern=generate-email-trigger-token.spec.ts`
Expected: all tests PASS.

### Task 5: Migration to add `email_trigger_token` column + backfill

**Files:**
- Create: `back/src/database/migrations/1789000000000-AddFlowEmailTriggerToken.ts`

Note on timestamp: use `1789000000000` (matches the sequence pattern of existing migrations in the folder — the last one is `1788800000000`). If a newer migration lands before this one, bump to the next free slot.

- [ ] **Step 1: Create the migration file**

Create `back/src/database/migrations/1789000000000-AddFlowEmailTriggerToken.ts`:

```ts
import { MigrationInterface, QueryRunner } from 'typeorm';
import { randomBytes } from 'crypto';

export class AddFlowEmailTriggerToken1789000000000 implements MigrationInterface {
  name = 'AddFlowEmailTriggerToken1789000000000';

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "flows" ADD COLUMN IF NOT EXISTS "emailTriggerToken" varchar(64) NULL`,
    );

    const rows: Array<{ id: string }> = await queryRunner.query(
      `SELECT "id" FROM "flows" WHERE "emailTriggerToken" IS NULL`,
    );

    const BATCH_SIZE = 500;
    for (let i = 0; i < rows.length; i += BATCH_SIZE) {
      const batch = rows.slice(i, i + BATCH_SIZE);
      await Promise.all(
        batch.map((row) => {
          const token = randomBytes(32).toString('base64url');
          return queryRunner.query(
            `UPDATE "flows" SET "emailTriggerToken" = $1 WHERE "id" = $2`,
            [token, row.id],
          );
        }),
      );
    }

    await queryRunner.query(
      `ALTER TABLE "flows" ALTER COLUMN "emailTriggerToken" SET NOT NULL`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE "flows" DROP COLUMN IF EXISTS "emailTriggerToken"`,
    );
  }
}
```

Notes:
- The migration duplicates the token-generation logic instead of importing the helper, because migrations must not depend on evolving application code.
- Column name uses camelCase to match TypeORM's default naming convention already used across other columns in the `flows` table (e.g. `backgroundColor`).
- Backfill batches to avoid holding all rows in memory for large tables.

- [ ] **Step 2: Verify the migration is picked up locally**

Run: `cd back && pnpm dev:api`
Expected: on startup, log shows `AddFlowEmailTriggerToken1789000000000` executed. Confirm by connecting to local Postgres and running:

```sql
SELECT COUNT(*) FROM flows WHERE "emailTriggerToken" IS NULL;
```

Expected: `0`. And:

```sql
\d flows
```

Expected: `emailTriggerToken` column present, `not null`.

### Task 6: Add `emailTriggerToken` to Flow entity

**Files:**
- Modify: `back/src/entities/flow.entity.ts`

- [ ] **Step 1: Add the column**

In `flow.entity.ts`, add the following column definition next to the other simple columns (e.g., near the existing `public` column around line 72):

```ts
  @Column({ type: 'varchar', length: 64 })
  @Expose()
  emailTriggerToken: string;
```

Note: not marked `nullable` — the migration in Task 5 already backfilled all rows and set `NOT NULL`.

- [ ] **Step 2: Restart the API and verify TypeORM does not attempt a schema change**

Run: `cd back && pnpm dev:api`
Expected: no "column already exists" error, no synchronize-triggered ALTER on startup, API starts clean.

### Task 7: Generate `emailTriggerToken` on every flow creation

**Files:**
- Modify: `back/src/app-api/folw/flow.service.ts:242-265`

- [ ] **Step 1: Add the import at the top of the file**

```ts
import { generateEmailTriggerToken } from 'src/utils/generate-email-trigger-token';
```

- [ ] **Step 2: Inject token generation into `createFlowWithNodesAndEdges`**

Replace the current `createFlowWithNodesAndEdges` method body (lines 242-265) with:

```ts
  async createFlowWithNodesAndEdges(
    data: DeepPartial<Flow>,
    nodes: any[],
    edges: any[],
  ): Promise<Flow> {
    return this.dataSource.transaction(async (manager) => {
      const flowRepo = manager.getRepository(Flow);

      const dataWithToken: DeepPartial<Flow> = {
        ...data,
        emailTriggerToken: data.emailTriggerToken ?? generateEmailTriggerToken(),
      };
      const flow = await flowRepo.save(dataWithToken);

      if (nodes?.length > 0) {
        await this.flowNodeService.upsertNodes(flow.id, nodes, manager);
      }
      if (edges?.length > 0) {
        await this.flowEdgeService.upsertEdges(flow.id, edges, manager);
      }

      flow.nodes = nodes ?? [];
      flow.edges = edges ?? [];

      return flow;
    });
  }
```

The `??` fallback lets callers override the token if they ever need to (e.g. tests, seeds); the default path always gets a fresh token.

- [ ] **Step 3: Manual smoke test**

Run: `cd back && pnpm dev:api` and hit the `POST /flow` endpoint (or use the frontend to create a flow). Then query:

```sql
SELECT id, name, "emailTriggerToken" FROM flows ORDER BY "createdAt" DESC LIMIT 1;
```

Expected: the newest flow has a non-null `emailTriggerToken` that is a ~43-char base64url string.

### Task 8: Add rotation endpoint — service method + failing controller test

**Files:**
- Modify: `back/src/app-api/folw/flow.service.ts`
- Create: `back/src/app-api/folw/dto/rotate-email-trigger-token.dto.ts`
- Modify: `back/src/app-api/folw/flow.controller.ts`
- Create: `back/src/app-api/folw/flow.controller.rotate-email-trigger.spec.ts`

- [ ] **Step 1: Create the response DTO**

Create `back/src/app-api/folw/dto/rotate-email-trigger-token.dto.ts`:

```ts
import { ApiProperty } from '@nestjs/swagger';

export class RotateEmailTriggerTokenResponseDto {
  @ApiProperty({
    description:
      'The full new email trigger address for this flow. Any integration using the previous address will stop working.',
    example: 'a1b2c3d4-...+xYz...@upload.fluxprompt.com',
  })
  emailTriggerAddress: string;
}
```

- [ ] **Step 2: Add the service method**

In `flow.service.ts`, add this method (place near `createFlowWithNodesAndEdges`):

```ts
  async rotateEmailTriggerToken(
    flowId: string,
    userId: string,
  ): Promise<{ emailTriggerAddress: string }> {
    const flow = await Flow.findOne({
      where: { id: flowId },
      relations: { user: true },
    });
    if (!flow) {
      throw new NotFoundException('Flow not found');
    }
    if (flow.user?.id !== userId) {
      throw new ForbiddenException('You do not own this flow');
    }

    const newToken = generateEmailTriggerToken();
    await Flow.update(flow.id, { emailTriggerToken: newToken });

    const domain = process.env.EMAIL_TRIGGER_DOMAIN || 'upload.fluxprompt.com';
    return {
      emailTriggerAddress: `${flow.id}+${newToken}@${domain}`,
    };
  }
```

Add the imports at the top of `flow.service.ts`:

```ts
import { ForbiddenException, NotFoundException } from '@nestjs/common';
```

- [ ] **Step 3: Write the failing controller test**

Create `back/src/app-api/folw/flow.controller.rotate-email-trigger.spec.ts`:

```ts
import { ForbiddenException, NotFoundException } from '@nestjs/common';

describe('FlowController - rotateEmailTriggerToken', () => {
  let controller: any;
  let rotateEmailTriggerToken: jest.Mock;

  beforeEach(() => {
    rotateEmailTriggerToken = jest.fn();
    controller = {
      flowService: { rotateEmailTriggerToken },
      rotateEmailTriggerToken: async function (res: any, id: string, user: any) {
        try {
          const result = await this.flowService.rotateEmailTriggerToken(
            id,
            user.id,
          );
          res.status(200).json(result);
        } catch (err) {
          if (err instanceof NotFoundException) {
            res.status(404).json({ message: err.message });
            return;
          }
          if (err instanceof ForbiddenException) {
            res.status(403).json({ message: err.message });
            return;
          }
          throw err;
        }
      },
    };
  });

  function makeRes() {
    const res: any = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    return res;
  }

  it('returns the new address when the caller owns the flow', async () => {
    rotateEmailTriggerToken.mockResolvedValue({
      emailTriggerAddress: 'flow-1+newtoken@upload.fluxprompt.com',
    });
    const res = makeRes();

    await controller.rotateEmailTriggerToken(res, 'flow-1', { id: 'user-1' });

    expect(rotateEmailTriggerToken).toHaveBeenCalledWith('flow-1', 'user-1');
    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith({
      emailTriggerAddress: 'flow-1+newtoken@upload.fluxprompt.com',
    });
  });

  it('returns 404 when the flow does not exist', async () => {
    rotateEmailTriggerToken.mockRejectedValue(
      new NotFoundException('Flow not found'),
    );
    const res = makeRes();

    await controller.rotateEmailTriggerToken(res, 'nope', { id: 'user-1' });

    expect(res.status).toHaveBeenCalledWith(404);
  });

  it('returns 403 when the caller does not own the flow', async () => {
    rotateEmailTriggerToken.mockRejectedValue(
      new ForbiddenException('You do not own this flow'),
    );
    const res = makeRes();

    await controller.rotateEmailTriggerToken(res, 'flow-1', { id: 'other-user' });

    expect(res.status).toHaveBeenCalledWith(403);
  });
});
```

Note: this spec exercises the controller shape in isolation. When the real controller method is wired in (Step 4 below), replace this test's inline object with a proper Nest `Test.createTestingModule` setup if the file's existing tests use that pattern (check `flow.controller.create-flow.spec.ts` for the local convention and mirror it).

- [ ] **Step 4: Run the test — expect it to pass**

Run: `cd back && pnpm test -- --testPathPattern=flow.controller.rotate-email-trigger.spec.ts`
Expected: all 3 tests PASS (they test the shape, not the wired controller yet).

- [ ] **Step 5: Wire the real controller endpoint**

In `back/src/app-api/folw/flow.controller.ts`, add near the other `@Post('/...')` methods:

```ts
  @ApiSingleDto({
    status: 200,
    description: 'Rotate the email trigger token for a flow',
    type: RotateEmailTriggerTokenResponseDto,
  })
  @UseGuards(JwtAuthGuard)
  @Post(':id/rotate-email-trigger-token')
  async rotateEmailTriggerToken(
    @Res() res: Response,
    @Param('id', ParseUUIDPipe) id: string,
    @CurrentUser() user: User,
  ) {
    const result = await this.flowService.rotateEmailTriggerToken(
      id,
      user.id,
    );
    return this.success(res, result, RotateEmailTriggerTokenResponseDto);
  }
```

The service throws `NotFoundException` and `ForbiddenException` — NestJS's default exception filter maps those to 404 and 403 automatically. No `try/catch` needed in the controller.

Add this import at the top of `flow.controller.ts`:

```ts
import { RotateEmailTriggerTokenResponseDto } from './dto/rotate-email-trigger-token.dto';
```

- [ ] **Step 6: Smoke test the endpoint**

Run: `cd back && pnpm dev:api`, then from an authenticated session:

```bash
curl -X POST http://localhost:3000/flow/<flowId>/rotate-email-trigger-token \
  -H 'Authorization: Bearer <jwt>'
```

Expected: 200 with `{ "emailTriggerAddress": "<flowId>+<newtoken>@upload.fluxprompt.com" }`. In DB, `flows.emailTriggerToken` for that row has changed.

Try the same call with a JWT belonging to a different user:
Expected: 403.

### Task 9: Add failing MailService test — new format accepted, old format rejected

**Files:**
- Modify: `back/src/app-api/mail/mail.service.spec.ts`

- [ ] **Step 1: Add new test cases in a new `describe` block**

Append to `mail.service.spec.ts`:

```ts
describe('MailService - address-token authentication', () => {
  let service: MailService;
  let getFlow: jest.Mock;
  let enqueueApiV2Job: jest.Mock;
  let sendMail: jest.SpyInstance;

  const logger = {
    log: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    getFlow = jest.fn();
    enqueueApiV2Job = jest.fn().mockResolvedValue(undefined);

    service = new MailService(
      { findOne: jest.fn() } as any, // userService (no longer used by processEmail)
      logger as any,
      { enqueueApiV2Job } as any,
      { getFlowWithNodesAndEdges: getFlow } as any,
      { uploadFile: jest.fn() } as any,
    );

    sendMail = jest.spyOn(service, 'sendMail').mockResolvedValue(undefined);
  });

  const FLOW_ID = '550e8400-e29b-41d4-a716-446655440000';
  const GOOD_TOKEN = 'ValidTokenAtLeast20CharactersLong';

  function buildMime(from: string, to: string) {
    return [
      `From: ${from}`,
      `To: ${to}`,
      'Subject: hi',
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset=utf-8',
      '',
      'body content',
    ].join('\r\n');
  }

  it('accepts the new format when the token matches', async () => {
    getFlow.mockResolvedValue({
      id: FLOW_ID,
      emailTriggerToken: GOOD_TOKEN,
      user: { id: 'owner' },
      nodes: [{ id: 'n1', type: 'varInputNode' }],
    });

    await service.processEmail(
      buildMime(
        'anyone@example.com',
        `${FLOW_ID}+${GOOD_TOKEN}@upload.fluxprompt.com`,
      ),
    );

    expect(enqueueApiV2Job).toHaveBeenCalledTimes(1);
    expect(sendMail).not.toHaveBeenCalled();
  });

  it('rejects the old format (bare flowId, no token) with a bounce', async () => {
    await service.processEmail(
      buildMime('anyone@example.com', `${FLOW_ID}@upload.fluxprompt.com`),
    );

    expect(enqueueApiV2Job).not.toHaveBeenCalled();
    expect(sendMail).toHaveBeenCalledWith(
      ['anyone@example.com'],
      'Invalid trigger address!',
      expect.stringContaining('new trigger address'),
    );
  });

  it('rejects the new format with a wrong token', async () => {
    getFlow.mockResolvedValue({
      id: FLOW_ID,
      emailTriggerToken: GOOD_TOKEN,
      user: { id: 'owner' },
      nodes: [{ id: 'n1', type: 'varInputNode' }],
    });

    await service.processEmail(
      buildMime(
        'anyone@example.com',
        `${FLOW_ID}+WrongTokenAtLeast20CharsHere@upload.fluxprompt.com`,
      ),
    );

    expect(enqueueApiV2Job).not.toHaveBeenCalled();
    expect(sendMail).toHaveBeenCalledWith(
      ['anyone@example.com'],
      'Invalid trigger address!',
      expect.stringContaining('does not match'),
    );
  });

  it('accepts the new format regardless of the From header (public flow)', async () => {
    getFlow.mockResolvedValue({
      id: FLOW_ID,
      emailTriggerToken: GOOD_TOKEN,
      user: { id: 'owner' },
      public: true,
      nodes: [{ id: 'n1', type: 'varInputNode' }],
    });

    await service.processEmail(
      buildMime(
        'stranger@example.com',
        `${FLOW_ID}+${GOOD_TOKEN}@upload.fluxprompt.com`,
      ),
    );

    expect(enqueueApiV2Job).toHaveBeenCalledTimes(1);
    expect(sendMail).not.toHaveBeenCalled();
  });

  it('no longer inspects the From header for private flows', async () => {
    getFlow.mockResolvedValue({
      id: FLOW_ID,
      emailTriggerToken: GOOD_TOKEN,
      user: { id: 'owner', email: 'owner@example.com' },
      public: false,
      nodes: [{ id: 'n1', type: 'varInputNode' }],
    });

    await service.processEmail(
      buildMime(
        'not-the-owner@attacker.example',
        `${FLOW_ID}+${GOOD_TOKEN}@upload.fluxprompt.com`,
      ),
    );

    expect(enqueueApiV2Job).toHaveBeenCalledTimes(1);
    expect(sendMail).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run the tests — expect all 5 to fail**

Run: `cd back && pnpm test -- --testPathPattern=mail.service.spec.ts`
Expected: the 5 new tests FAIL because the current `processEmail` parses `<flowId>@` (old format), does not check any token, and checks `From` against `flow.user` for private flows.

### Task 10: Rewrite `MailService.processEmail` to use address-token

**Files:**
- Modify: `back/src/app-api/mail/mail.service.ts`

- [ ] **Step 1: Add the import at the top of the file**

```ts
import { timingSafeEqualStrings } from 'src/utils/generate-email-trigger-token';
```

- [ ] **Step 2: Replace the parsing block and the `From` check block**

Locate `processEmail` (starts around line 345). Replace the address-parsing region (currently lines 355-405, from `const tagRegex = /^[^@]+/` through the `if (flowId === null || !isUUID(flowId))` block) with:

```ts
    const ADDRESS_PATTERN =
      /^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\+([A-Za-z0-9_-]{20,})@/i;

    let recipientEmail = parsedEmail?.to?.value?.[0]?.address;
    if (!recipientEmail || !ADDRESS_PATTERN.test(recipientEmail)) {
      const receivedHeader = parsedEmail.headers?.get('received');
      if (receivedHeader) {
        const receivedHeaders = Array.isArray(receivedHeader)
          ? receivedHeader
          : [receivedHeader];
        for (const header of receivedHeaders) {
          const headerString = String(header).replace(/[\r\n\t]+/g, ' ');
          const forMatch = headerString.match(
            /for\s+<([^>]+)>/i,
          );
          if (forMatch && ADDRESS_PATTERN.test(forMatch[1])) {
            recipientEmail = forMatch[1];
            break;
          }
        }
      }
      if (!recipientEmail || !ADDRESS_PATTERN.test(recipientEmail)) {
        const deliveredTo = parsedEmail.headers?.get('delivered-to');
        if (deliveredTo && ADDRESS_PATTERN.test(String(deliveredTo))) {
          recipientEmail = String(deliveredTo);
        }
      }
    }

    if (!parsedEmail?.from?.value?.[0]?.address) {
      await this.loggerService.error({
        message:
          'MailService (ProcessEmail) - Email missing required "from" field structure',
        metadata: {
          status: 400,
          error_type: 'missing_from',
          user: null,
          other: { emailData: data },
        },
      });
      return;
    }

    const senderAddress = parsedEmail.from.value[0].address;

    const match = recipientEmail
      ? ADDRESS_PATTERN.exec(recipientEmail)
      : null;
    if (!match) {
      await this.loggerService.warn({
        message:
          'MailService (ProcessEmail) - Recipient address does not match expected <flowId>+<token>@ format',
        metadata: {
          status: 400,
          error_type: 'invalid_address_format',
          user: null,
          other: { recipientEmail },
        },
      });
      await this.sendMail(
        [senderAddress],
        'Invalid trigger address!',
        'This address is no longer accepted. Get your new trigger address from the flow settings page.',
      );
      return;
    }

    const [, flowId, providedToken] = match;
```

- [ ] **Step 3: Replace the flow-lookup + `From` check block with a token check**

Locate the region that currently starts at `const flow = await this.flowService.getFlowWithNodesAndEdges(flowId, ['user']);` and ends after the `if (user?.id !== flow.user?.id)` block (currently around lines 441-500). Replace with:

```ts
    const flow = await this.flowService.getFlowWithNodesAndEdges(flowId, [
      'user',
    ]);

    if (!flow) {
      await this.sendMail([senderAddress], 'Flow not found!');
      return;
    }

    if (!timingSafeEqualStrings(flow.emailTriggerToken, providedToken)) {
      await this.loggerService.warn({
        message:
          'MailService (ProcessEmail) - Token in address does not match flow',
        metadata: {
          status: 401,
          error_type: 'invalid_trigger_token',
          user: null,
          other: { flowId, senderAddress },
        },
      });
      await this.sendMail(
        [senderAddress],
        'Invalid trigger address!',
        'The token in this address does not match. Get your new trigger address from the flow settings page.',
      );
      return;
    }
```

The old `if (!flow.public) { … From check … }` block is deleted entirely.

Also update the `const text = ...` line further down to use `senderAddress` instead of `parsedEmail.from.value[0].address` (small cleanup — same value, less repetition).

- [ ] **Step 4: Remove now-unused imports and services**

If `UserService` is no longer referenced anywhere in `MailService` after the deletion (search the file for `userService`), remove its `@Inject` and its constructor parameter, and delete the import at the top. If it is still referenced by another method in the file (e.g., `sendGmailEmail`), leave it.

- [ ] **Step 5: Re-run the mail service tests — expect all to pass**

Run: `cd back && pnpm test -- --testPathPattern=mail.service.spec.ts`
Expected: all tests PASS, including the 5 new address-token tests from Task 9 and any pre-existing attachment tests.

### Task 11: Update pre-existing MailService tests that relied on old behavior

**Files:**
- Modify: `back/src/app-api/mail/mail.service.spec.ts`

- [ ] **Step 1: Review pre-existing tests**

Skim the top-of-file `describe('MailService - email attachments', ...)` block from Task 9's read. Any test that sends email to `<FLOW_UUID>@upload.fluxprompt.com` (old format) will now be rejected as invalid and won't reach the attachment code path. Those tests need their `to` address updated to `<FLOW_UUID>+<token>@upload.fluxprompt.com` and their `getFlow` mock updated to return a flow with `emailTriggerToken: <that same token>`.

- [ ] **Step 2: Update the fixtures**

For every `buildMime({ to: `${FLOW_UUID}@…` })` in the file, change to `${FLOW_UUID}+${GOOD_TOKEN}@…` and ensure the `getFlow` mock returns `{ id, emailTriggerToken: GOOD_TOKEN, user: ..., nodes: ... }`.

Define `GOOD_TOKEN` at file scope if not already:

```ts
const GOOD_TOKEN = 'ValidTokenAtLeast20CharactersLong';
```

- [ ] **Step 3: Re-run the tests**

Run: `cd back && pnpm test -- --testPathPattern=mail.service.spec.ts`
Expected: all tests PASS.

---

## FRONTEND

### Task 12: Locate the flow-settings screens and identify the sections to replace

**Files:**
- Read-only: `front/src/**` — find the components that render the webhook URL card and the email trigger card

- [ ] **Step 1: Find the webhook URL section**

Run: `cd front && rg -l 'api-v2-webhook|apiWebhook|webhook.*url' src/`
Expected: a small number of files. Identify the component(s) that display the webhook URL in flow settings.

- [ ] **Step 2: Find the email trigger section**

Run: `cd front && rg -l 'upload\.fluxprompt|emailTrigger|email.*trigger|@upload' src/`
Expected: a small number of files. Identify the component(s) that display the email trigger address.

- [ ] **Step 3: Record the paths in this plan**

Write the two file paths into the top of this task in a comment:

```
Webhook section:  front/src/<path-here>
Email section:    front/src/<path-here>
```

The engineer executing Tasks 13 and 14 uses these paths as the "Modify" targets. If the search returns unexpected files (tests, storybook), narrow with `rg -l -g 'src/components/**' ...`.

### Task 13: Replace the webhook URL card with "Trigger via API" guidance

**Files:**
- Modify: `front/src/<path from Task 12>`

- [ ] **Step 1: Delete the current webhook URL card**

Remove the JSX block that renders the `api-v2-webhook` URL along with any copy-to-clipboard wiring specific to it.

- [ ] **Step 2: Insert the new "Trigger via API" card**

Add a card component in the same place, styled to match the surrounding sections. It must show two blocks with copy buttons:

Block 1 — trigger:
```
POST https://<api-host>/flux/api-v2?flowId=<this-flow-id>&callback_url=<your-callback>
Header: api-key: FLUX_API.xxxxxxxx
Body:   { "variableInputs": [ { "inputId": "...", "inputText": "..." } ] }
```

Block 2 — status polling:
```
GET https://<api-host>/flux/executions/<executionId>
Header: api-key: FLUX_API.xxxxxxxx
```

Copy near the top of the card:

> Trigger this flow from any HTTP client using your API key. Pass a `callback_url` to receive the result via POST, or omit it and poll the executions endpoint until `status: completed`.

Reuse whatever helper the codebase has for copy-to-clipboard (search: `rg 'copyToClipboard|useCopyToClipboard|writeText' src/`).

- [ ] **Step 3: Manual verification in the browser**

Run: `cd front && pnpm dev`. Open a flow's settings. Expected: the old webhook card is gone; the new "Trigger via API" card is present; copy buttons work; the flow-id in the snippet matches the current flow.

### Task 14: Replace the email trigger card with token address + rotate button

**Files:**
- Modify: `front/src/<path from Task 12>`

- [ ] **Step 1: Delete the current email trigger card**

Remove the JSX block that renders the old `<flowId>@upload.fluxprompt.com` address.

- [ ] **Step 2: Add the new card**

The new card shows:

```
Email trigger address
[ <flowId>+<emailTriggerToken>@upload.fluxprompt.com ]  [Copy]

This address is a credential — anyone who has it can trigger this flow
at your expense. Keep it inside your Zapier/Make/forwarding config.

[Rotate address]
```

The flow object returned by the existing "get flow" React Query hook must include the `emailTriggerToken` field. If it doesn't, extend the query's TypeScript type and the backend response DTO to expose it (backend: add `emailTriggerToken` to whichever DTO the `GET /flow/:id` endpoint returns, gated to the flow owner).

- [ ] **Step 3: Wire the Rotate button**

Add a new React Query mutation:

```ts
const rotateEmailTriggerToken = useMutation({
  mutationFn: async (flowId: string) => {
    const res = await api.post<{ emailTriggerAddress: string }>(
      `/flow/${flowId}/rotate-email-trigger-token`,
    );
    return res.data;
  },
  onSuccess: (data, flowId) => {
    queryClient.invalidateQueries({ queryKey: ['flow', flowId] });
  },
});
```

(Adjust `api` and query keys to match the project's existing conventions — see any other flow-mutation in the same folder for the pattern.)

The Rotate button opens a confirm modal (reuse the project's existing confirm modal component):

> Rotating this address will immediately invalidate the current one. Any integration (Zapier, Make, Gmail forwarding rule) still using the old address will stop working. Continue?

On confirm → call the mutation.

- [ ] **Step 4: Manual verification in the browser**

Run: `cd front && pnpm dev`. Open a flow's settings. Expected:
- Old `<flowId>@` address is gone.
- New `<flowId>+<token>@` address shows.
- Copy button copies the address.
- Clicking Rotate opens the modal; confirming rotates the address (verify the shown address changes and the DB `emailTriggerToken` for that flow changes).

---

## DOCS

### Task 15: Update Mintlify docs

**Files:**
- Read-only search: `docs/**` — locate the pages for `/api-v2-webhook`, `/api-v2`, and the email trigger

- [ ] **Step 1: Delete the webhook page**

Run: `cd docs && rg -l 'api-v2-webhook' .`
Delete every page whose primary topic is `/api-v2-webhook`. If it's mentioned in passing on another page, remove the mention and add a one-line note pointing to `/api-v2`.

- [ ] **Step 2: Expand the `/api-v2` page**

Locate the `/api-v2` page and extend it with:
- A "Callback pattern" section explaining `callback_url` (optional; if provided, Fluxprompt POSTs the result there when the run finishes).
- A "Polling pattern" section documenting `GET /flux/executions/:executionId` (returns `pending` / `in_progress` / `completed` / `error`, plus `output`, `tokensUsed`, `totalCost`, `durationMs` on completion, or `errorMessage` on failure).

Show a full `curl` example of each.

- [ ] **Step 3: Rewrite the email trigger page**

The email trigger page must state:
- Address format is now `<flowId>+<token>@upload.fluxprompt.com`.
- The address itself is the credential; keep it private.
- The address is shown in the flow's settings page (link).
- Rotation invalidates the previous address immediately; update any integration to the new address before rotating.
- The `From` header is no longer inspected; anyone with the address may trigger the flow.

- [ ] **Step 4: Local render check (Mintlify)**

Run: `cd docs && pnpm mintlify dev` (or whatever the project's docs preview command is — check `docs/package.json` `scripts`).
Expected: the three updated pages render without broken links.

---

## Self-Review Checklist (for the engineer executing this plan)

Before declaring the plan complete, verify:

- [ ] `curl -X POST http://<host>/flux/api-v2-webhook?flowId=<any>` returns HTTP 410 with the migration message.
- [ ] Sending an email to `<flowId>@upload.fluxprompt.com` (old format) triggers no run and produces a bounce reply.
- [ ] Sending an email to `<flowId>+<wrong-token>@upload.fluxprompt.com` triggers no run and produces a bounce reply.
- [ ] Sending an email to `<flowId>+<correct-token>@upload.fluxprompt.com` triggers exactly one run for the flow owner, regardless of what's in the `From` header, regardless of whether the flow is public or private.
- [ ] `POST /flow/:id/rotate-email-trigger-token` (owner JWT) returns 200 with the new address, and `POST /flow/:id/rotate-email-trigger-token` (non-owner JWT) returns 403.
- [ ] The flow settings screen no longer shows the old webhook URL or the old email address; it shows the new API guidance and the new token-based email address with a working Rotate button.
- [ ] Every existing flow in the local DB has a non-null `emailTriggerToken`.

---

## Not in this plan

- Rate limiting (S7 Part 2 — separate Wave 1 card).
- DKIM/SPF/DMARC verification (future reinforcement on top of the address-token).
- Audit log entry for token rotations.
- Any usage-analytics dashboard for the retired webhook route.
- Migration of any external customer integrations that call the retired routes — those callers hit 410 (webhook) or receive a bounce reply (email old format) and follow the migration guidance to the new endpoints/addresses.
