FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app/src
ENV PYTHONIOENCODING=utf-8

COPY src/ ./src/
COPY examples/ ./examples/
COPY .ai-pr-review.yml README.md ./

ENTRYPOINT ["python", "-m", "ai_pr_review_agent.cli"]
