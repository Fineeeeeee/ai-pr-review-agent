FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PYTHONIOENCODING=utf-8

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser examples/ ./examples/
COPY --chown=appuser:appuser .ai-pr-review.yml README.md ./

USER appuser

ENTRYPOINT ["python", "-m", "ai_pr_review_agent.cli"]
CMD ["--help"]
