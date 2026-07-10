# OSH & Security fixtures

> **Note:** The API data in this directory is **fake**. These JSON files are hand-built/synthetic
> stand-ins for the Sigrid OSH and Security endpoints — they are **not** captured from the live
> Sigrid API and do not represent real analysis results for any customer.

## Why these exist

The Sigrid OSH and Security **ratings** and **findings** endpoints (`osh-findings`,
`security-findings`, `model-ratings?feature=SECURITY`) now return real-time data — a newly discovered
vulnerability appears in the response immediately. That makes the golden-file integration suite
(`test_report_generation.py`) non-deterministic for any preset containing OSH/Security content.

To restore determinism, the integration test replays these fixtures for those volatile endpoints
instead of calling the live API. All other (date-parameterized) endpoints still run against live data.

## Regenerating

These fixtures are produced by `build_fake_fixtures.py`. Re-run it to (re)generate the files, then
regenerate the affected `reference_*.pptx` golden files so they match.
