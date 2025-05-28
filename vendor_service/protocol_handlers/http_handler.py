import requests
import json
from .base import BaseProtocolHandler

class HTTPHandler(BaseProtocolHandler):
    def test_connection(self, api_config):
        """Test HTTP connection"""
        try:
            url = api_config.base_url
            headers = api_config.headers_template.copy()
            
            # Add authentication if configured
            self._add_auth(headers, api_config.auth_type, api_config.auth_config)
            
            response = requests.get(url, headers=headers, timeout=api_config.timeout)
            return {
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'success': response.status_code < 400
            }
        except Exception as e:
            raise Exception(f"HTTP connection test failed: {str(e)}")

    def execute_command(self, api_config, command_template, params):
        """Execute HTTP command"""
        try:
            # Render templates
            url = self.render_template(
                api_config.base_url + command_template.url_template, 
                params
            )
            headers = self.render_template(command_template.headers_template, params)
            body = self.render_template(command_template.body_template, params)
            
            # Add base headers
            headers.update(api_config.headers_template)
            
            # Add authentication
            self._add_auth(headers, api_config.auth_type, api_config.auth_config)
            
            # Make request
            response = requests.request(
                method=command_template.method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=api_config.timeout
            )
            
            # Process response
            result = {
                'status_code': response.status_code,
                'response': response.json() if response.content else None,
                'success': response.status_code < 400
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"HTTP command execution failed: {str(e)}")

    def _add_auth(self, headers, auth_type, auth_config):
        """Add authentication to headers"""
        if auth_type == 'bearer':
            headers['Authorization'] = f"Bearer {auth_config.get('token')}"
        elif auth_type == 'basic':
            import base64
            credentials = f"{auth_config.get('username')}:{auth_config.get('password')}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"
        elif auth_type == 'api_key':
            key_name = auth_config.get('key_name', 'X-API-Key')
            headers[key_name] = auth_config.get('api_key')