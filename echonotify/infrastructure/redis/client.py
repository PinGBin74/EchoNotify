"""Redis клиенты для кэширования, сессий и блокировок."""

import json
from typing import Any, Optional

import msgpack
from redis.asyncio import ConnectionPool, Redis

from echonotify.infrastructure.redis.constants import (
    DEFAULT_TTL,
    REDIS_LOCK_TTL,
    REDIS_SESSION_TTL,
    SCAN_KEYS_COUNT,
)
from echonotify.settings import Settings


class BaseRedisClient:
    """Base Redis client with connection pooling and async/await support."""

    def __init__(
        self,
        settings: Settings,
        decode_responses: bool = False,
        max_connections: int = 20,
    ):
        """Initialize base Redis client with connection pooling."""
        self.settings = settings
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self._client: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None

    async def connect(self) -> Redis:
        """Establish Redis connection and create connection pool."""
        if self._client is None:
            self._pool = ConnectionPool(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                db=self.settings.REDIS_DB,
                decode_responses=self.decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=self.max_connections,
                socket_keepalive=True,
                socket_keepalive_options={},
            )

            self._client = Redis(connection_pool=self._pool)
            await self._client.ping()
        return self._client

    async def disconnect(self):
        """Close Redis connection and connection pool."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def health_check(self) -> bool:
        """Check Redis availability."""
        try:
            client = await self.connect()
            await client.ping()
            return True
        except Exception:
            return False

    async def scan_keys(
        self, pattern: str, count: int = SCAN_KEYS_COUNT
    ) -> list:
        """Get keys by pattern using SCAN (non-blocking)."""
        client = await self.connect()
        cursor = 0
        keys = []

        while True:
            cursor, batch_keys = await client.scan(
                cursor=cursor, match=pattern, count=count
            )
            keys.extend(batch_keys)

            if cursor == 0:
                break

        return keys


class RedisCache(BaseRedisClient):
    """Redis client for caching data with JSON serialization support."""

    def __init__(self, settings: Settings, default_ttl: int = DEFAULT_TTL):
        """Initialize cache client with default TTL."""
        super().__init__(settings, decode_responses=True)
        self.default_ttl = default_ttl

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True,
    ) -> bool:
        """Store value in cache with optional TTL."""
        client = await self.connect()

        if serialize:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)

        expire_time = ttl or self.default_ttl
        await client.setex(key, expire_time, value)
        return True

    async def get(
        self,
        key: str,
        deserialize: bool = True,
        default: Any = None,
    ) -> Any:
        """Retrieve value from cache with optional deserialization."""
        client = await self.connect()
        value = await client.get(key)

        if value is None:
            return default

        if deserialize:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        return value

    async def delete(self, *keys: str) -> int:
        """Delete multiple keys from cache."""
        client = await self.connect()
        return await client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await self.connect()
        return await client.exists(key)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for key."""
        client = await self.connect()
        result = await client.expire(key, ttl)
        return result

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        client = await self.connect()
        return await client.ttl(key)

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value by specified amount."""
        client = await self.connect()
        return await client.incrby(key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value by specified amount."""
        client = await self.connect()
        return await client.decrby(key, amount)


class RedisSession(BaseRedisClient):
    """Redis client for user sessions with msgpack serialization."""

    def __init__(
        self, settings: Settings, session_ttl: int = REDIS_SESSION_TTL
    ):
        """Initialize session client with TTL."""
        super().__init__(settings, decode_responses=False)
        self.session_ttl = session_ttl

    async def create_session(
        self,
        session_id: str,
        user_data: dict,
    ) -> bool:
        """Create new user session with msgpack serialization."""
        client = await self.connect()
        session_key = f"session:{session_id}"

        serialized_data = msgpack.packb(user_data, use_bin_type=True)
        await client.setex(
            session_key,
            self.session_ttl,
            serialized_data,
        )
        return True

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve user session and deserialize from msgpack."""
        client = await self.connect()
        session_key = f"session:{session_id}"

        data = await client.get(session_key)
        if data is None:
            return None

        try:
            return msgpack.unpackb(data, raw=False)
        except (msgpack.UnpackException, TypeError):
            return None

    async def update_session(
        self,
        session_id: str,
        user_data: dict,
    ) -> bool:
        """Update existing user session."""
        return await self.create_session(session_id, user_data)

    async def delete_session(self, session_id: str) -> bool:
        """Delete user session."""
        client = await self.connect()
        session_key = f"session:{session_id}"
        result = await client.delete(session_key)
        return result > 0

    async def refresh_session(self, session_id: str) -> bool:
        """Refresh session TTL."""
        client = await self.connect()
        session_key = f"session:{session_id}"
        result = await client.expire(session_key, self.session_ttl)
        return result

    async def is_session_valid(self, session_id: str) -> bool:
        """Check if session exists and is valid."""
        return await self.get_session(session_id) is not None


class RedisLock(BaseRedisClient):
    """Redis client for distributed locks."""

    def __init__(self, settings: Settings, lock_ttl: int = REDIS_LOCK_TTL):
        """Initialize lock client with default TTL."""
        super().__init__(settings)
        self.lock_ttl = lock_ttl

    async def acquire_lock(
        self,
        resource: str,
        identifier: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Acquire distributed lock for resource."""
        client = await self.connect()
        lock_key = f"lock:{resource}"
        expire_time = ttl or self.lock_ttl

        result = await client.set(
            lock_key,
            identifier,
            ex=expire_time,
            nx=True,
        )
        return result is not None

    async def release_lock(
        self,
        resource: str,
        identifier: str,
    ) -> bool:
        """Release distributed lock using Lua script."""
        client = await self.connect()
        lock_key = f"lock:{resource}"

        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        result = await client.eval(lua_script, 1, lock_key, identifier)
        return result == 1

    async def extend_lock(
        self,
        resource: str,
        identifier: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Extend distributed lock TTL."""
        client = await self.connect()
        lock_key = f"lock:{resource}"
        expire_time = ttl or self.lock_ttl

        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        result = await client.eval(
            lua_script, 1, lock_key, identifier, expire_time
        )
        return result == 1


def get_redis_cache(settings: Settings) -> RedisCache:
    """Factory function to create Redis cache client."""
    return RedisCache(settings)


def get_redis_session(settings: Settings) -> RedisSession:
    """Factory function to create Redis session client."""
    return RedisSession(settings)


def get_redis_lock(settings: Settings) -> RedisLock:
    """Factory function to create Redis lock client."""
    return RedisLock(settings)
