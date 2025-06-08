import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vendor_service.settings")
django.setup()

import grpc
from concurrent import futures
from api_config.models import APIConfiguration, CommandTemplate
import shared.grpc.generated.vendor_service_pb2_grpc as vendor_service_pb2_grpc
import shared.grpc.generated.vendor_service_pb2 as vendor_service_pb2
from shared.grpc.services.utils import dict_to_struct
from grpc_reflection.v1alpha import reflection

class VendorServiceServicer(vendor_service_pb2_grpc.VendorServiceServicer):
    def GetApiConfig(self, request, context):
        try:
            api_config = APIConfiguration.objects.get(id=request.api_config_id)
            return vendor_service_pb2.APIConfiguration(
                id=str(api_config.id),
                vendor_id=str(api_config.vendor.id) if api_config.vendor else "",
                name=api_config.name,
                version=api_config.version,
                description=api_config.description,
                base_url=api_config.base_url,
                auth_type=api_config.auth_type,
                auth_config=dict_to_struct(api_config.auth_config),
                headers_template=dict_to_struct(api_config.headers_template),
                timeout=api_config.timeout,
                retry_count=api_config.retry_count,
                retry_delay=api_config.retry_delay,
            )
        except APIConfiguration.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("API Config not found.")
            return vendor_service_pb2.APIConfiguration()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error retrieving API Config: {str(e)}")
            return vendor_service_pb2.APIConfiguration()
    
    def GetCommandTemplate(self, request, context):
        try:
            api_config = APIConfiguration.objects.get(id=request.api_config_id)
            template = CommandTemplate.objects.get(api_config=api_config, command_type=request.command_type)

            return vendor_service_pb2.CommandTemplate(
                url_template=template.url_template,
                method=template.method,
                headers_template=dict_to_struct(template.headers_template),
                body_template=dict_to_struct(template.body_template),
                required_params=template.required_params,
                optional_params=template.optional_params,
            )
        except APIConfiguration.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("API Config not found.")
            return vendor_service_pb2.CommandTemplate()
        except CommandTemplate.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Command Template not found.")
            return vendor_service_pb2.CommandTemplate()

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