import requests
import json
from .base import BaseProtocolHandler
from urllib.parse import urljoin

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

    def execute_command(self, api_config, command_template, params, device=None):
        """Execute HTTP command"""
        try:
            # Prepare URL
            base_url = (
                getattr(device, 'base_url', None)
                or getattr(api_config, 'base_url', None)
                or command_template.base_url
            )
            url = self.render_template(
                urljoin(base_url, command_template.url_template),
                params
            )
            
            # Prepare headers
            headers = {
                **(command_template.headers_template or {}),
                **(api_config.headers_template or {}),
                **(getattr(device, 'headers_template', {}))
            }
            headers = self.render_template(headers, params)

            # Prepare body
            body = {
                **(command_template.body_template or {}),
                **(getattr(device, 'body_template', {}))
            }
            body = self.render_template(body, params)

            # Add authentication
            if getattr(device, 'auth_type', 'none') != 'none':
                auth_type = device.auth_type
                auth_config = device.auth_config
            else:
                auth_type = api_config.auth_type
                auth_config = api_config.auth_config
            
            self._add_auth(headers, auth_type, auth_config)
            
            # Make request
            response = requests.request(
                method=command_template.method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=getattr(device, 'timeout', api_config.timeout),
            )
            
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text
            
            # Process response
            result = {
                'status_code': response.status_code,
                'response': response_data,
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