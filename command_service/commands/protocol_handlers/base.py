from abc import ABC, abstractmethod
from .template_renderer import TemplateRenderer

class BaseProtocolHandler(ABC):
    def __init__(self):
        self.renderer = TemplateRenderer()
    
    @abstractmethod
    def test_connection(self, api_config):
        """Test connection to the API endpoint"""
        pass

    @abstractmethod
    def execute_command(self, api_config, command_template, params, device=None):
        """Execute a command using the API configuration"""
        pass

    def render_template(self, template, params):
        """Render template with parameters using enhanced renderer"""
        return self.renderer.render_template(template, params)