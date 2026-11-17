// Entry point (not used by the tests): node -r ts-node/register src/server.ts in a real deployment.
import { openDatabase } from "./db";
import { buildApp } from "./app";
import { installGracefulShutdown } from "./shutdown";

async function main(): Promise<void> {
  const app = buildApp({ db: await openDatabase() });
  installGracefulShutdown(app);
  await app.listen({ port: Number(process.env.PORT || 8080), host: "0.0.0.0" });
}

if (require.main === module) {
  main().catch((e) => { console.error(e); process.exit(1); });
}
