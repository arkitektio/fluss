"""Validate a Python flow: the report ``createPythonFlow`` stores.

Two passes. The host parses the source with ``ast`` (never executing it) to check its shape
and read the entrypoint's signature into ports. Then Monty type-checks it against the stubs
of the manifest's actions -- which is also what rejects a call to anything the manifest does
not offer, as an unresolved name.

Feeding the source defines its functions, so its module body may only import, define, and
bind literals: nothing runs until the entrypoint is called.
"""

import ast
from typing import Iterable, Sequence

import pydantic_monty
from pydantic import BaseModel, Field

from fluss.api.schema import ArgPortInput, ManifestEntryInput, ReturnPortInput
from fluss.engine.python.manifest import ManifestAction, ManifestError, build_stubs, check_manifest, manifest_entries
from fluss.engine.python.ports import AnnotationError, signature_to_ports

#: The version of the helpers a flow may use beside its manifest (none yet but the stdlib Monty ships).
HELPERS_VERSION = "1"
#: What a validation is valid for: the interpreter and the helpers the source was checked against.
RUNTIME = f"monty-{pydantic_monty.__version__}/helpers-{HELPERS_VERSION}"

SCRIPT_NAME = "flow.py"


class Diagnostic(BaseModel):
    """One problem with the source."""

    message: str
    line: int | None = None


class ValidationReport(BaseModel):
    """What validation derived from a source: store it with ``createPythonFlow`` when ``ok``."""

    ok: bool
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    entrypoint: str = "main"
    args: list[ArgPortInput] = Field(default_factory=list)
    returns: list[ReturnPortInput] = Field(default_factory=list)
    manifest: list[ManifestEntryInput] = Field(default_factory=list)
    runtime: str = RUNTIME
    stubs: str = ""


class SourceError(ValueError):
    """The source's shape is wrong (before any type checking)."""

    def __init__(self, message: str, line: int | None = None) -> None:
        """``line`` is where in the source, when known."""
        super().__init__(message)
        self.line = line


def _is_literal(node: ast.expr | None) -> bool:
    if node is None:
        return True
    try:
        ast.literal_eval(node)
    except ValueError:
        return False
    return True


def check_module(module: ast.Module) -> None:
    """Only imports, definitions, a docstring and literal bindings at module level."""
    for index, node in enumerate(module.body):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Expr) and index == 0 and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets) and _is_literal(node.value):
            continue
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and _is_literal(node.value):
            continue
        raise SourceError(
            f"Only imports, functions, classes and literal constants may appear at module level, not `{ast.unparse(node).splitlines()[0]}`",
            node.lineno,
        )


def find_entrypoint(module: ast.Module, entrypoint: str) -> ast.AsyncFunctionDef:
    """The ``async def`` the run calls."""
    for node in module.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == entrypoint:
            return node
        if isinstance(node, ast.FunctionDef) and node.name == entrypoint:
            raise SourceError(f"{entrypoint}() must be `async def`, so it can await the actions it calls", node.lineno)
    raise SourceError(f"The source defines no `async def {entrypoint}(...)`")


def analyse(source: str, entrypoint: str, structures: dict[str, str]) -> tuple[list[ArgPortInput], list[ReturnPortInput]]:
    """Shape-check the source and read its entrypoint's ports (host side, no execution)."""
    try:
        module = ast.parse(source, filename=SCRIPT_NAME)
    except SyntaxError as error:
        raise SourceError(f"Syntax error: {error.msg}", error.lineno) from error
    check_module(module)
    function = find_entrypoint(module, entrypoint)
    try:
        return signature_to_ports(function, structures)
    except AnnotationError as error:
        raise SourceError(str(error), error.line) from error


def _typing_diagnostic(error: pydantic_monty.MontyError) -> Diagnostic:
    display = getattr(error, "display", None)
    display = display() if callable(display) else str(error)
    return Diagnostic(message=display)


async def validate_python_flow(
    source: str,
    actions: Sequence[ManifestAction] = (),
    *,
    entrypoint: str = "main",
    structures: Iterable[str] = (),
    pool: pydantic_monty.AsyncMonty | None = None,
) -> ValidationReport:
    """Check ``source`` against the ``actions`` it may call; derive its ports and manifest.

    ``structures`` are identifiers the entrypoint's signature uses that no action mentions.
    Pass a running ``pool`` to reuse its workers; otherwise one is started for this check.
    """
    report = ValidationReport(ok=False, entrypoint=entrypoint)
    try:
        check_manifest(actions, reserved=[entrypoint])
        stubs, classes = build_stubs(actions, structures)
        args, returns = analyse(source, entrypoint, classes)
    except (ManifestError, AnnotationError) as error:
        report.diagnostics.append(Diagnostic(message=str(error)))
        return report
    except SourceError as error:
        report.diagnostics.append(Diagnostic(message=str(error), line=error.line))
        return report

    report.stubs = stubs
    diagnostic = await type_check(source, stubs, pool=pool)
    if diagnostic is not None:
        report.diagnostics.append(diagnostic)
        return report

    report.ok = True
    report.args = args
    report.returns = returns
    report.manifest = manifest_entries(actions)
    return report


async def type_check(source: str, stubs: str, *, pool: pydantic_monty.AsyncMonty | None = None) -> Diagnostic | None:
    """Type-check (and define) the source in a fresh session; the problem, if any."""
    if pool is None:
        async with pydantic_monty.AsyncMonty(min_processes=1, max_processes=1) as own_pool:
            return await type_check(source, stubs, pool=own_pool)
    async with pool.checkout(script_name=SCRIPT_NAME, type_check=True, type_check_stubs=stubs, type_check_format="concise") as session:
        try:
            await session.feed_run(source)
        except (pydantic_monty.MontyTypingError, pydantic_monty.MontySyntaxError, pydantic_monty.MontyRuntimeError) as error:
            return _typing_diagnostic(error)
    return None
