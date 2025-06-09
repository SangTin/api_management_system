import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vendor_service.settings")
django.setup()

import grpc
from concurrent import futures
from api_config.models import APIConfiguration, CommandTemplate
from device.models import Device, DeviceCommand
import shared.grpc.generated.vendor_service_pb2_grpc as vendor_service_pb2_grpc
import shared.grpc.generated.vendor_service_pb2 as vendor_service_pb2
from shared.grpc.services.utils import dict_to_struct
from grpc_reflection.v1alpha import reflection

class VendorServiceServicer(vendor_service_pb2_grpc.VendorServiceServicer):
    
    def GetAPIConfigByID(self, request, context):
        """Get API configuration by ID"""
        try:
            api_config = APIConfiguration.objects.select_related('vendor').get(id=request.api_config_id)
            
            # Return APIConfiguration message directly
            response_config = vendor_service_pb2.APIConfiguration(
                id=str(api_config.id),
                name=str(api_config.name),
                version=str(api_config.version),
                description=str(api_config.description or ''),
                base_url=str(api_config.base_url or ''),
                auth_type=str(api_config.auth_type or 'none'),
                auth_config=dict_to_struct(api_config.auth_config or {}),
                headers_template=dict_to_struct(api_config.headers_template or {}),
                timeout=int(api_config.timeout or 30),
                retry_count=int(api_config.retry_count or 3),
                retry_delay=int(api_config.retry_delay or 5),
                vendor_id=str(api_config.vendor.id) if api_config.vendor else '',
                vendor_name=str(api_config.vendor.name) if api_config.vendor else '',
                is_active=bool(api_config.is_active),
                created_by=str(api_config.created_by or ''),
                created_at=api_config.created_at.isoformat() if api_config.created_at else '',
                updated_at=api_config.updated_at.isoformat() if api_config.updated_at else '',
            )
            
            response = vendor_service_pb2.GetApiConfigByIDResponse(api_config=response_config)
            return response
            
        except APIConfiguration.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("API configuration not found.")
            return vendor_service_pb2.GetApiConfigByIDResponse()
        except Exception as e:
            print(f"GetAPIConfigByID error: {e}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An error occurred: {str(e)}")
            return vendor_service_pb2.GetApiConfigByIDResponse()

    def GetCommandTemplate(self, request, context):
        """Get command template by ID"""
        try:
            command_template = CommandTemplate.objects.get(id=request.command_template_id)
            
            # Return CommandTemplate message directly
            response_template = vendor_service_pb2.CommandTemplate(
                id=str(command_template.id),
                name=str(command_template.name),
                command_type=str(command_template.command_type),
                description=str(command_template.description or ''),
                method=str(command_template.method),
                url_template=str(command_template.url_template or ''),
                body_template=dict_to_struct(command_template.body_template or {}),
                headers_template=dict_to_struct(command_template.headers_template or {}),
                base_url=str(command_template.base_url or ''),
                timeout=int(command_template.timeout or 30),
                retry_count=int(command_template.retry_count or 3),
                retry_delay=int(command_template.retry_delay or 5),
                required_params=list(command_template.required_params or []),
                optional_params=list(command_template.optional_params or []),
                api_config_id=str(command_template.api_config.id) if command_template.api_config else '',
                created_at=command_template.created_at.isoformat() if command_template.created_at else '',
                updated_at=command_template.updated_at.isoformat() if command_template.updated_at else '',
            )
            
            response = vendor_service_pb2.GetCommandTemplateResponse(command_template=response_template)
            return response
            
        except CommandTemplate.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Command template not found.")
            return vendor_service_pb2.GetCommandTemplateResponse()
        except Exception as e:
            print(f"GetCommandTemplate error: {e}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An error occurred: {str(e)}")
            return vendor_service_pb2.GetCommandTemplateResponse()

    def GetDevice(self, request, context):
        """Get device by ID"""
        try:
            device = Device.objects.select_related('vendor').get(id=request.device_id)
            
            # Return Device message directly
            response_device = vendor_service_pb2.Device(
                id=str(device.id),
                name=str(device.name),
                model=str(device.model or ''),
                serial_number=str(device.serial_number or ''),
                firmware_version=str(device.firmware_version or ''),
                base_url=str(device.base_url or ''),
                auth_type=str(device.auth_type or 'none'),
                auth_config=dict_to_struct(device.auth_config or {}),
                headers_template=dict_to_struct(device.headers_template or {}),
                body_template=dict_to_struct(device.body_template or {}),
                params_template=dict_to_struct(device.params_template or {}),
                timeout=int(device.timeout or 30),
                retry_count=int(device.retry_count or 3),
                retry_delay=int(device.retry_delay or 5),
                vendor_id=str(device.vendor.id) if device.vendor else '',
                vendor_name=str(device.vendor.name) if device.vendor else '',
                is_active=True,
                created_at=device.created_at.isoformat() if device.created_at else '',
                updated_at=device.updated_at.isoformat() if device.updated_at else '',
            )
            
            response = vendor_service_pb2.GetDeviceResponse(device=response_device)
            return response
            
        except Device.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Device not found.")
            return vendor_service_pb2.GetDeviceResponse()
        except Exception as e:
            print(f"GetDevice error: {e}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An error occurred: {str(e)}")
            return vendor_service_pb2.GetDeviceResponse()

    def GetCommandContext(self, request, context):
        """Get command context for device"""
        try:
            # Get device
            device = Device.objects.select_related('vendor').get(id=request.device_id)
            
            # Get primary device command for this command type
            device_command = DeviceCommand.objects.filter(
                device=device,
                command_type=request.command_type,
                is_primary=True,
                is_active=True
            ).select_related('command').first()
            
            if not device_command or not device_command.command:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No active command template found for this device and command type.")
                return vendor_service_pb2.CommandContext()
            
            command_template = device_command.command
            api_config = command_template.api_config
            
            # Create Device message
            device_msg = vendor_service_pb2.Device(
                id=str(device.id),
                name=str(device.name),
                model=str(device.model or ''),
                serial_number=str(device.serial_number or ''),
                firmware_version=str(device.firmware_version or ''),
                base_url=str(device.base_url or ''),
                auth_type=str(device.auth_type or 'none'),
                auth_config=dict_to_struct(device.auth_config or {}),
                headers_template=dict_to_struct(device.headers_template or {}),
                body_template=dict_to_struct(device.body_template or {}),
                params_template=dict_to_struct(device.params_template or {}),
                timeout=int(device.timeout or 30),
                retry_count=int(device.retry_count or 3),
                retry_delay=int(device.retry_delay or 5),
                vendor_id=str(device.vendor.id) if device.vendor else '',
                vendor_name=str(device.vendor.name) if device.vendor else '',
                is_active=True,
                created_at=device.created_at.isoformat() if device.created_at else '',
                updated_at=device.updated_at.isoformat() if device.updated_at else '',
            )
            
            # Create APIConfiguration message
            api_config_msg = vendor_service_pb2.APIConfiguration(
                id=str(api_config.id),
                name=str(api_config.name),
                version=str(api_config.version),
                description=str(api_config.description or ''),
                base_url=str(api_config.base_url or ''),
                auth_type=str(api_config.auth_type or 'none'),
                auth_config=dict_to_struct(api_config.auth_config or {}),
                headers_template=dict_to_struct(api_config.headers_template or {}),
                timeout=int(api_config.timeout or 30),
                retry_count=int(api_config.retry_count or 3),
                retry_delay=int(api_config.retry_delay or 5),
                vendor_id=str(api_config.vendor.id) if api_config.vendor else '',
                vendor_name=str(api_config.vendor.name) if api_config.vendor else '',
                is_active=bool(api_config.is_active),
                created_by=str(api_config.created_by or ''),
                created_at=api_config.created_at.isoformat() if api_config.created_at else '',
                updated_at=api_config.updated_at.isoformat() if api_config.updated_at else '',
            )
            
            # Create CommandTemplate message
            command_template_msg = vendor_service_pb2.CommandTemplate(
                id=str(command_template.id),
                name=str(command_template.name),
                command_type=str(command_template.command_type),
                description=str(command_template.description or ''),
                method=str(command_template.method),
                url_template=str(command_template.url_template or ''),
                body_template=dict_to_struct(command_template.body_template or {}),
                headers_template=dict_to_struct(command_template.headers_template or {}),
                base_url=str(command_template.base_url or ''),
                timeout=int(command_template.timeout or 30),
                retry_count=int(command_template.retry_count or 3),
                retry_delay=int(command_template.retry_delay or 5),
                required_params=list(command_template.required_params or []),
                optional_params=list(command_template.optional_params or []),
                api_config_id=str(command_template.api_config.id) if command_template.api_config else '',
                created_at=command_template.created_at.isoformat() if command_template.created_at else '',
                updated_at=command_template.updated_at.isoformat() if command_template.updated_at else '',
            )
            
            # Create DeviceCommand message
            device_command_msg = vendor_service_pb2.DeviceCommand(
                id=str(device_command.id),
                device_id=str(device_command.device.id),
                command_template_id=str(device_command.command.id),
                command_type=str(device_command.command_type),
                custom_params=dict_to_struct(device_command.params or {}),
                is_primary=bool(device_command.is_primary),
                priority=int(device_command.priority),
                is_active=bool(device_command.is_active),
                created_at=device_command.created_at.isoformat() if device_command.created_at else '',
                updated_at=device_command.updated_at.isoformat() if device_command.updated_at else '',
            )
            
            # Create CommandContext response
            response = vendor_service_pb2.CommandContext(
                device=device_msg,
                api_config=api_config_msg,
                command_template=command_template_msg,
                device_command=device_command_msg
            )
            return response
            
        except Device.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Device not found.")
            return vendor_service_pb2.CommandContext()
        except Exception as e:
            print(f"GetCommandContext error: {e}")
            import traceback
            traceback.print_exc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An error occurred: {str(e)}")
            return vendor_service_pb2.CommandContext()

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