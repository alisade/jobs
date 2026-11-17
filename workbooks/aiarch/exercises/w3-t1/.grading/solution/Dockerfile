# Lighthouse helpdesk agent image for AgentCore Runtime.
FROM python:3.12-slim
WORKDIR /app
RUN useradd --uid 10001 --create-home agent
COPY agent/ /app/agent/
USER 10001
EXPOSE 8080
CMD ["python", "-m", "agent.server"]
