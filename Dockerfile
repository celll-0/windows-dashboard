FROM python:3.12-alpine
WORKDIR /app

# Create store file as root user before switching to non-root
RUN touch ./store.json

# create a non-root user to run the application
RUN adduser -D -u 1001 -s /bin/sh app
RUN chown app:app ./store.json
USER app

RUN pip install --user --no-cache-dir "poetry==2.4.1"
ENV PATH="/home/app/.local/bin:$PATH"

COPY pyproject.toml poetry.lock ./
RUN poetry install --only services,shared --no-root

COPY --chown=app:app dash-services/dash/ ./dash/
COPY --chown=app:app dash-services/scripts/ ./scripts/
COPY --chown=app:app dash-services/logging_conf.py ./logging_conf.py
COPY --chown=app:app dash-services/main.py ./main.py
# Copy the installed dependencies from the build stage
RUN poetry install --only services,shared

COPY --chown=app:app logging.yml ./
COPY --chown=app:app utils/ ./utils/

CMD ["poetry", "run", "python", "main.py"]