import re
import json
import uuid
from typing import Any, Dict, Union
from datetime import datetime

class TemplateRenderer:
    """Enhanced template renderer with support for advanced features"""
    
    def __init__(self):
        self.builtin_functions = {
            'now': lambda: datetime.now().isoformat(),
            'timestamp': lambda: int(datetime.now().timestamp()),
            'uuid': lambda: str(uuid.uuid4()),
        }
    
    def render_template(self, template: Any, params: Dict[str, Any]) -> Any:
        """
        Render template with parameters
        
        Supports:
        - Simple replacement: {device_id}
        - Nested parameters: {device.id}
        - Functions: {now()}, {timestamp()}
        - Conditional: {value|default_value}
        - Type conversion: {value:int}, {value:float}
        """
        if isinstance(template, str):
            return self._render_string(template, params)
        elif isinstance(template, dict):
            return {k: self.render_template(v, params) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.render_template(item, params) for item in template]
        return template
    
    def _render_string(self, template: str, params: Dict[str, Any]) -> str:
        """Render string template with advanced features"""
        
        # Pattern để match các placeholder
        pattern = r'\{([^}]+)\}'
        
        def replacer(match):
            placeholder = match.group(1)
            return self._resolve_placeholder(placeholder, params)
        result = re.sub(pattern, replacer, template)
        return result
    
    def _resolve_placeholder(self, placeholder: str, params: Dict[str, Any]) -> str:
        """Resolve single placeholder"""
        try:
            # Check for type conversion {value:type}
            if ':' in placeholder:
                key, type_hint = placeholder.split(':', 1)
                key = key.strip()  # Remove any whitespace
                value = self._get_value(key, params)
                return self._convert_type(value, type_hint)
            
            # Check for default value {value|default}
            elif '|' in placeholder:
                key, default = placeholder.split('|', 1)
                key = key.strip()  # Remove any whitespace
                try:
                    return str(self._get_value(key, params))
                except (KeyError, AttributeError):
                    return default
            
            # Check for function call {func()}
            elif placeholder.endswith('()'):
                func_name = placeholder[:-2].strip()
                if func_name in self.builtin_functions:
                    return str(self.builtin_functions[func_name]())
                raise ValueError(f"Unknown function: {func_name}")
            
            # Simple replacement
            else:
                key = placeholder.strip()  # Remove any whitespace
                return str(self._get_value(key, params))
                
        except Exception as e:
            # Fallback: return placeholder as-is if resolution fails
            return f"{{{placeholder}}}"
    
    def _get_value(self, key: str, params: Dict[str, Any]) -> Any:
        """Get value from params, supporting nested keys"""
        # Support nested keys like 'device.id'
        if '.' in key:
            parts = key.split('.')
            value = params
            for part in parts:
                if isinstance(value, list):
                    try:
                        part = int(part)
                    except ValueError:
                        raise KeyError(f"Invalid index: {part}")
                    value = value[part]
                if isinstance(value, dict):
                    value = value[part]
                else:
                    value = getattr(value, part)
            return value
        else:
            return params[key]
    
    def _convert_type(self, value: Any, type_hint: str) -> str:
        """Convert value to specified type"""
        if type_hint == 'int':
            if isinstance(value, str) and '.' in value:
                return str(int(float(value)))
            return str(int(value))
        elif type_hint == 'float':
            return str(float(value))
        elif type_hint == 'bool':
            return str(bool(value)).lower()
        elif type_hint == 'json':
            return json.dumps(value)
        else:
            return str(value)