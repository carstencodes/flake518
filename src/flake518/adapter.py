# adapter.py
#
# Part of Flake518
#
# Copyright (c) 2021 Carsten Igel
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software")
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the
# next paragraph) shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Adapter unit.

Tries to locate and read the pyproject.toml.
The configuration section is written to a temporary
file which is passed as additional config file to flake8.
"""

import logging
import os
import sys
from configparser import RawConfigParser
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, TextIO

from flake8.main.cli import main as run_flake8
from toml import load as load_toml

# Python 3.9 enforces list over List
# In this order, the linter will get it straight
if sys.version_info.major == 3 and sys.version_info.minor < 9:
    from typing import List as _List
else:
    _List = list

PY_PROJECT_TOML = "pyproject.toml"
TOOL = "tool"
FLAKE_SECTIONS = ("flake8", "flake518")


def _get_log_level() -> int:
    """Get the log level (INFO or DEBUG).

    The value is determined according to value of 'FLAKE518_DEBUG'
    environment variable.

    Returns:
        int: A log-level for a logging.Logger instance.
    """
    result: int = logging.INFO

    flake518_dbg: bool = False
    flake518_dbg_env: Optional[str] = os.getenv("FLAKE518_DEBUG")

    if flake518_dbg_env is not None:
        flake518_dbg = bool(flake518_dbg_env)

    if flake518_dbg:
        result = logging.DEBUG

    return result


_log_level: int = _get_log_level()

logger: logging.Logger = logging.Logger("FLAKE518", level=_log_level)
logger.addHandler(logging.StreamHandler(sys.stdout))


def get_pyproject_toml() -> Optional[Path]:
    """Find the 'pytproject.toml' file.

    Starts in the current directory and attempts to find the
    the 'pyproject.toml' file in this directory or any parent
    directory. The first found file is returned. If no file
    is found, the result will be `None`.

    Returns:
        Optional[Path]: The path to the pyproject.toml file, if found.
    """
    cur_dir: str = os.curdir
    cur_dir = os.path.realpath(cur_dir)

    parent, tail = (cur_dir, cur_dir)
    while tail is not None and not len(tail) == 0:
        logger.debug("Searching for '%s' in %s", PY_PROJECT_TOML, parent)
        py_project_toml_path = os.path.join(parent, PY_PROJECT_TOML)

        py_project_toml = Path(py_project_toml_path)

        if py_project_toml.exists():
            logger.debug("Found %s", py_project_toml)
            return py_project_toml

        parent, tail = os.path.split(parent)

    logger.debug("Failed to find '%s'", PY_PROJECT_TOML)
    return None


def read_pyproject_toml(py_project_toml: Path) -> dict:
    """Read the specified pyproject.toml file.

    Reads the pyproject.toml file searching for either tool.flake8
    or tool.flake518 configuration sections. If both sections are found,
    the sections will be merged.

    Args:
        py_project_toml (Path): The path to the pyproject.toml.

    Returns:
        dict: The matching configuration sections.
    """
    result: dict = {}

    if not py_project_toml.exists():
        logger.debug("%s does not exist", py_project_toml)
        return result

    logger.debug("Reading %s", py_project_toml)
    toml_content: dict = load_toml(py_project_toml)
    if TOOL in toml_content.keys():
        logger.debug("Found '%s' section in %s", TOOL, py_project_toml)
        tool_content: dict = toml_content[TOOL]

        for section in FLAKE_SECTIONS:
            logger.debug(
                "Searching for section '%s' in %s", section, py_project_toml
            )
            if section in tool_content.keys():
                logger.debug(
                    "Found section '%s' in %s", section, py_project_toml
                )
                result.update(tool_content[section])
            else:
                logger.debug(
                    "Section '%s' does not exist in %s",
                    section,
                    py_project_toml,
                )

    # Captions have been lost after merging. Add generic flake8 section
    if len(result) > 0:
        result = {'flake8': result}

    return result


def write_config_to_ini(config: dict, ini: TextIO) -> None:
    """Write the configuration dictionary to the specified file.

    Args:
        config (dict): The configuration to write.
        ini (TextIO): The targetting file pointer.
    """
    config_writer: RawConfigParser = RawConfigParser("")
    logger.debug("The following configuration is written: %s", config)
    config_writer.read_dict(config)
    config_writer.write(ini)
    ini.flush()


def run(argv: Optional[_List[str]] = None) -> None:
    """Perform the operations of flake8.

    Parses the pyproject.toml file if found. If configuration sections for
    flake8 are contained, it creates a ini file as additional configuration
    file.

    Args:
        argv (Optional[_List[str]], optional): [description]. Defaults to None.
    """
    args: _List[str] = argv or sys.argv[1:]

    config: dict = {}
    py_project: Path = get_pyproject_toml()
    if py_project is not None:
        config = read_pyproject_toml(py_project)

    if (len(config)) > 0:
        logger.debug(
            "Found entries in %s. Adding additional configuration...",
            py_project,
        )
        with NamedTemporaryFile(
                "w+t", prefix="flake518_", suffix=".cfg", delete=True
        ) as handle:
            write_config_to_ini(config, handle)
            logger.debug(
                "Using additional configuration file '%s' for flake8 call. "
                "File will be deleted afterwards",
                handle.name,
            )
            handle.flush()
            args.append('--config')
            args.append('{}'.format(handle.name))
            logger.debug("The following arguments are applied now: %s", args)
            run_flake8(args)

    else:
        logger.debug("Running flake8 without modified configuration")
        run_flake8(args)
