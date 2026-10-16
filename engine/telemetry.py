"""Agent tracing in Google Cloud Trace (OpenTelemetry). Off unless SAFESHELF_TRACE_TO_CLOUD=1.

ADK already emits a span for every agent, tool call and model call; this sends them, and SafeShelf's own spans (each
official source fetch, the identity agent, the critic, the code verdict), to Cloud Trace through ADK's Google Cloud
exporter (telemetry.googleapis.com). Needs the Telemetry and Cloud Trace APIs enabled on the project.

    from engine import telemetry
    with telemetry.span("source.cpsc", source="cpsc"):
        ...
"""
import contextlib
import logging
import os

from opentelemetry import trace

log = logging.getLogger(__name__)
tracer = trace.get_tracer("safeshelf")
_ready = False


def setup() -> bool:
    """Install the Cloud Trace exporter once (API startup). Never raises: tracing must not stop an answer."""
    global _ready
    if _ready or os.environ.get("SAFESHELF_TRACE_TO_CLOUD") != "1":
        return _ready
    try:
        import google.auth
        from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
        from google.adk.telemetry.setup import maybe_set_otel_providers

        credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or project
        hooks = get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_metrics=False, enable_cloud_logging=False,
                                  google_auth=(credentials, project))
        maybe_set_otel_providers(otel_hooks_to_setup=[hooks], otel_resource=get_gcp_resource(project))
        _ready = True
        log.info("Cloud Trace on for project %s", project)
    except Exception as error:  # noqa: BLE001
        log.warning("Cloud Trace not set up: %s", type(error).__name__)
    return _ready


@contextlib.contextmanager
def span(name: str, **attributes):
    """A SafeShelf span; attributes must be plain values (no personal data)."""
    with tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            if value is not None:
                current.set_attribute(f"safeshelf.{key}", value if isinstance(value, (str, int, float, bool))
                                      else str(value))
        yield current


def note(current, **attributes) -> None:
    for key, value in attributes.items():
        if value is not None:
            current.set_attribute(f"safeshelf.{key}", value if isinstance(value, (str, int, float, bool))
                                  else str(value))
