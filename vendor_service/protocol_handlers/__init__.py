from .http_handler import HTTPHandler

PROTOCOL_HANDLERS = {
    'http': HTTPHandler,
}

def get_protocol_handler(protocol):
    handler_class = PROTOCOL_HANDLERS.get(protocol)
    if not handler_class:
        raise ValueError(f"Unsupported protocol: {protocol}")
    return handler_class()