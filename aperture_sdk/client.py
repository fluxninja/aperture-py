import datetime
import functools
import logging
import time
import typing
from typing import Callable, Dict, Optional, Type, TypeVar

import grpc
from aperture_sdk._gen.aperture.flowcontrol.check.v1.check_pb2 import CheckRequest
from aperture_sdk._gen.aperture.flowcontrol.check.v1.check_pb2_grpc import (
    FlowControlServiceStub,
)
from aperture_sdk.const import (
    default_grpc_reconnection_time,
    default_rpc_timeout,
    flow_start_timestamp_label,
    library_name,
    library_version,
    source_label,
    workload_start_timestamp_label,
)
from aperture_sdk.flow import Flow
from aperture_sdk.utils import TWrappedReturn, run_fn
from opentelemetry import baggage, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.util import types as otel_types

TApertureClient = TypeVar("TApertureClient", bound="ApertureClient")
TWrappedFunction = Callable[..., TWrappedReturn]
Labels = Dict[str, str]


class ApertureClient:
    def __init__(
        self,
        channel: grpc.Channel,
        otlp_exporter: OTLPSpanExporter,
        check_timeout: datetime.timedelta = default_rpc_timeout,
    ):
        self.logger = logging.getLogger("aperture-py-sdk")
        self.timeout = check_timeout

        resource = Resource.create(
            {
                SERVICE_NAME: library_name,
                SERVICE_VERSION: library_version,
            }
        )
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        self.tracer = trace.get_tracer(library_name, library_version)

        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        self.otlp_exporter = otlp_exporter
        self.grpc_channel = channel

    @classmethod
    def new_client(
        cls: Type[TApertureClient],
        endpoint: str = "http://localhost:4317",
        insecure: bool = False,
        check_timeout: datetime.timedelta = default_rpc_timeout,
        grpc_timeout: datetime.timedelta = default_grpc_reconnection_time,
        credentials: Optional[grpc.ChannelCredentials] = None,
        compression: grpc.Compression = grpc.Compression.NoCompression,
    ) -> TApertureClient:
        if credentials is None:
            credentials = grpc.ssl_channel_credentials()
        otlp_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            insecure=insecure,
            credentials=credentials,
            compression=compression,
            timeout=int(grpc_timeout.total_seconds()),
        )
        grpc_channel = (
            grpc.insecure_channel(endpoint, compression=compression)
            if insecure
            else grpc.secure_channel(endpoint, credentials, compression=compression)
        )
        return cls(
            channel=grpc_channel,
            otlp_exporter=otlp_exporter,
            check_timeout=check_timeout,
        )

    def start_flow(
        self, control_point: str, explicit_labels: Optional[Labels] = None
    ) -> Flow:
        labels: Labels = {}
        labels.update({key: str(value) for key, value in baggage.get_all().items()})
        # Explicit labels override baggage
        labels.update(explicit_labels or {})
        request = CheckRequest(control_point=control_point, labels=labels)
        span_attributes: otel_types.Attributes = {
            flow_start_timestamp_label: time.monotonic_ns(),
            source_label: "sdk",
        }

        span = self.tracer.start_span("Aperture Check", attributes=span_attributes)
        stub = FlowControlServiceStub(self.grpc_channel)
        try:
            # stub.Check is typed to accept an int, but it actually accepts a float
            timeout = typing.cast(int, self.timeout.total_seconds())
            response = (
                stub.Check(request)
                if timeout == 0
                else stub.Check(request, timeout=timeout)
            )
        except grpc.RpcError as e:
            self.logger.debug(f"Aperture gRPC call failed: {e.details()}")
            response = None
        span.set_attribute(workload_start_timestamp_label, time.monotonic_ns())
        return Flow(span=span, check_response=response)

    def decorate(
        self,
        control_point: str,
        explicit_labels: Optional[Dict[str, str]] = None,
        on_reject: Optional[Callable] = None,
        fail_open: bool = True,
    ) -> Callable[[TWrappedFunction], TWrappedFunction]:
        def decorator(fn: TWrappedFunction) -> TWrappedFunction:
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                with self.start_flow(control_point, explicit_labels) as flow:
                    if flow.should_run():
                        return await run_fn(fn, *args, **kwargs)
                    else:
                        if on_reject:
                            return on_reject()
                        raise RejectedFlowException("Flow was rejected")

            return wrapper

        return decorator

    def close(self):
        self.otlp_exporter.shutdown()


class ApertureException(Exception):
    pass


class RejectedFlowException(ApertureException):
    pass
