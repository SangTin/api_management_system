import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vendor_service.settings")
django.setup()

import grpc
from concurrent import futures
from api_config.models import APIConfiguration, CommandTemplate
from devices.models import Device, DeviceCommand
import shared.grpc.generated.vendor_service_pb2_grpc as vendor_service_pb2_grpc
import shared.grpc.generated.vendor_service_pb2 as vendor_service_pb2
from shared.grpc.services.utils import dict_to_struct
from grpc_reflection.v1alpha import reflection

class VendorServiceServicer(vendor_service_pb2_grpc.VendorServiceServicer):
    def GetCommandContext(self, request, context):
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    vendor_service_pb2_grpc.add_VendorServiceServicer_to_server(VendorServiceServicer(), server)

    SERVICE_NAMES = (
        vendor_service_pb2.DESCRIPTOR.services_by_name['VendorService'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    port = os.getenv("VENDOR_SERVICE_GRPC_PORT", "50051")
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"[gRPC] VendorService is running on port {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()