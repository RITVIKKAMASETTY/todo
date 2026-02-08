# Redis Microservice

This is the Redis service for the Chess Backend, running as a separate microservice.

## Quick Start

```bash
# Start Redis
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f redis

# Stop Redis
docker-compose down
```

## Connection Details

| Setting | Value |
|---------|-------|
| Host | `localhost` (or container IP) |
| Port | `6379` |
| Password | None (add in production) |

## For Production

1. Set a password in `redis.conf`:
   ```
   requirepass your_secure_password
   ```

2. Update backend `.env`:
   ```
   REDIS_HOST=your-redis-server-ip
   REDIS_PORT=6379
   REDIS_PASSWORD=your_secure_password
   ```

## Data Persistence

Redis data is stored in a Docker volume `redis_data`. To backup:
```bash
docker run --rm -v chess-redis_redis_data:/data -v $(pwd):/backup alpine tar cvf /backup/redis-backup.tar /data
```
