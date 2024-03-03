deps:
	poetry install

dev: deps
	cd app && poetry run python main.py

codecarbon-init:
	poetry run codecarbon init

codecarbon-monitor:
	poetry run codecarbon monitor --no-api

codecarbon-report:
	poetry run carbonboard --filepath="app/emissions.csv" --port=3333

lint: lint-black lint-flake lint-pycodestyle

lint-black:
	poetry run black --line-length 100 app

lint-flake:
	poetry run flake8 --max-line-length 100 app

lint-pycodestyle:
	poetry run pycodestyle --max-line-length 100 ./app
