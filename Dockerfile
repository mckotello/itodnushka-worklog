FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir \
    "fastapi>=0.116,<1.0" \
    "uvicorn[standard]>=0.35,<1.0" \
    "sqlalchemy>=2.0,<3.0" \
    "asyncpg>=0.30,<1.0" \
    "pydantic-settings>=2.10,<3.0" \
    "alembic>=1.16,<2.0" \
    "pwdlib[argon2]>=0.2,<1.0" \
    "email-validator>=2.2,<3.0" \
    "PyJWT>=2.10,<3.0" \
    "pytest>=8.4,<9.0" \
    "pytest-asyncio>=1.1,<2.0" \
    "httpx>=0.28,<1.0"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]