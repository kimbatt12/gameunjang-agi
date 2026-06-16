import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const [dir, ...candidateScripts] = process.argv.slice(2);

if (!dir || candidateScripts.length === 0) {
  console.error("Usage: node scripts/run-if-dir.mjs <dir> <script> [fallback-script...]");
  process.exit(2);
}

const packagePath = join(process.cwd(), dir, "package.json");

if (!existsSync(dir)) {
  console.log(`skip: ${dir}/ does not exist`);
  process.exit(0);
}

if (!existsSync(packagePath)) {
  console.log(`skip: ${dir}/package.json does not exist`);
  process.exit(0);
}

const packageJson = JSON.parse(readFileSync(packagePath, "utf8"));
const scripts = packageJson.scripts ?? {};
const scriptName = candidateScripts.find((name) => scripts[name]);

if (!scriptName) {
  console.log(`skip: ${dir} has none of scripts: ${candidateScripts.join(", ")}`);
  process.exit(0);
}

const result = spawnSync("npm", ["--prefix", dir, "run", scriptName], {
  stdio: "inherit",
  shell: process.platform === "win32",
});

process.exit(result.status ?? 1);
