import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const config = JSON.parse(readFileSync(".secret-patterns.json", "utf8"));
const patterns = config.patterns.map((pattern) => new RegExp(pattern, "g"));
const placeholderValues = new Set(
  config.allowPlaceholderValues.map((value) => value.toLowerCase())
);
const skipPath =
  /(^|\/)(\.git|node_modules|dist|build|coverage|\.next|out)(\/|$)|package-lock\.json$/;
const binaryExtensions = /\.(png|jpe?g|gif|webp|ico|pdf|zip|gz|tar|woff2?|ttf|eot)$/i;

const git = spawnSync("git", ["ls-files", "--cached", "--others", "--exclude-standard"], {
  encoding: "utf8",
});

if (git.status !== 0) {
  process.stderr.write(git.stderr);
  process.exit(git.status ?? 1);
}

const files = git.stdout
  .split("\n")
  .filter(Boolean)
  .filter((file) => !skipPath.test(file) && !binaryExtensions.test(file));

const findings = [];

for (const file of files) {
  let content;
  try {
    content = readFileSync(file, "utf8");
  } catch {
    continue;
  }

  for (const pattern of patterns) {
    pattern.lastIndex = 0;
    if (pattern.test(content)) {
      findings.push(`${file}: matched secret pattern ${pattern.source}`);
    }
  }

  if (file.endsWith(".env.example")) {
    continue;
  }

  const lines = content.split("\n");
  lines.forEach((line, index) => {
    const match = line.match(
      /^\s*([A-Z0-9_]*(?:SECRET|TOKEN(?!S\b)|KEY|PASSWORD)[A-Z0-9_]*)\s*=\s*(.+?)\s*$/i
    );
    if (!match) {
      return;
    }

    const value = match[2]
      .replace(/^['\"]|['\"]$/g, "")
      .trim()
      .toLowerCase();
    if (!placeholderValues.has(value) && !value.startsWith("your_") && !value.startsWith("<")) {
      findings.push(`${file}:${index + 1}: possible secret value assigned to ${match[1]}`);
    }
  });
}

if (findings.length > 0) {
  console.error("Secret scan failed:");
  findings.forEach((finding) => console.error(`- ${finding}`));
  process.exit(1);
}

console.log(`Secret scan passed (${files.length} files checked).`);
