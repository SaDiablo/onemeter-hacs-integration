"""Nox sessions."""
import tempfile
from pathlib import Path
import shutil

import nox

nox.options.sessions = ["lint", "docs", "linkcheck"]
locations = ["custom_components/onemeter", "tests", "noxfile.py"]


@nox.session
def lint(session):
    """Lint using flake8."""
    args = session.posargs or locations
    install_with_constraints = ["flake8", "flake8-black", "flake8-docstrings", "flake8-isort"]
    session.install(*install_with_constraints)
    session.run("flake8", *args)


@nox.session
def docs(session):
    """Build the documentation."""
    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.install("-r", "docs/requirements.txt")
    session.run(
        "sphinx-build",
        "-b",
        "html",
        "-v",
        "docs",
        str(build_dir),
    )


@nox.session
def linkcheck(session):
    """Check links in documentation."""
    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.install("-r", "docs/requirements.txt")
    session.run(
        "sphinx-build",
        "-b",
        "linkcheck",
        "-v",
        "docs",
        str(build_dir),
    )


def install_with_constraints(session, *args, **kwargs):
    """Install packages constrained by Poetry's lock file."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "pip",
            "install",
            *args,
            **kwargs,
        )