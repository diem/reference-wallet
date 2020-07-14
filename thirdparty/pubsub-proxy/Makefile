test:
	pytest -s tests

lint:
	bandit -r pubsub_proxy setup.py
	black pubsub_proxy tests examples setup.py
	flake8 --ignore E501,W503 pubsub_proxy tests examples setup.py

typecheck:
	mypy pubsub_proxy --ignore-missing-imports --strict

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache
