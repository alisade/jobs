// Idempotency records. Written by the platform team for lfg-email-to-ticket (REL-301); a record is
// claimed with a conditional write so exactly one caller wins per key.
import { DynamoDBDocumentClient, GetCommand, PutCommand, UpdateCommand } from "@aws-sdk/lib-dynamodb";

export interface IdempotencyRecord {
  key: string;
  status: "IN_PROGRESS" | "COMPLETED";
  result?: Record<string, string>;
}

export interface IdempotencyStore {
  /** true if this caller claimed the key (no record existed); false if someone else holds it */
  claim(key: string, ttlSeconds: number): Promise<boolean>;
  complete(key: string, result: Record<string, string>): Promise<void>;
  get(key: string): Promise<IdempotencyRecord | null>;
}

export class InMemoryIdempotencyStore implements IdempotencyStore {
  readonly records = new Map<string, IdempotencyRecord>();
  async claim(key: string): Promise<boolean> {
    if (this.records.has(key)) return false;
    this.records.set(key, { key, status: "IN_PROGRESS" });
    return true;
  }
  async complete(key: string, result: Record<string, string>): Promise<void> {
    this.records.set(key, { key, status: "COMPLETED", result });
  }
  async get(key: string): Promise<IdempotencyRecord | null> {
    return this.records.get(key) ?? null;
  }
}

/** Table: partition key "pk" (string), TTL attribute "expiresAt" (epoch seconds). */
export class DynamoIdempotencyStore implements IdempotencyStore {
  constructor(private doc: DynamoDBDocumentClient, private table: string, private now = () => Date.now()) {}

  async claim(key: string, ttlSeconds: number): Promise<boolean> {
    try {
      await this.doc.send(new PutCommand({
        TableName: this.table,
        Item: { pk: key, status: "IN_PROGRESS", expiresAt: Math.floor(this.now() / 1000) + ttlSeconds },
        ConditionExpression: "attribute_not_exists(pk)",
      }));
      return true;
    } catch (err: any) {
      if (err && err.name === "ConditionalCheckFailedException") return false;
      throw err;
    }
  }

  async complete(key: string, result: Record<string, string>): Promise<void> {
    await this.doc.send(new UpdateCommand({
      TableName: this.table,
      Key: { pk: key },
      UpdateExpression: "SET #s = :c, #r = :r",
      ExpressionAttributeNames: { "#s": "status", "#r": "result" },
      ExpressionAttributeValues: { ":c": "COMPLETED", ":r": result },
    }));
  }

  async get(key: string): Promise<IdempotencyRecord | null> {
    const out = await this.doc.send(new GetCommand({ TableName: this.table, Key: { pk: key }, ConsistentRead: true }));
    return out.Item ? { key, status: out.Item.status, result: out.Item.result } : null;
  }
}
