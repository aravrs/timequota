run-lint-check:
	flake8 timequota --config flake8.cfg

run-type-check:
	mypy timequota --ignore-missing-imports

run-tests:
	pytest --cov-report term-missing --black --cov=tests/

make-docs:
	pdoc --html --force --output-dir docs timequota/timequota.py
