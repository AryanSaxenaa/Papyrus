.PHONY: test secret-scan demo eval

test:
	cd backend && python -m pytest -q

secret-scan:
	python backend/scripts/secret_scan.py

demo:
	@echo "Start lite replay: PAPYRUS_MODE=replay docker compose --profile lite up"

eval:
	cd backend && python -m eval.run --set tests-mini --mode replay --out eval/report.json
