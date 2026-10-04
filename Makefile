.PHONY: test secret-scan demo eval bundle-verify freeze

test:
	cd backend && python -m pytest -q

secret-scan:
	python backend/scripts/secret_scan.py

demo:
	@echo "Start lite replay: PAPYRUS_MODE=replay docker compose --profile lite up"

eval:
	cd backend && python -m eval.run --set tests-mini --mode replay --out eval/report.json

bundle-verify:
	cd backend && python -m pytest tests/test_bundle.py -q

freeze:
	cd backend && python scripts/freeze_fixtures.py --set demo-a
