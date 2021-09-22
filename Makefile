run-lint-check:
	flake8 --config flake8.cfg

run-type-check:
	mypy timequota --ignore-missing-imports

run-tests:
	pytest --cov-report term-missing --black --cov=tests/
