FROM python:3.12-alpine as builder

RUN pip install --upgrade pip && \
    pip install pdm --no-cache-dir

COPY pdm.lock pyproject.toml ./
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


FROM python:3.12-alpine

WORKDIR /app/
ENV PYTHONPATH=/pkgs
COPY --from=builder /__pypackages__/3.12/lib /pkgs
COPY --from=builder /__pypackages__/3.12/bin/* /bin/

COPY src/bot .
CMD ["python", "main.py"]