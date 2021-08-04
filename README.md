# Flake518

A small wrapper around the famous [flake8](https://flake8.pycqa.org/) tool empowering it to read
the configuration not from `setup.cfg`, `tox.ini` or `.flake8`, but from the [PEP518](https://www.python.org/dev/peps/pep-0518/)
compliant `pyproject.toml`.

In contrast to [flake9](https://gitlab.com/retnikt/flake9) it is not a fork of flake8. It uses flake8 under the hood and transforms
the relevant configuration to a flake8 configuration file. This way, the ongoing implementation of flake8 can be used.

## Rational

The usage of `pyproject.toml` is though highly anticipated by some community members, but currently [rejected](https://github.com/PyCQA/flake8/issues/234) by the maintainers for an undisclosed reason. Flake9 already uses the `pyproject.toml` file, but does not incorporate later changes.

Since flake8 allows to pass additional configuration files, a temporary configuration file is created. This way, the latest flake8 revision is used, but it can be configured using `pyproject.toml`.

## Configuration

According to PEP518, each tool may add a tool-specific table to the project configuration.

```toml
[tool.flake8]
statistics=True
show-source=True
max-line-length=79
doctests=True
exclude=[".git", "__pypackages__", ".vscode", ".mypy_cache"]
```

For compliance reason, the `[tool.flake518]` can be used as well.

## License

Like flake8, this project is licensed under the MIT license.

## Contributions

Contributions welcome, feel free to submit issues and pull requests on github.
Contact me, if you are using gitlab or codeberg.
