import { readFileSync } from "node:fs";

const commitMsgPath = process.argv[2];

if (!commitMsgPath) {
  console.error("Usage: node scripts/validate-commit-msg.mjs <commit-msg-file>");
  process.exit(2);
}

const message = readFileSync(commitMsgPath, "utf8").trim();
const firstLine = message.split("\n")[0];
const conventionalCommit =
  /^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9-]+\))?!?: .{1,100}$/;

if (!conventionalCommit.test(firstLine)) {
  console.error("Commit message must follow Conventional Commits.");
  console.error("Example: chore: configure development tooling");
  process.exit(1);
}

console.log("Commit message follows Conventional Commits.");
