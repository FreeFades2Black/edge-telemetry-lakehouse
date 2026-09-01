.PHONY: init lint test plan localstack run-local clean

init:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

lint:
	ruff check src/ tests/
	mypy src/

test:
	pytest tests/ -v --tb=short

plan:
	cd terraform && terraform init -backend=false && terraform validate

localstack-up:
	docker-compose up -d localstack

localstack-down:
	docker-compose down

run-local:
	python -c "from src.processing.delta_lakehouse import EdgeTelemetryLakehousePipeline; p = EdgeTelemetryLakehousePipeline(); print(p.run_bronze_ingestion(300)); print(p.run_silver_processing()); print(p.run_gold_aggregation())"

replay-benchmarks:
	python -c "from src.ingestion.revolver_replay import HistoricalTelemetryReplay; [print(f) for f in HistoricalTelemetryReplay('nasa_cmapss').stream_records(limit=5)]"

run-historical:
	python -c "from src.processing.delta_lakehouse import EdgeTelemetryLakehousePipeline; p = EdgeTelemetryLakehousePipeline(); print(p.run_historical_benchmark_replay('nasa_cmapss', 50)); print(p.run_silver_processing()); print(p.run_gold_aggregation())"

clean:
	rm -rf .pytest_cache data/bronze/*.json data/silver/*.json data/gold/*.json
