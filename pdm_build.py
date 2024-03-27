"""
PDM Build Script
auto bump version
2024/3/18
"""

import subprocess
import shutil

from pdm.backend.hooks import Context

git = shutil.which("git")
rev = ""


def pdm_build_hook_enabled(_context: Context) -> bool:
    global rev
    if not git:
        return False
    with subprocess.Popen(
        [git, "rev-parse", "--short", "HEAD"],
        stdout=subprocess.PIPE,
    ) as proc:
        rev = proc.stdout.read().strip().decode()
    if rev is None:
        return False
    return True


def pdm_build_initialize(context: Context):
    ver = context.config.metadata.get("version")
    with open("lagrange/version.py", "w") as f:
        if ver is None:
            ver = "0.0.0"
        f.write(f"__version__ = '{ver}-{rev}'\n")


def pdm_build_finalize(context: Context, _files) -> None:
    ver = context.config.metadata.get("version")
    with open("lagrange/version.py", "w") as f:
        if ver is None:
            ver = "0.0.0"
        f.write(f"__version__ = '{ver}'")
