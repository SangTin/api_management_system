local typedefs = require "kong.db.schema.typedefs"

return {
    name = "user-service-auth",
    fields = {{
        consumer = typedefs.no_consumer
    }, {
        protocols = typedefs.protocols_http
    }, {
        config = {
            type = "record",
            fields = {{
                user_service_url = {
                    type = "string",
                    required = true
                }
            }, {
                cache_ttl = {
                    type = "number",
                    default = 300
                }
            }, {
                timeout = {
                    type = "number",
                    default = 5000
                }
            }, {
                redis_host = {
                    type = "string",
                    default = "redis"
                }
            }, {
                redis_port = {
                    type = "number",
                    default = 6379
                }
            }, {
                redis_database = {
                    type = "number",
                    default = 0
                }
            }, {
                bypass_paths = {
                    type = "array",
                    elements = {
                        type = "string"
                    },
                    default = {}
                }
            }, {
                required_headers = {
                    type = "array",
                    elements = {
                        type = "string"
                    },
                    default = {"authorization"}
                }
            }}
        }
    }}
}
