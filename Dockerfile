FROM python:3.12-alpine
WORKDIR /app

# create a non-root user to run the application
RUN adduser -D -u 1001 -s /bin/sh app
RUN chown app:app /app
USER app

RUN pip install --user --no-cache-dir "poetry==2.4.1"
ENV PATH="/home/app/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only services,shared --no-root

COPY --chown=app:app daily_brief/src/dbrief/ ./dbrief/
COPY --chown=app:app daily_brief/logging_conf.py ./logging_conf.py
COPY --chown=app:app daily_brief/main.py ./main.py
# Copy the installed dependencies from the build stage
RUN poetry install --only services,shared

COPY --chown=app:app logging.yml ./
COPY --chown=app:app utils/ ./utils/

CMD ["poetry", "run", "python", "main.py"]