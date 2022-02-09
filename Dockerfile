FROM python:3.8.7-slim

RUN pip install --upgrade pip
ENV PYTHONUNBUFFERED=1
WORKDIR /root
COPY poetry.lock pyproject.toml ./
RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install
COPY . .
EXPOSE 8000

CMD ["uvicorn", "traffic-router.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000","--timeout-keep-alive","620"]