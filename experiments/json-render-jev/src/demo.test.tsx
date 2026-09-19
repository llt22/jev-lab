import assert from "node:assert/strict";
import test from "node:test";

import { catalog, composeDashboard, offlineEvaluator } from "./demo.tsx";

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
