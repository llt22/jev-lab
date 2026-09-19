# json-render + Jev experiment

This experiment exercises the official `@json-render/core@0.21.0` composition
API with an app-owned dashboard catalog. It verifies the full local path:

1. an evaluator selects from bounded candidates;
2. `experimental_composeSpec` assembles and validates a flat Spec;
3. `@json-render/react` renders the Spec to HTML.

The default evaluator is deterministic so the integration remains testable
without credentials. Live modes replace only that evaluator: `demo:gateway`
uses the official Vercel AI Gateway adapter, while `demo:typesafe` calls the
TypeSafe System One API directly. The catalog, candidates, composer, validation,
and renderer remain identical.

```sh
cd experiments/json-render-jev
npm install
npm test
npm run demo

# Live Jev evaluation through TypeSafe (loads ../../.env when present)
npm run demo:typesafe

# Or use the official Vercel AI Gateway adapter
AI_GATEWAY_API_KEY=... npm run demo:gateway
```

Do not expose the Gateway key to browser code. The live model selects prepared
components and layout relationships; it does not generate props, business
data, actions, or arbitrary JSON.
