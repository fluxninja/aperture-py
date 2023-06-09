# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import check_pb2 as aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2


class FlowControlServiceStub(object):
    """FlowControlService is used to perform Flow Control operations.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Check = channel.unary_unary(
                '/aperture.flowcontrol.check.v1.FlowControlService/Check',
                request_serializer=aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2.CheckRequest.SerializeToString,
                response_deserializer=aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2.CheckResponse.FromString,
                )


class FlowControlServiceServicer(object):
    """FlowControlService is used to perform Flow Control operations.
    """

    def Check(self, request, context):
        """Check wraps the given arbitrary resource and matches the given labels against Flow Control Limiters to makes a decision whether to allow/deny.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_FlowControlServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Check': grpc.unary_unary_rpc_method_handler(
                    servicer.Check,
                    request_deserializer=aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2.CheckRequest.FromString,
                    response_serializer=aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2.CheckResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'aperture.flowcontrol.check.v1.FlowControlService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class FlowControlService(object):
    """FlowControlService is used to perform Flow Control operations.
    """

    @staticmethod
    def Check(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/aperture.flowcontrol.check.v1.FlowControlService/Check',
            aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2.CheckRequest.SerializeToString,
            aperture_dot_flowcontrol_dot_check_dot_v1_dot_check__pb2.CheckResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
