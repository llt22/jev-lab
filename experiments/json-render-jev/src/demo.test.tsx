import assert from "node:assert/strict";
import test from "node:test";

import {
  catalog,
  composeDashboard,
  createTypeSafeEvaluator,
  offlineEvaluator,
} from "./demo.tsx";

test("composes a valid dashboard and renders it to HTML", async () => {
  const result = await composeDashboard(offlineEvaluator);

  assert.equal(result.complete.stopReason, "finish");
  assert.equal(result.complete.steps.length, 2);
  assert.equal(catalog.validate(result.spec).success, true);
  assert.match(result.html, /Operations overview/);
  assert.match(result.html, /Recent orders/);
  assert.match(result.html, /New customers/);
  assert.match(result.html, /Weekly revenue/);
});

test("preserves the requested section and metric order", async () => {
  const { html } = await composeDashboard(offlineEvaluator);

  assert.ok(html.indexOf("Recent orders") < html.indexOf("Key metrics"));
  assert.ok(html.indexOf("Key metrics") < html.indexOf("Weekly revenue"));
  assert.ok(html.indexOf("Revenue") < html.indexOf("Orders"));
  assert.ok(html.indexOf("Orders") < html.indexOf("New customers"));
});

test("adapts a TypeSafe choice response to the composer contract", async () => {
  const evaluate = createTypeSafeEvaluator("test-key", async (_input, init) => {
    const request = JSON.parse(String(init?.body));
    assert.equal(request.model, "jev-1.13.0");
    assert.deepEqual(Object.keys(request.questions), ["pick"]);
    return new Response(
      JSON.stringify({
        answers: {
          pick: { type: "choice", choice: "yes", confidence: 0.9 },
        },
        usage: { input_tokens: 42 },
      }),
    );
  });

  const result = await evaluate({
    state: { task: "test" },
    questions: {
      pick: {
        type: "choice",
        instructions: "Choose yes.",
        criteria: { yes: "Yes", no: "No" },
      },
    },
    signal: AbortSignal.timeout(1_000),
  });

  assert.deepEqual(result, {
    answers: { pick: { choice: "yes", confidence: 0.9 } },
    usage: { inputTokens: 42 },
  });
});
