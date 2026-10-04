# Evaluation (SerpApi ablation)

Offline mini set: `backend/eval/tests-mini.jsonl` (synthetic rows only).

```bash
cd backend
python -m eval.run --set tests-mini --mode replay --out eval/report.json
```

Arms (future labelled runs): A = `SERPAPI_SCOPE=off`, B = +`google_scholar`, C = +cite, D = +author.

Report metrics include Wilson 95% intervals where sample size allows. Do not cite numbers in the README unless they appear in `eval/report.json` from a committed run.
