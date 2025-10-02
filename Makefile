install:
	pip install -r requirements.txt

run-demo:
	PYTHONPATH=. python scripts/run_demo.py

test:
	pytest -q
