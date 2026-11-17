// Provided: idempotency store contract plus a DynamoDB implementation (conditional writes).
// The handler decides WHEN to claim, complete and release; the tests use an in-memory store.
import { DynamoDBDocumentClient, PutCommand, GetCommand, UpdateCommand, DeleteCommand } from "@aws-sdk/lib-dynamodb";

export type ClaimResult = "CLAIMED" | "COMPLETED" | "IN_PROGRESS";

export interface IdempotencyStore {
  /** Claim the key. COMPLETED: already done (skip). IN_PROGRESS: another worker holds a fresh claim. */
  claim(key: string): Promise<ClaimResult>;
  /** Mark the key done and store a small result. */
  complete(key: string, result: Record<string, unknown>): Promise<void>;
  /** Drop an in-progress claim so a retry can take over immediately. */
  release(key: string): Promise<void>;
}

export class DynamoIdempotencyStore implements IdempotencyStore {
  constructor(
    private ddb: DynamoDBDocumentClient,
    private table: string,
    private ttlSeconds: number,
    private inProgressExpirySeconds: number,
    private nowSec: () => number = () => Math.floor(Date.now() / 1000),
  ) {}

  async claim(key: string): Promise<ClaimResult> {
    const now = this.nowSec();
    try {
      await this.ddb.send(new PutCommand({
        TableName: this.table,
        Item: { pk: key, status: "IN_PROGRESS", expiresAt: now + this.inProgressExpirySeconds, ttl: now + this.ttlSeconds },
        ConditionExpression: "attribute_not_exists(pk) OR (#s = :ip AND expiresAt < :now)",
        ExpressionAttributeNames: { "#s": "status" },
        ExpressionAttributeValues: { ":ip": "IN_PROGRESS", ":now": now },
      }));
      return "CLAIMED";
    } catch (err) {
      if ((err as Error).name !== "ConditionalCheckFailedException") throw err;
      const cur = await this.ddb.send(new GetCommand({ TableName: this.table, Key: { pk: key }, ConsistentRead: true }));
      return cur.Item && cur.Item.status === "COMPLETED" ? "COMPLETED" : "IN_PROGRESS";
    }
  }

  async complete(key: string, result: Record<string, unknown>): Promise<void> {
    await this.ddb.send(new UpdateCommand({
      TableName: this.table, Key: { pk: key },
      UpdateExpression: "SET #s = :c, #r = :r",
      ExpressionAttributeNames: { "#s": "status", "#r": "result" },
      ExpressionAttributeValues: { ":c": "COMPLETED", ":r": result },
    }));
  }

  async release(key: string): Promise<void> {
    await this.ddb.send(new DeleteCommand({
      TableName: this.table, Key: { pk: key },
      ConditionExpression: "#s = :ip", ExpressionAttributeNames: { "#s": "status" }, ExpressionAttributeValues: { ":ip": "IN_PROGRESS" },
    })).catch(() => undefined);
  }
}
