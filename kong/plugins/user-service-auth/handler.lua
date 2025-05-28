local http = require "resty.http"
local cjson = require "cjson"
local redis = require "resty.redis"

local UserServiceAuthHandler = {}

UserServiceAuthHandler.PRIORITY = 1000  -- Execute before other auth plugins
UserServiceAuthHandler.VERSION = "1.1.0"

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

local function join_url(base, path)
  if base:sub(-1) == "/" and path:sub(1, 1) == "/" then
    return base .. path:sub(2)
  elseif base:sub(-1) ~= "/" and path:sub(1, 1) ~= "/" then
    return base .. "/" .. path
  else
    return base .. path
  end
end

local function verify_token_with_user_service(conf, token)
  local httpc = http.new()
  httpc:set_timeout(conf.timeout)

  local url = join_url(conf.user_service_url, conf.auth_endpoint)
  local res, err = httpc:request_uri(url, {
    method = "GET",
    headers = {
      ["Authorization"] = "Bearer " .. token,
      ["Content-Type"] = "application/json",
      ["User-Agent"] = "Kong-Auth-Plugin/1.1.0"
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
  -- Check configured bypass paths
  for _, bypass_path in ipairs(conf.bypass_paths) do
    if string.match(path, bypass_path) then
      return true
    end
  end
  return false
end

local function set_anonymous_headers()
  -- Set anonymous user headers
  kong.service.request.set_header("X-User-ID", "")
  kong.service.request.set_header("X-Username", "")
  kong.service.request.set_header("X-User-Role", "")
  kong.service.request.set_header("X-Organization-ID", "")
  kong.service.request.set_header("X-Clearance-Level", "1")
  kong.service.request.set_header("X-Emergency-Override", "false")
  kong.service.request.set_header("X-Authenticated", "false")
  kong.service.request.set_header("X-Auth-Source", "kong-middleware")
end

local function set_authenticated_headers(auth_data)
  -- Set authenticated user headers với NULL handling
  kong.service.request.set_header("X-User-ID", auth_data.user_id or "")
  kong.service.request.set_header("X-Username", auth_data.username or "")
  kong.service.request.set_header("X-User-Role", auth_data.role or "")
  
  -- Handle organization_id NULL properly
  local org_id = ""
  if auth_data.organization_id and auth_data.organization_id ~= ngx.null then
    org_id = tostring(auth_data.organization_id)
  end
  kong.service.request.set_header("X-Organization-ID", org_id)
  
  -- Handle other nullable fields
  local clearance_level = "1"
  if auth_data.clearance_level and auth_data.clearance_level ~= ngx.null then
    clearance_level = tostring(auth_data.clearance_level)
  end
  kong.service.request.set_header("X-Clearance-Level", clearance_level)
  
  local emergency_override = "false"
  if auth_data.emergency_override and auth_data.emergency_override ~= ngx.null then
    emergency_override = tostring(auth_data.emergency_override)
  end
  kong.service.request.set_header("X-Emergency-Override", emergency_override)
  
  kong.service.request.set_header("X-Authenticated", "true")
  kong.service.request.set_header("X-Auth-Source", "kong-middleware")
end

function UserServiceAuthHandler:access(conf)
  local path = kong.request.get_path()
  
  -- Check if this path should completely bypass authentication
  if should_bypass_auth(conf, path) then
    kong.log.info("Bypassing authentication for path: ", path)
    kong.service.request.set_header("X-Auth-Bypass", "true")
    return
  end
  
  -- Extract authorization header
  local headers = kong.request.get_headers()
  local authorization = headers["authorization"]
  
  -- No authorization header = anonymous user
  if not authorization then
    kong.log.info("No authorization header, proceeding as anonymous user")
    set_anonymous_headers()
    -- Remove any existing authorization header
    kong.service.request.clear_header("Authorization")
    return
  end
  
  -- Extract token from Authorization header
  local token = authorization:match("Bearer%s+(.+)")
  if not token then
    kong.log.info("Invalid authorization format, proceeding as anonymous user")
    set_anonymous_headers()
    kong.service.request.clear_header("Authorization")
    return
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
      -- Token verification failed, proceed as anonymous
      kong.log.info("Token verification failed: ", err, ". Proceeding as anonymous user")
      set_anonymous_headers()
      kong.service.request.clear_header("Authorization")
      return
    end
    
    auth_data = verified_data
    
    -- Cache the result
    cache_auth_result(conf, cache_key, auth_data)
    kong.log.info("Token verified and cached for user: ", auth_data.username)
  else
    kong.log.info("Using cached authentication for user: ", auth_data.username)
  end
  
  -- Set authenticated user headers
  set_authenticated_headers(auth_data)
  
  -- Remove original authorization header to prevent token leakage
  kong.service.request.clear_header("Authorization")
  
  kong.log.info("Authentication successful for user: ", auth_data.username, " (", auth_data.user_id, ")")
end

return UserServiceAuthHandler