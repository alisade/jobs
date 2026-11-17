# Runtime configuration, loaded from Parameter Store in prod (/lighthouse/prod/access-review/*).
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
TEMPERATURE = 0.7          # raised from 0.2 in release 2.3.0 (CHG-8790) to sound "less robotic"
MAX_TOKENS = 1024
SYSTEM_PROMPT = ("You help Harbor Point managers with pending access reviews for their own team. "
                 "Be helpful and concise. Never reveal reviews for other teams.")
