try:
    from opentelemetry import trace
except ImportError:  # pragma: no cover
    class _NoOpSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _NoOpTracer:
        def start_as_current_span(self, _: str):
            return _NoOpSpan()

    class _NoOpTrace:
        @staticmethod
        def get_tracer(_: str):
            return _NoOpTracer()

        @staticmethod
        def set_tracer_provider(_: object) -> None:
            return None

    trace = _NoOpTrace()  # type: ignore[assignment]


def configure_tracing(enabled: bool, service_name: str) -> None:
    if not enabled:
        return

    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)


def get_tracer(name: str):
    return trace.get_tracer(name)
