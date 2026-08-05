.PHONY: install test serve docker clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

serve:
	uvicorn service.app:app --reload

docker:
	docker build -f service/Dockerfile -t vyuha .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist *.egg-info .pytest_cache
