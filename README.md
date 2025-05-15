# Overview
Confspec is a configuration loading library for Python that supports smart environment variable interpolation at runtime.

It provides a simple way to load configuration from common formats like `YAML`, `JSON`, and `TOML`, while being easy
to add support for any additional formats. Out-of-the-box, confspec supports parsing application configuration
into Pydantic models, or Msgspec Structs.

The environment variable interpolation syntax allows you to keep your defaults in the configuration file, while
still being able to override them from a deployment environment.

## Installation
Confspec is available on PyPI and can be installed using your package manager of choice.

```bash
pip install confspec
```
```bash
uv add confspec
```

## Usage
`config.toml`
```toml
[server]
port = "${PORT:8080}"
debug = "${DEBUG:false}"

[database]
url = "postgres://${DB_URL:postgres:postgres@localhost:5432}/postgres"

[logging]
level = "${LOG_LEVEL~:INFO}"
handlers = "${LOG_HANDLERS[,]:console,file}"

[features]
enabled = "${FEATURE_FLAGS[,]:auth,metrics,caching}"
```

The above configuration file can easily be loaded, with any environment substitution happening automatically.
```python
>>> import confspec
>>> confspec.load("config.toml")
{
    "server": {
        "port": "8080",
        "debug": "false"
    },
    "database": {
        "url": "postgres://postgres:postgres@localhost:5432/postgres"
    },
    "logging": {
        "level": "INFO",
        "handlers": ["console", "file"]
    },
    "features": {
        "enabled": ["auth", "metrics", "caching"]
    }
}
```

Or if you wanted it to be loaded into a msgspec Struct object. Note that msgspec will coerce some fields
into the requested types automatically, unless you pass `strict=True`.
```python
>>> import confspec
>>> import msgspec

>>> class Server(msgspec.Struct):
...    port: int
...    debug: bool

>>> class Database(msgspec.Struct):
...    url: str

>>> class Logging(msgspec.Struct):
...    level: str
...    handlers: list[str]

>>> class Features(msgspec.Struct):
...    enabled: list[str]

>>> class Config(msgspec.Struct):
...    server: Server
...    database: Database
...    logging: Logging
...    features: Features

>>> confspec.load("config.toml", cls=Config)
Config(
    server=Server(port=8080, debug=False),
    database=Database(url='postgres://postgres:postgres@localhost:5432/postgres'),
    logging=Logging(level='INFO', handlers=['console', 'file']),
    features=Features(enabled=['auth', 'metrics', 'caching'])
)
```

## Issues
If you find any bugs, issues, or unexpected behaviour while using the library, you should open an issue with
details of the problem and how to reproduce if possible. Please also open an issue for any new features
you would like to see added.

## Contributing
Pull requests are welcome. For major changes, please open an issue/discussion first to discuss what you
would like to change.

Please try to ensure that documentation is updated if you add any features accessible through the public API.

If you use this library and like it, feel free to sign up to GitHub and star the project, it is greatly appreciated
and lets me know that I'm going in the right direction!

## Links
- **License:** [MIT](https://choosealicense.com/licenses/mit/)
- **Repository:** [GitHub](https://github.com/tandemdude/confspec)
