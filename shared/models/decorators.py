from functools import wraps

def force_overwrite_auth(auth_field="auth_config"):
    def decorator(func):
        @wraps(func)
        def wrapper(self, instance, validated_data):
            auth_input = validated_data.pop(auth_field, None)
            if auth_input is not None:
                force = auth_input.pop('force_override', False)
                current_config = getattr(instance, auth_field, {}) or {}
                result_config = {}

                for key, value in auth_input.items():
                    if value in ['__HIDDEN__', '***'] and not force:
                        result_config[key] = current_config.get(key)
                    else:
                        result_config[key] = value

                setattr(instance, auth_field, result_config)

            return func(self, instance, validated_data)
        return wrapper
    return decorator
