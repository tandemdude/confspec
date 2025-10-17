# Overview
Confspec is a configuration loading library for Python that supports smart environment variable interpolation at runtime.

It provides a simple way to load configuration from common formats like `YAML`, `JSON`, and `TOML`, while being easy
to add support for any additional formats. Out-of-the-box, confspec also supports parsing application configuration
into Pydantic models, or Msgspec Structs.

The environment variable interpolation syntax allows you to keep your defaults in the configuration file, while
still being able to override them from a deployment environment.

Confspec also supports environment-based configuration overrides, allowing you to maintain separate configuration
files for different environments (akin to spring's application.properties) without duplicating your entire
configuration.

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

## Interpolation Syntax

- `${VAR}`
  - replaced with the value of the `VAR` environment variable
  - if `VAR` is unset during interpolation, a `KeyError` will be raised
- `${VAR:default}`
  - replaced with the value of the `VAR` environment variable
  - if `VAR` is unset during interpolation, the default value will be used instead
- `${VAR[,]}`
  - performs list expansion on the value of the `VAR` environment variable, splitting on the delimiter (in this case `,`)
  - the delimiter can be any combination of one or more characters, excluding `]` and `}`
  - this operator cannot be applied to patterns within a longer string
- `${VAR~}`
  - strips whitespace from the value of the `VAR` environment variable (or the default if one is specified)
  - if combined with list expansion, each individual element will have its whitespace stripped
- `${VAR?}`
  - replaced with the value of the `VAR` environment variable
  - if `VAR` is unset during interpolation, it will be replaced with Python's `None` instead
  - this operator cannot be applied to patterns within a longer string

Most of these interpolation rules can be combined, except for a default value and the "None as default" flag.

For example:

- `${VAR[,]~:default}` - valid
- `${VAR[,]~?}` - valid
- `${VAR[,]~?:default}` - invalid

> [!NOTE]
> The order that the flags are written is important, as the interpolation syntax is parsed using regex. You should
> always specify the flags in the same order as the valid expressions shown above.

## Environment-specific Configurations

When an environment is specified, Confspec automatically looks for an additional file matching the base
configuration name with the environment suffix and merges it with the base configuration.

For example:
```bash
config.yaml
config.prod.yaml
config.dev.yaml
```

You can activate an additional environment in two ways:
```python
import confspec

# Explicitly pass the environment
config = confspec.load("config.yaml", env="prod")

# Or use the CONFSPEC_ENV environment variable
# export CONFSPEC_ENV=prod
config = confspec.load("config.yaml")
```

In both cases, config.prod.yaml will be loaded and merged with config.yaml, allowing you to override specific values
for that environment while keeping shared defaults in one place. Any values specified in the environment-specific
config file will override those specified within the root configuration file.

Environment variable interpolations are performed after the configurations have been merged.

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
