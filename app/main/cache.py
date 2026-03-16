import redis.asyncio as aioredis

from app.settings import settings

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS.url, decode_responses=True
)


async def set_email_code(email: str, code: str, ttl_seconds: int) -> None:
    await redis_client.set(f"email_confirm:{email}", code, ex=ttl_seconds)


async def get_email_code(email: str) -> str | None:
    return await redis_client.get(f"email_confirm:{email}")


async def delete_email_code(email: str) -> None:
    await redis_client.delete(f"email_confirm:{email}")
