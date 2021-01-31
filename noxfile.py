import tempfile

import nox
from nox.sessions import Session


nox.options.sessions = "lint", "safety", "mypy", "tests"

SOURCE_CODE = "src", "tests", "noxfile.py"
PYTHON_VERSIONS = ["3.8", "3.7", "3.6"]


@nox.session(python="3.8")
def black(session: Session) -> None:
    """Run black code formatter."""
    args = session.posargs or SOURCE_CODE
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session(python=PYTHON_VERSIONS)
def lint(session: Session) -> None:
    """Lint using flake8."""
    args = session.posargs or SOURCE_CODE
    install_with_constraints(
        session,
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-import-order",
    )
    session.run("flake8", *args)


@nox.session(python=PYTHON_VERSIONS)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or SOURCE_CODE
    install_with_constraints(session, "mypy")
    session.run("mypy", *args)


@nox.session(python=PYTHON_VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["--cov", "-m", "not e2e"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session, "coverage[toml]", "pytest", "pytest-cov", "pytest-mock"
    )
    session.run("pytest", *args)


@nox.session(python="3.8")
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        install_with_constraints(session, "safety")
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")


@nox.session(python="3.8")
def coverage(session: Session) -> None:
    """Upload coverage data."""
    install_with_constraints(session, "coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)


def install_with_constraints(session, *args, **kwargs):
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            "--without-hashes",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)
