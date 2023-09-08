FROM python:3.11-alpine as builder

RUN pip install --upgrade pip && \
    pip install pdm --no-cache-dir

COPY pdm.lock pyproject.toml ./
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


FROM python:3.11-alpine as app

WORKDIR /app/
ENV PYTHONPATH=/app/pkgs
COPY --from=builder /__pypackages__/3.11/lib pkgs

FROM app as client
COPY src/client .

FROM app as server
COPY src/server .
