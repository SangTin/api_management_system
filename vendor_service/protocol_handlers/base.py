from abc import ABC, abstractmethod

class BaseProtocolHandler(ABC):
    @abstractmethod
    def test_connection(self, api_config):
        """Test connection to the API endpoint"""
        pass

    @abstractmethod
    def execute_command(self, api_config, command_template, params):
        """Execute a command using the API configuration"""
        pass

    def render_template(self, template, params):
        """Render template with parameters"""
        if isinstance(template, str):
            return template.format(**params)
        elif isinstance(template, dict):
            return {k: self.render_template(v, params) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.render_template(item, params) for item in template]
        return template