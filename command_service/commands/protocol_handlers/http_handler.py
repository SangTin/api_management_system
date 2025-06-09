import requests
import json
from .base import BaseProtocolHandler
from urllib.parse import urljoin

class HTTPHandler(BaseProtocolHandler):
    
    def safe_get(self, obj, key, default=None):
        """Safely get attribute from object or dict"""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    
    def test_connection(self, api_config):
        """Test HTTP connection"""
        try:
            url = self.safe_get(api_config, 'base_url')
            if not url:
                raise Exception("No base URL provided")
                
            headers = self.safe_get(api_config, 'headers_template', {}).copy()
            
            # Add authentication if configured
            auth_type = self.safe_get(api_config, 'auth_type', 'none')
            auth_config = self.safe_get(api_config, 'auth_config', {})
            self._add_auth(headers, auth_type, auth_config)
            
            timeout = self.safe_get(api_config, 'timeout', 30)
            response = requests.get(url, headers=headers, timeout=timeout)
            
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
                self.safe_get(device, 'base_url') if device else None
            ) or (
                self.safe_get(api_config, 'base_url')
            ) or (
                self.safe_get(command_template, 'base_url')
            )
            
            if not base_url:
                raise Exception("No base URL found in device, api_config, or command_template")
            
            url_template = self.safe_get(command_template, 'url_template', '')
            if not url_template:
                url = base_url
            else:
                url = urljoin(base_url, url_template)
            
            url = self.render_template(url, params)
            
            # Prepare headers
            headers = {}
            headers.update(self.safe_get(command_template, 'headers_template', {}))
            headers.update(self.safe_get(api_config, 'headers_template', {}))
            if device:
                headers.update(self.safe_get(device, 'headers_template', {}))
            
            headers = self.render_template(headers, params)

            # Prepare body
            body = {}
            body.update(self.safe_get(command_template, 'body_template', {}))
            if device:
                body.update(self.safe_get(device, 'body_template', {}))
            
            body = self.render_template(body, params)

            # Add authentication
            if device and self.safe_get(device, 'auth_type', 'none') != 'none':
                auth_type = self.safe_get(device, 'auth_type')
                auth_config = self.safe_get(device, 'auth_config', {})
            else:
                auth_type = self.safe_get(api_config, 'auth_type', 'none')
                auth_config = self.safe_get(api_config, 'auth_config', {})
            
            self._add_auth(headers, auth_type, auth_config)
            
            # Make request
            method = self.safe_get(command_template, 'method', 'POST')
            timeout = (
                self.safe_get(device, 'timeout') if device else None
            ) or self.safe_get(api_config, 'timeout', 30)
            
            print(f"Making HTTP request: {method} {url}")
            print(f"Headers: {headers}")
            print(f"Body: {body}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=timeout,
            )
            
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text
            
            # Process response
            result = {
                'status_code': response.status_code,
                'response': response_data,
                'success': response.status_code < 400,
                'url': url,
                'method': method
            }
            
            print(f"HTTP response: {result}")
            return result
            
        except Exception as e:
            print(f"HTTP command execution error: {e}")
            raise Exception(f"HTTP command execution failed: {str(e)}")

    def _add_auth(self, headers, auth_type, auth_config):
        """Add authentication to headers"""
        if not auth_type or auth_type == 'none':
            return
            
        if not auth_config:
            auth_config = {}
            
        if auth_type == 'bearer':
            token = auth_config.get('token')
            if token:
                headers['Authorization'] = f"Bearer {token}"
        elif auth_type == 'basic':
            username = auth_config.get('username')
            password = auth_config.get('password')
            if username and password:
                import base64
                credentials = f"{username}:{password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers['Authorization'] = f"Basic {encoded}"
        elif auth_type == 'api_key':
            api_key = auth_config.get('api_key')
            if api_key:
                key_name = auth_config.get('key_name', 'X-API-Key')
                headers[key_name] = api_key