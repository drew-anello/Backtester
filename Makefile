install:
	pip install -r requirements.txt

run-demo:
	python scripts/run_demo.py

test:
	pytest -q
