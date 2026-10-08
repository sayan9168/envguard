"""Example schema for a typical web service.

Usage:
    export DATABASE_URL=postgres://user:pass@db:5432/app
    export SUPPORT_EMAIL=support@example.com
    python examples/web_service_schema.py
"""

from envguard import Field, Schema

schema = Schema({
    "DATABASE_URL": Field.url(required=True, secret=True,
                              description="Primary database connection string"),
    "REDIS_URL": Field.url(default="redis://localhost:6379/0",
                           description="Cache and queue broker"),
    "PORT": Field.int(default=8000, min_value=1, max_value=65535,
                      description="HTTP listen port"),
    "DEBUG": Field.bool(default=False, description="Enable debug mode"),
    "LOG_LEVEL": Field.enum(["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"),
    "ALLOWED_HOSTS": Field.list_of("str", default=["localhost"]),
    "SUPPORT_EMAIL": Field.email(required=True),
    "WORKER_CONCURRENCY": Field.int(default=4, min_value=1, max_value=64),
})

if __name__ == "__main__":
    config = schema.load()
    print("Validated configuration:")
    for key, value in config.as_dict().items():
        print(f"  {key} = {value!r}")
