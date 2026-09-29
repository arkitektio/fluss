"""Validate a source and store it as a Python flow version, in one step."""

from typing import Iterable, Mapping, Sequence

from rekuest.client.client import Rekuest

from fluss.api.schema import EffectClass, PythonFlow
from fluss.engine.python.manifest import ManifestAction
from fluss.engine.python.validate import ValidationReport, validate_python_flow
from fluss.fluss import Fluss


class InvalidPythonFlow(ValueError):
    """The source did not validate; ``report`` says why."""

    def __init__(self, report: ValidationReport) -> None:
        """Carry the report; the message is its diagnostics."""
        super().__init__("\n".join(d.message for d in report.diagnostics))
        self.report = report


async def amanifest(actions: Mapping[str, str], rekuest: Rekuest, effects: Mapping[str, EffectClass] | None = None) -> list[ManifestAction]:
    """``{alias: action hash}`` as manifest actions, each looked up in rekuest.

    ``effects`` declares the aliases that touch the real world: rekuest's ``Action`` does not
    carry its implementations' effect class, so the author of the flow says so.
    """
    effects = effects or {}
    return [ManifestAction(alias=alias, action=await rekuest.afind(hash=hash), effect=effects.get(alias, EffectClass.NONE)) for alias, hash in actions.items()]


async def acreate_python_flow_from_source(
    source: str,
    actions: Sequence[ManifestAction],
    fluss: Fluss,
    *,
    title: str | None = None,
    description: str | None = None,
    previous: str | None = None,
    entrypoint: str = "main",
    structures: Iterable[str] = (),
    publish: bool = False,
) -> PythonFlow:
    """Validate ``source`` against ``actions`` and store it as a DRAFT (or published) version.

    Raises :class:`InvalidPythonFlow` with the report when the source does not validate.
    """
    report = await validate_python_flow(source, actions, entrypoint=entrypoint, structures=structures)
    if not report.ok:
        raise InvalidPythonFlow(report)
    flow = await fluss.acreate_python_flow(
        source=source,
        entrypoint=report.entrypoint,
        args=report.args,
        returns=report.returns,
        manifest=report.manifest,
        runtime=report.runtime,
        title=title,
        description=description,
        previous=previous,
    )
    if publish:
        flow = await fluss.apublish_python_flow(id=flow.id)
    return flow
