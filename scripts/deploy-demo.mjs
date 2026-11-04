import { spawnSync } from "node:child_process";
import { mkdirSync, rmdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";

const repo = fileURLToPath(new URL("../", import.meta.url));
const compose = ["compose", "--project-name", "bbb_stack",
  "-f", "docker-compose.yml", "-f", "docker-compose.demo.yml",
  "-f", "docker-compose.deploy.yml", "--env-file", "deploy/images.env"];

function docker(args, options = {}) {
  const result = spawnSync("docker", ["--context", "desktop-linux", ...args], {
    cwd: repo, stdio: ["ignore", "pipe", "inherit"], ...options,
  });
  if (result.status !== 0) throw new Error(`Docker step failed: ${args[0]}`);
  return result.stdout;
}

function unlock(path) {
  if (!process.stdin.isTTY || !path?.endsWith(".abi-credentials.age")) {
    throw new Error("Run from a terminal and provide a .abi-credentials.age file");
  }
  const stat = statSync(path);
  if (!stat.isFile() || stat.size > 4096 || (stat.mode & 0o077) !== 0) {
    throw new Error("Use a regular encrypted credential file with private permissions");
  }
  const result = spawnSync("age", ["--decrypt", resolve(path)], {
    stdio: ["inherit", "pipe", "inherit"], maxBuffer: 8192,
  });
  if (result.status !== 0) {
    result.stdout?.fill(0);
    throw new Error("Could not unlock ABI credentials. Check the password and age installation.");
  }
  const plaintext = result.stdout;
  try {
    const pair = JSON.parse(plaintext.toString("utf8"));
    if (!Array.isArray(pair) || pair.length !== 2 || !pair.every(value =>
      typeof value === "string" && value.length <= 1024 && /^[A-Za-z0-9_-]+$/.test(value))) {
      throw new Error();
    }
    return Buffer.concat([plaintext, Buffer.from("\n")]);
  } catch {
    throw new Error("Invalid ABI credential pair");
  } finally {
    plaintext.fill(0);
  }
}

function composeRun(...args) {
  return docker([...compose, ...args]).toString().trim();
}

async function deploy(path) {
  const config = JSON.parse(composeRun("config", "--format", "json"));
  const abi = config.services.abi;
  if (abi.environment.BYBIT_ENV !== "demo") throw new Error("The launcher requires Bybit Demo");
  const expected = abi.image;
  if (!/^ghcr\.io\/roman-vyl\/abi_executor_bot:[0-9a-f]{40}$/.test(expected)) {
    throw new Error("Pin the ABI image to a published commit SHA");
  }

  const currentId = composeRun("ps", "-q", "abi");
  const hash = composeRun("config", "--hash", "abi").split(/\s+/).at(-1);
  const healthy = currentId && docker(["inspect", "--format",
    '{{.Config.Image}} {{index .Config.Labels "com.docker.compose.config-hash"}} {{.State.Health.Status}}',
    currentId]).toString().trim() === `${expected} ${hash} healthy`;

  composeRun("pull");
  if (!healthy) {
    try {
      docker(["run", "--rm", "--network", "none", "--entrypoint", "test", expected,
        "-f", "/app/dist/config/receiveProtectedCredentials.js"]);
    } catch {
      throw new Error("Cannot verify protected startup support in the pinned ABI image");
    }
    const frame = unlock(path);
    let id;
    try {
      composeRun("up", "-d", "--no-build", "--no-deps", "--force-recreate", "abi");
      id = composeRun("ps", "-q", "abi");
      if (!/^[0-9a-f]{64}$/.test(id)) throw new Error("Could not identify ABI container");
      const swap = docker(["exec", id, "cat", "/sys/fs/cgroup/memory.swap.max"]).toString().trim();
      if (swap !== "0") throw new Error("Container swap must be disabled");
      docker(["exec", "-i", id, "node", "dist/config/receiveProtectedCredentials.js"], { input: frame });
      frame.fill(0);
      for (let attempt = 0; attempt < 45; attempt++) {
        const state = docker(["inspect", "--format", "{{.State.Health.Status}}", id]).toString().trim();
        if (state === "healthy") break;
        if (state === "unhealthy" || attempt === 44) throw new Error("ABI did not become healthy");
        await delay(1000);
      }
    } catch (error) {
      if (id && /^[0-9a-f]{64}$/.test(id)) {
        try {
          docker(["stop", id]);
        } catch {
          console.error("Could not stop ABI after startup failure");
        }
      }
      throw error;
    } finally {
      frame.fill(0);
    }
  }

  // Keep Compose from pulling ABI in through Runtime's dependency.
  for (const services of [
    ["strategy-engine"], ["strategy-runtime"], ["market-data-service"], ["research-service", "journal-service"],
  ]) {
    composeRun("up", "-d", "--no-build", "--no-deps", "--wait", "--wait-timeout", "150", ...services);
  }
  console.log("BBB Demo is ready");
}

try {
  const root = process.env.BBB_DATA_ROOT;
  if (!root) throw new Error("Export BBB_DATA_ROOT before deploying");
  const lock = join(root, ".demo-deploy.lock");
  try {
    mkdirSync(lock, { mode: 0o700 });
  } catch (error) {
    if (error.code === "EEXIST") throw new Error("Another Demo deploy owns the lock");
    throw error;
  }
  try {
    await deploy(process.argv[2]);
  } finally {
    rmdirSync(lock);
  }
} catch (error) {
  console.error(error.code ? "Could not access the credential file or deploy environment" : error.message);
  process.exitCode = 1;
}
