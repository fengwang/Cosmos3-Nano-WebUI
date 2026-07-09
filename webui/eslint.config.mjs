import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { FlatCompat } from "@eslint/eslintrc";

// eslint 9 flat config bridging Next 15's eslintrc-style shareable config.
const compat = new FlatCompat({
  baseDirectory: dirname(fileURLToPath(import.meta.url)),
});

const config = [
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts", "lib/api/schema.d.ts"] },
  ...compat.extends("next/core-web-vitals"),
];

export default config;
