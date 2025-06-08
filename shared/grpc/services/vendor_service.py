import grpc
from shared.grpc.generated import vendor_service_pb2_grpc, vendor_service_pb2
from google.protobuf.json_format import MessageToDict, ParseDict
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
        class DotDict(dict):
            __getattr__ = dict.get
            __setattr__ = dict.__setitem__

        def to_dotdict(obj):
            print(f"Converting protobuf object to dict: {obj}")
            if isinstance(obj, dict):
                return DotDict({k: to_dotdict(v) for k, v in obj.items()})
            elif isinstance(obj, list):
                return [to_dotdict(item) for item in obj]
            return obj
        
        return to_dotdict(MessageToDict(proto_obj, preserving_proto_field_name=True))
        
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
            request = vendor_service_pb2.ApiConfigRequest(api_config_id=api_config_id)
            response = self.stub.GetApiConfig(request)
            return self._protobuf_to_dict(response)
        except grpc.RpcError as e:
            raise Exception(f"Failed to get API config: {e.details()}")
        except Exception as e:
            raise

    def get_command_template(self, api_config_id, command_type):
        """Get command template for a specific API configuration and command type"""
        try:
            request = vendor_service_pb2.CommandTemplateRequest(api_config_id=api_config_id, command_type=command_type)
            response = self.stub.GetCommandTemplate(request)
            return self._protobuf_to_dict(response)
        except grpc.RpcError as e:
            raise Exception(f"Failed to get command template: {e.details()}")
        except Exception as e:
            raise

    # def get_api_config_by_device(self, device_id):
    #     """Get API configuration by device ID"""
    #     request = vendor_service_pb2.GetApiConfigByDeviceIdRequest(device_id=device_id)
    #     return self.stub.GetApiConfigByDeviceId(request)