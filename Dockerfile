FROM python:3.12-alpine as builder

RUN pip install --upgrade pip && \
    pip install pdm --no-cache-dir

COPY pdm.lock pyproject.toml ./
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


FROM python:3.12-alpine as app

WORKDIR /app/
ENV PYTHONPATH=/pkgs
COPY --from=builder /__pypackages__/3.12/lib /pkgs
COPY --from=builder /__pypackages__/3.12/bin/* /bin/

FROM app as bot

COPY src/bot .
CMD ["python", "main.py"]

FROM app as monitoring

COPY src/monitoring .
CMD ["python", "main.py"]