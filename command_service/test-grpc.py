import grpc
from shared.grpc.generated import vendor_service_pb2, vendor_service_pb2_grpc

channel = grpc.insecure_channel("api-gateway:8000")
stub = vendor_service_pb2_grpc.VendorServiceStub(channel)

request = vendor_service_pb2.ApiConfigRequest(
    api_config_id="2c1f098c-c4ec-4ac6-9101-d7f6646f5676"
)

response = stub.GetApiConfig(request)
print(response)