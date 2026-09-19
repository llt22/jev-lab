import {
  defineCatalog,
  experimental_composeSpec,
  experimental_createEvaluator,
  type Experimental_CompositionCandidate,
  type Experimental_CompositionEvaluator,
  type Experimental_CompositionEvent,
  type Spec,
} from "@json-render/core";
import {
  defineRegistry,
  JSONUIProvider,
  Renderer,
} from "@json-render/react";
import { schema } from "@json-render/react/schema";
import { renderToStaticMarkup } from "react-dom/server";
import { z } from "zod";

export const PROMPT =
  "Generate an operations dashboard with the recent orders table first, " +
  "then revenue, orders, and new-customer metrics in one row, followed by weekly revenue.";

export const catalog = defineCatalog(schema, {
  components: {
    Dashboard: {
      props: z.object({ title: z.string() }),
      slots: ["default"],
    },
    MetricRow: {
      props: z.object({ label: z.string() }),
      slots: ["default"],
    },
    Metric: {
      props: z.object({ label: z.string(), value: z.string() }),
    },
    OrdersTable: {
      props: z.object({
        title: z.string(),
        rows: z.array(
          z.object({ id: z.string(), customer: z.string(), total: z.string() }),
        ),
      }),
    },
    RevenueBars: {
      props: z.object({
        title: z.string(),
        points: z.array(z.object({ day: z.string(), value: z.number() })),
      }),
    },
  },
  actions: {},
});

export const candidates = [
  {
    id: "dashboard",
    description: "Operations dashboard shell",
    element: { type: "Dashboard", props: { title: "Operations overview" } },
  },
  {
    id: "ordersTable",
    description: "Recent orders table with customer and total",
    root: false,
    element: {
      type: "OrdersTable",
      props: {
        title: "Recent orders",
        rows: [
          { id: "A-1042", customer: "Northstar", total: "$840" },
          { id: "A-1041", customer: "Acme", total: "$620" },
        ],
      },
    },
  },
  {
    id: "metricRow",
    description: "Horizontal row grouping the requested metrics",
    root: false,
    element: { type: "MetricRow", props: { label: "Key metrics" } },
  },
  {
    id: "revenueMetric",
    description: "Revenue metric",
    root: false,
    element: { type: "Metric", props: { label: "Revenue", value: "$24.8k" } },
  },
  {
    id: "ordersMetric",
    description: "Orders metric",
    root: false,
    element: { type: "Metric", props: { label: "Orders", value: "184" } },
  },
  {
    id: "customersMetric",
    description: "New customers metric",
    root: false,
    element: { type: "Metric", props: { label: "New customers", value: "31" } },
  },
  {
    id: "weeklyRevenue",
    description: "Weekly revenue bar chart",
    root: false,
    element: {
      type: "RevenueBars",
      props: {
        title: "Weekly revenue",
        points: [
          { day: "Mon", value: 3200 },
          { day: "Tue", value: 4100 },
          { day: "Wed", value: 3700 },
        ],
      },
    },
  },
] satisfies Experimental_CompositionCandidate[];

const selectedCandidateIds = new Set(candidates.map(({ id }) => id));

function elementDescription(state: Record<string, unknown>, questionName: string) {
  const id = questionName.replace(/^(parent|order)_/, "");
  const elements = Array.isArray(state.selected_elements) ? state.selected_elements : [];
  const element = elements.find(
    (entry): entry is { id: string; content: string } =>
      typeof entry === "object" &&
      entry !== null &&
      "id" in entry &&
      entry.id === id &&
      "content" in entry &&
      typeof entry.content === "string",
  );
  return element?.content ?? "";
}

function offlineChoice(
  state: Record<string, unknown>,
  name: string,
  criteria: Record<string, string>,
) {
  if (name === "root") return "dashboard";
  if (name.startsWith("select_")) {
    const selected = Object.keys(criteria).find(
      (key) => key.startsWith("use:") && selectedCandidateIds.has(key.slice(4)),
    );
    return selected ?? "omit";
  }

  const description = elementDescription(state, name).toLowerCase();
  if (name.startsWith("parent_")) {
    const parentDescription = description.includes("metric")
      ? "horizontal row"
      : "dashboard shell";
    return (
      Object.entries(criteria).find(([, value]) =>
        value.toLowerCase().includes(parentDescription),
      )?.[0] ?? Object.keys(criteria)[0]
    );
  }

  const order = description.includes("recent orders")
    ? "1"
    : description.includes("horizontal row")
      ? "2"
      : description.includes("weekly revenue")
        ? "3"
        : description === "revenue metric"
          ? "1"
          : description === "orders metric"
            ? "2"
            : "3";
  return Object.hasOwn(criteria, order) ? order : Object.keys(criteria)[0];
}

export const offlineEvaluator: Experimental_CompositionEvaluator = async ({
  state,
  questions,
}) => ({
  answers: Object.fromEntries(
    Object.entries(questions).map(([name, question]) => [
      name,
      {
        choice: offlineChoice(state, name, question.criteria),
        confidence: 1,
      },
    ]),
  ),
  usage: { inputTokens: 0 },
});

const TYPESAFE_API_URL = "https://api.typesafe.ai/v1/systemone";
const TYPESAFE_MODEL = "jev-1.13.0";
const typesafeResponseSchema = z.object({
  answers: z.record(
    z.string(),
    z.object({
      type: z.literal("choice"),
      choice: z.string(),
      confidence: z.number().min(0).max(1).optional(),
    }),
  ),
  usage: z.object({ input_tokens: z.number().int().nonnegative().optional() }).optional(),
});

export function createTypeSafeEvaluator(
  apiKey: string,
  fetchImpl: typeof fetch = fetch,
): Experimental_CompositionEvaluator {
  const key = apiKey.trim();
  if (!key) throw new Error("A TypeSafe API key is required.");
  return async ({ state, questions, signal }) => {
    const response = await fetchImpl(TYPESAFE_API_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        "User-Agent": "jev-lab-json-render/1.0",
      },
      body: JSON.stringify({ model: TYPESAFE_MODEL, state, questions }),
      signal,
    });
    if (!response.ok) {
      const detail = (await response.text()).slice(0, 300);
      throw new Error(
        `TypeSafe evaluation failed (HTTP ${response.status})${detail ? `: ${detail}` : "."}`,
      );
    }
    const parsed = typesafeResponseSchema.safeParse(await response.json());
    if (!parsed.success)
      throw new Error("TypeSafe evaluation returned an invalid response.");
    return {
      answers: Object.fromEntries(
        Object.entries(parsed.data.answers).map(([name, answer]) => [
          name,
          { choice: answer.choice, confidence: answer.confidence },
        ]),
      ),
      usage: { inputTokens: parsed.data.usage?.input_tokens },
    };
  };
}

const { registry } = defineRegistry(catalog, {
  components: {
    Dashboard: ({ props, children }) => (
      <main data-component="dashboard">
        <h1>{props.title}</h1>
        {children}
      </main>
    ),
    MetricRow: ({ props, children }) => (
      <section data-component="metric-row" aria-label={props.label}>
        {children}
      </section>
    ),
    Metric: ({ props }) => (
      <article data-component="metric">
        <strong>{props.value}</strong>
        <span>{props.label}</span>
      </article>
    ),
    OrdersTable: ({ props }) => (
      <section data-component="orders-table">
        <h2>{props.title}</h2>
        <table>
          <tbody>
            {props.rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.customer}</td>
                <td>{row.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    ),
    RevenueBars: ({ props }) => (
      <section data-component="revenue-bars">
        <h2>{props.title}</h2>
        <ol>
          {props.points.map((point) => (
            <li key={point.day}>{`${point.day}: ${point.value}`}</li>
          ))}
        </ol>
      </section>
    ),
  },
});

export function renderSpec(spec: Spec) {
  return renderToStaticMarkup(
    <JSONUIProvider registry={registry} initialState={spec.state ?? {}}>
      <Renderer spec={spec} registry={registry} />
    </JSONUIProvider>,
  );
}

export async function composeDashboard(evaluate: Experimental_CompositionEvaluator) {
  const events: Experimental_CompositionEvent[] = [];
  for await (const event of experimental_composeSpec({
    catalog,
    candidates,
    prompt: PROMPT,
    evaluate,
    maxSteps: 4,
    maxElements: 8,
    maxDepth: 3,
    signal: AbortSignal.timeout(30_000),
    instructions: {
      root: "Use the dashboard shell for dashboard requests.",
      next: "Include only the table, three requested metrics, their row, and weekly chart.",
      parent: "Put metrics in the metric row; put the table, metric row, and chart in the dashboard.",
    },
  })) {
    events.push(event);
  }
  const complete = events.at(-1);
  if (complete?.type !== "complete" || !complete.spec)
    throw new Error("Composition did not produce a complete spec.");
  return { events, complete, spec: complete.spec, html: renderSpec(complete.spec) };
}

async function main() {
  const gateway = process.argv.includes("--gateway") || process.argv.includes("--live");
  const typesafe = process.argv.includes("--typesafe");
  if (gateway && typesafe) throw new Error("Choose either --gateway or --typesafe.");
  const mode = gateway ? "gateway" : typesafe ? "typesafe" : "offline";
  const gatewayKey = process.env.AI_GATEWAY_API_KEY?.trim();
  const typesafeKey = process.env.TYPESAFE_API_KEY?.trim();
  if (gateway && !gatewayKey)
    throw new Error("AI_GATEWAY_API_KEY is required for --gateway.");
  if (typesafe && !typesafeKey)
    throw new Error("TYPESAFE_API_KEY is required for --typesafe.");
  const evaluate = gateway
    ? experimental_createEvaluator({ model: "typesafe-ai/jev", apiKey: gatewayKey! })
    : typesafe
      ? createTypeSafeEvaluator(typesafeKey!)
      : offlineEvaluator;
  const result = await composeDashboard(evaluate);
  console.log(
    JSON.stringify(
      {
        mode,
        model: gateway ? "typesafe-ai/jev" : typesafe ? TYPESAFE_MODEL : null,
        prompt: PROMPT,
        stopReason: result.complete.stopReason,
        elapsedMs: result.complete.elapsedMs,
        inputTokens: result.complete.inputTokens,
        decisions: result.complete.steps.map((step) => ({
          phase: step.choice,
          elapsedMs: step.elapsedMs,
          answers: step.answers,
        })),
        spec: result.spec,
        html: result.html,
      },
      null,
      2,
    ),
  );
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
}
