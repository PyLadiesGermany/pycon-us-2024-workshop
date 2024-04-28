FROM python:3.11-slim-bullseye

RUN apt-get -y update && apt-get -y install gcc 

RUN pip install poetry

COPY ./pyproject.toml /
COPY ./poetry.lock /
RUN poetry install

COPY ./app /python_server

WORKDIR /python_server
EXPOSE 8001
CMD ["poetry", "run", "python", "main.py"]
