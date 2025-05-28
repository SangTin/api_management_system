local http = require "resty.http"
local cjson = require "cjson"
local redis = require "resty.redis"

local UserServiceAuthHandler = {}

UserServiceAuthHandler.PRIORITY = 1000  -- Execute before other auth plugins
UserServiceAuthHandler.VERSION = "1.0.0"

local function get_redis_connection(conf)
  local red = redis:new()
  red:set_timeout(1000)
  
  local ok, err = red:connect(conf.redis_host, conf.redis_port)
  if not ok then
    kong.log.err("Failed to connect to Redis: ", err)
    return nil
  end
  
  if conf.redis_database > 0 then
    red:select(conf.redis_database)
  end
  
  return red
end

local function cache_auth_result(conf, cache_key, auth_data)
  local red = get_redis_connection(conf)
  if not red then
    return false
  end
  
  local ok, err = red:setex(cache_key, conf.cache_ttl, cjson.encode(auth_data))
  if not ok then
    kong.log.err("Failed to cache auth result: ", err)
    return false
  end
  
  red:set_keepalive(10000, 100)
  return true
end

local function get_cached_auth_result(conf, cache_key)
  local red = get_redis_connection(conf)
  if not red then
    return nil
  end
  
  local res, err = red:get(cache_key)
  red:set_keepalive(10000, 100)
  
  if not res or res == ngx.null then
    return nil
  end
  
  local ok, auth_data = pcall(cjson.decode, res)
  if not ok then
    kong.log.err("Failed to decode cached auth data: ", auth_data)
    return nil
  end
  
  return auth_data
end

local function verify_token_with_user_service(conf, token)
  local httpc = http.new()
  httpc:set_timeout(conf.timeout)
  
  local res, err = httpc:request_uri(conf.user_service_url .. "/api/auth/verify-token/", {
    method = "GET",
    headers = {
      ["Authorization"] = "Bearer " .. token,
      ["Content-Type"] = "application/json",
      ["User-Agent"] = "Kong-Auth-Plugin/1.0.0"
    }
  })
  
  if not res then
    kong.log.err("Failed to call user service: ", err)
    return nil, "User service unavailable"
  end
  
  if res.status ~= 200 then
    kong.log.info("User service returned status: ", res.status)
    return nil, "Authentication failed"
  end
  
  local ok, auth_data = pcall(cjson.decode, res.body)
  if not ok then
    kong.log.err("Failed to decode user service response: ", auth_data)
    return nil, "Invalid response from user service"
  end
  
  if not auth_data.valid then
    return nil, auth_data.error or "Token validation failed"
  end
  
  return auth_data, nil
end

local function should_bypass_auth(conf, path)
  for _, bypass_path in ipairs(conf.bypass_paths) do
    if string.match(path, bypass_path) then
      return true
    end
  end
  return false
end

function UserServiceAuthHandler:access(conf)
  local path = kong.request.get_path()
  
  -- Check if this path should bypass authentication
  if should_bypass_auth(conf, path) then
    kong.log.info("Bypassing authentication for path: ", path)
    return
  end
  
  -- Extract authorization header
  local headers = kong.request.get_headers()
  local authorization = headers["authorization"]
  
  if not authorization then
    return kong.response.exit(401, {
      error = "Authentication required",
      message = "Authorization header is missing"
    })
  end
  
  -- Extract token from Authorization header
  local token = authorization:match("Bearer%s+(.+)")
  if not token then
    return kong.response.exit(401, {
      error = "Invalid authorization format",
      message = "Authorization header must be 'Bearer <token>'"
    })
  end
  
  -- Create cache key
  local cache_key = "auth:" .. ngx.md5(token)
  
  -- Try to get cached authentication result
  local auth_data = get_cached_auth_result(conf, cache_key)
  
  if not auth_data then
    -- Cache miss, verify token with user service
    kong.log.info("Cache miss, verifying token with user service")
    
    local verified_data, err = verify_token_with_user_service(conf, token)
    if not verified_data then
      return kong.response.exit(401, {
        error = "Authentication failed",
        message = err
      })
    end
    
    auth_data = verified_data
    
    -- Cache the result
    cache_auth_result(conf, cache_key, auth_data)
    kong.log.info("Token verified and cached for user: ", auth_data.username)
  else
    kong.log.info("Using cached authentication for user: ", auth_data.username)
  end
  
  -- Add user information to request headers for downstream services
  kong.service.request.set_header("X-User-ID", auth_data.user_id)
  kong.service.request.set_header("X-Username", auth_data.username)
  kong.service.request.set_header("X-User-Role", auth_data.role)
  kong.service.request.set_header("X-Organization-ID", tostring(auth_data.organization_id or ""))
  kong.service.request.set_header("X-Clearance-Level", tostring(auth_data.clearance_level or 1))
  kong.service.request.set_header("X-Emergency-Override", tostring(auth_data.emergency_override or false))
  kong.service.request.set_header("X-Authenticated", "true")
  kong.service.request.set_header("X-Auth-Source", "kong-middleware")
  
  -- Remove original authorization header to prevent token leakage
  kong.service.request.clear_header("Authorization")
  
  kong.log.info("Authentication successful for user: ", auth_data.username, " (", auth_data.user_id, ")")
end

return UserServiceAuthHandler