import grpc
from shared.grpc.generated import vendor_service_pb2_grpc, vendor_service_pb2
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct

class BaseServiceClient:
    """Base class for gRPC service clients"""
    
    def _init_client(self):
        grpc_target = 'api-gateway:8000'
        self.channel = grpc.insecure_channel(grpc_target)
        self.stub = None

    def get_stub(self):
        return self.stub

    def close(self):
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stub = None
            
    def _protobuf_to_dict(self, proto_obj):
        """Convert protobuf object to dict"""
        try:
            if hasattr(proto_obj, 'fields'):  # It's a Struct
                return self._struct_to_dict(proto_obj)
            else:  # It's a regular message
                return MessageToDict(proto_obj, preserving_proto_field_name=True)
        except Exception as e:
            print(f"Protobuf conversion error: {e}")
            return {}
    
    def _struct_to_dict(self, struct_obj):
        """Convert protobuf Struct to dict"""
        if not struct_obj or not hasattr(struct_obj, 'fields'):
            return {}
        
        result = {}
        for key, value in struct_obj.fields.items():
            if value.HasField('null_value'):
                result[key] = None
            elif value.HasField('number_value'):
                result[key] = value.number_value
            elif value.HasField('string_value'):
                result[key] = value.string_value
            elif value.HasField('bool_value'):
                result[key] = value.bool_value
            elif value.HasField('struct_value'):
                result[key] = self._struct_to_dict(value.struct_value)
            elif value.HasField('list_value'):
                result[key] = [self._convert_list_value(item) for item in value.list_value.values]
        return result
    
    def _convert_list_value(self, value):
        """Convert list value from protobuf"""
        if value.HasField('null_value'):
            return None
        elif value.HasField('number_value'):
            return value.number_value
        elif value.HasField('string_value'):
            return value.string_value
        elif value.HasField('bool_value'):
            return value.bool_value
        elif value.HasField('struct_value'):
            return self._struct_to_dict(value.struct_value)
        elif value.HasField('list_value'):
            return [self._convert_list_value(item) for item in value.list_value.values]
        return None
        
class VendorServiceClient(BaseServiceClient):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        super()._init_client()
        self.stub = vendor_service_pb2_grpc.VendorServiceStub(self.channel)

    def get_api_config_by_id(self, api_config_id):
        """Get API configuration by ID"""
        try:
            request = vendor_service_pb2.GetAPIConfigByIDRequest(api_config_id=api_config_id)
            response = self.stub.GetAPIConfigByID(request)
            
            if response.api_config:
                # Convert message object to dict manually
                api_config_dict = {
                    'id': response.api_config.id,
                    'name': response.api_config.name,
                    'version': response.api_config.version,
                    'description': response.api_config.description,
                    'base_url': response.api_config.base_url,
                    'auth_type': response.api_config.auth_type,
                    'auth_config': self._struct_to_dict(response.api_config.auth_config),
                    'headers_template': self._struct_to_dict(response.api_config.headers_template),
                    'timeout': response.api_config.timeout,
                    'retry_count': response.api_config.retry_count,
                    'retry_delay': response.api_config.retry_delay,
                    'vendor_id': response.api_config.vendor_id,
                    'vendor_name': response.api_config.vendor_name,
                    'is_active': response.api_config.is_active,
                    'created_by': response.api_config.created_by,
                    'created_at': response.api_config.created_at,
                    'updated_at': response.api_config.updated_at,
                }
                print(f"Converted API config: {api_config_dict}")
                return api_config_dict
            else:
                raise Exception("No API configuration returned")
                
        except grpc.RpcError as e:
            raise Exception(f"gRPC error: {e.details()}")
        except Exception as e:
            raise Exception(f"Failed to get API config: {str(e)}")

    def get_command_template_by_id(self, command_template_id):
        """Get command template by ID"""
        try:
            request = vendor_service_pb2.CommandTemplateRequest(command_template_id=command_template_id)
            response = self.stub.GetCommandTemplate(request)
            
            if response.command_template:
                # Convert message object to dict manually
                template_dict = {
                    'id': response.command_template.id,
                    'name': response.command_template.name,
                    'command_type': response.command_template.command_type,
                    'description': response.command_template.description,
                    'method': response.command_template.method,
                    'url_template': response.command_template.url_template,
                    'body_template': self._struct_to_dict(response.command_template.body_template),
                    'headers_template': self._struct_to_dict(response.command_template.headers_template),
                    'base_url': response.command_template.base_url,
                    'timeout': response.command_template.timeout,
                    'retry_count': response.command_template.retry_count,
                    'retry_delay': response.command_template.retry_delay,
                    'required_params': list(response.command_template.required_params),
                    'optional_params': list(response.command_template.optional_params),
                    'api_config_id': response.command_template.api_config_id,
                    'created_at': response.command_template.created_at,
                    'updated_at': response.command_template.updated_at,
                }
                print(f"Converted command template: {template_dict}")
                return template_dict
            else:
                raise Exception("No command template returned")
                
        except grpc.RpcError as e:
            raise Exception(f"gRPC error: {e.details()}")
        except Exception as e:
            raise Exception(f"Failed to get command template: {str(e)}")

    def get_device_by_id(self, device_id):
        """Get device by ID"""
        try:
            request = vendor_service_pb2.DeviceRequest(device_id=device_id)
            response = self.stub.GetDevice(request)
            
            if response.device:
                # Convert message object to dict manually
                device_dict = {
                    'id': response.device.id,
                    'name': response.device.name,
                    'model': response.device.model,
                    'serial_number': response.device.serial_number,
                    'firmware_version': response.device.firmware_version,
                    'base_url': response.device.base_url,
                    'auth_type': response.device.auth_type,
                    'auth_config': self._struct_to_dict(response.device.auth_config),
                    'headers_template': self._struct_to_dict(response.device.headers_template),
                    'body_template': self._struct_to_dict(response.device.body_template),
                    'params_template': self._struct_to_dict(response.device.params_template),
                    'timeout': response.device.timeout,
                    'retry_count': response.device.retry_count,
                    'retry_delay': response.device.retry_delay,
                    'vendor_id': response.device.vendor_id,
                    'vendor_name': response.device.vendor_name,
                    'is_active': response.device.is_active,
                    'created_at': response.device.created_at,
                    'updated_at': response.device.updated_at,
                }
                return device_dict
            else:
                raise Exception("No device returned")
                
        except grpc.RpcError as e:
            raise Exception(f"gRPC error: {e.details()}")
        except Exception as e:
            raise Exception(f"Failed to get device: {str(e)}")

    def get_command_context(self, device_id, command_type):
        """Get command context for device"""
        try:
            request = vendor_service_pb2.CommandContextRequest(
                device_id=device_id,
                command_type=command_type
            )
            response = self.stub.GetCommandContext(request)
            
            # Convert all components to dict
            context = {
                'device': {
                    'id': response.device.id,
                    'name': response.device.name,
                    'model': response.device.model,
                    'serial_number': response.device.serial_number,
                    'firmware_version': response.device.firmware_version,
                    'base_url': response.device.base_url,
                    'auth_type': response.device.auth_type,
                    'auth_config': self._struct_to_dict(response.device.auth_config),
                    'headers_template': self._struct_to_dict(response.device.headers_template),
                    'body_template': self._struct_to_dict(response.device.body_template),
                    'params_template': self._struct_to_dict(response.device.params_template),
                    'timeout': response.device.timeout,
                    'retry_count': response.device.retry_count,
                    'retry_delay': response.device.retry_delay,
                    'vendor_id': response.device.vendor_id,
                    'vendor_name': response.device.vendor_name,
                    'is_active': response.device.is_active,
                    'created_at': response.device.created_at,
                    'updated_at': response.device.updated_at,
                },
                'api_config': {
                    'id': response.api_config.id,
                    'name': response.api_config.name,
                    'version': response.api_config.version,
                    'description': response.api_config.description,
                    'base_url': response.api_config.base_url,
                    'auth_type': response.api_config.auth_type,
                    'auth_config': self._struct_to_dict(response.api_config.auth_config),
                    'headers_template': self._struct_to_dict(response.api_config.headers_template),
                    'timeout': response.api_config.timeout,
                    'retry_count': response.api_config.retry_count,
                    'retry_delay': response.api_config.retry_delay,
                    'vendor_id': response.api_config.vendor_id,
                    'vendor_name': response.api_config.vendor_name,
                    'is_active': response.api_config.is_active,
                    'created_by': response.api_config.created_by,
                    'created_at': response.api_config.created_at,
                    'updated_at': response.api_config.updated_at,
                },
                'command_template': {
                    'id': response.command_template.id,
                    'name': response.command_template.name,
                    'command_type': response.command_template.command_type,
                    'description': response.command_template.description,
                    'method': response.command_template.method,
                    'url_template': response.command_template.url_template,
                    'body_template': self._struct_to_dict(response.command_template.body_template),
                    'headers_template': self._struct_to_dict(response.command_template.headers_template),
                    'base_url': response.command_template.base_url,
                    'timeout': response.command_template.timeout,
                    'retry_count': response.command_template.retry_count,
                    'retry_delay': response.command_template.retry_delay,
                    'required_params': list(response.command_template.required_params),
                    'optional_params': list(response.command_template.optional_params),
                    'api_config_id': response.command_template.api_config_id,
                    'created_at': response.command_template.created_at,
                    'updated_at': response.command_template.updated_at,
                },
                'device_command': {
                    'id': response.device_command.id,
                    'device_id': response.device_command.device_id,
                    'command_template_id': response.device_command.command_template_id,
                    'command_type': response.device_command.command_type,
                    'custom_params': self._struct_to_dict(response.device_command.custom_params),
                    'is_primary': response.device_command.is_primary,
                    'priority': response.device_command.priority,
                    'is_active': response.device_command.is_active,
                    'created_at': response.device_command.created_at,
                    'updated_at': response.device_command.updated_at,
                }
            }
            return context
                
        except grpc.RpcError as e:
            raise Exception(f"gRPC error: {e.details()}")
        except Exception as e:
            raise Exception(f"Failed to get command context: {str(e)}")