# Contributing to Jev Lab

Independent replications, counterexamples, and datasets make this repository more useful. Small, evidence-backed contributions are preferred over broad claims.

## Ways to contribute

- Share a Jev benchmark through the [benchmark result form](https://github.com/llt22/jev-lab/issues/new?template=benchmark-result.yml).
- Add cases to an existing dataset under `evals/` with a clear expected result.
- Add a reproducible evaluator or comparison under `scripts/`.
- Correct a report with a primary source or raw artifact.
- Report an API behavior change, including the exact model version and observation date.

## Reproducing the current work

Run the offline test suite before changing code:

```sh
python3 -m unittest discover -s tests
```

Scripts that call the TypeSafe API read `TYPESAFE_API_KEY` from the environment or local `.env` file. Never include API keys, tokens, customer data, or other secrets in issues, fixtures, artifacts, or commits.

## Pull requests

Keep a pull request focused on one experiment or correction. Include:

1. The question or claim being tested.
2. The dataset and model version.
3. The exact reproduction command.
4. Raw machine-readable output under `artifacts/` when practical.
5. A short interpretation that separates measured results from assumptions.

For code changes, add or update the relevant unit tests. For documentation corrections, link the primary source and state its capture date.

Generated artifacts must not silently replace previous evidence. Use a new filename when the model, dataset, or observation date changes.

## Result quality

Avoid presenting small synthetic datasets as production accuracy. Report failures and negative results, record retries and errors, and distinguish end-to-end latency from provider-reported model latency.
