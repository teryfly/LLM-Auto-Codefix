# clients/grpc/grpc_client.py

import grpc
from config.config_manager import ConfigManager

# NOTE: Import your generated proto classes here
# from generated_pb2 import YourRequest, YourResponse
# from generated_pb2_grpc import AIProjectHelperStub

class GrpcClient:
    def __init__(self):
        config = ConfigManager.get_config()
        self.channel = grpc.insecure_channel(config.services.grpc_port)
        # self.stub = AIProjectHelperStub(self.channel)

    # def get_project_document(self, project_path: str):
    #     request = YourRequest(project_path=project_path)
    #     return self.stub.GetProjectDocument(request)