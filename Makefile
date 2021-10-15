run-all:
	@make run-lint-check
	@make run-type-check
	@make run-tests
	@make make-docs

run-lint-check:
	poetry run flake8 timequota --count --show-source --statistics --config flake8.cfg

run-type-check:
	poetry run mypy timequota --ignore-missing-imports

run-tests:
	poetry run pytest --cov-report term-missing --black --cov=tests/

make-docs:
	poetry run pdoc --html --force --output-dir docs timequota/timequota.py --template-dir docs/config
