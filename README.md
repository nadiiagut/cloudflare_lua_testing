# Cloudflare Lua Testing

A small lab project demonstrating how to:

- install nginx (or OpenResty) with Lua support
- configure nginx to act as an HTTP proxy (usable with `curl -x`)
- trigger a Lua rule on each proxied request

## Requirements

- Linux or macOS
- nginx with Lua support (recommended: OpenResty)
- A local backend HTTP server listening on `127.0.0.1:8080`

## Installing nginx / OpenResty

### macOS (Homebrew)

```bash
brew install openresty
# optional: standard nginx as well
brew install nginx
```

The OpenResty nginx binary is usually available as `openresty` or under
`/usr/local/openresty/nginx/sbin/nginx`.

### Debian / Ubuntu

Standard nginx:

```bash
sudo apt-get update
sudo apt-get install nginx
```

To get Lua support either install OpenResty packages (recommended):

- https://openresty.org/en/download.html

or install the Lua module if available on your distro:

```bash
sudo apt-get install libnginx-mod-http-lua
```

Verify Lua support:

```bash
nginx -V 2>&1 | grep -i lua
```

You should see `http_lua_module` or a Lua-related module flag.

## Project layout

```text
cloudflare_lua_testing/
  README.md
  nginx/
    nginx.conf.sample
    lua/
      example_rule.lua
```

## Sample nginx config

The sample config:

- listens on `127.0.0.1:8081`
- acts as a simple HTTP forward proxy (supports `curl -x` style usage)
- runs a Lua rule before proxying each request

See `nginx/nginx.conf.sample` in this project. A minimal version:

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    lua_package_path  "./nginx/lua/?.lua;;";

    # Simple HTTP forward proxy. Intended for use like:
    #   curl -x 127.0.0.1:8081 http://127.0.0.1:8080/
    # This supports HTTP (not HTTPS CONNECT) proxying.

    server {
        listen 127.0.0.1:8081;

        location / {
            access_by_lua_file ./nginx/lua/example_rule.lua;

            proxy_pass $scheme://$http_host$request_uri;
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Lua rule

The Lua rule is stored in `nginx/lua/example_rule.lua`. It is executed on
each request before proxying to the backend. It can log, modify headers,
or even block certain requests.

A minimal example:

```lua
-- Simple Lua rule executed before proxying the request.

-- Log the method and URI
ngx.log(ngx.INFO, "Lua rule triggered: ", ngx.var.request_method, " ", ngx.var.request_uri)

-- Add a custom header to be seen by the backend
ngx.req.set_header("X-Lua-Rule", "active")

-- Example block rule (commented out by default)
-- if ngx.var.request_uri == "/forbidden" then
--     ngx.status = ngx.HTTP_FORBIDDEN
--     ngx.say("Forbidden by Lua rule")
--     return ngx.exit(ngx.HTTP_FORBIDDEN)
-- end
```

In this lab the actual `example_rule.lua` goes a bit further: it mimics the
logic pattern described in Cloudflare's post *"Cloudflare outage on
December 5, 2025"*. It simulates a ruleset with an `execute` action and a
"killswitch" which skips initialising the `execute` sub-object. Later
code still assumes the sub-object exists and indexes into it, causing a
Lua runtime error when the killswitch is active.

You can toggle the simulated killswitch by:

- sending a request with the header `X-Killswitch: on`, or
- adding `?killswitch=on` to the query string.

When the killswitch is active you should see a 500-style error from
nginx/OpenResty and a Lua error like:

```text
attempt to index field 'execute' (a nil value)
```

in the error log, similar in spirit to the bug described in the
Cloudflare outage post.

## Running the example

1. Start a local backend server on port 8080, for example with Python:

   ```bash
   cd cloudflare_lua_testing
   python -m http.server 8080
   ```

2. In another terminal, start nginx/OpenResty using this project as prefix:

   ```bash
   cd cloudflare_lua_testing
   # Using nginx with Lua support or OpenResty; adjust binary path as needed
   nginx -p "$(pwd)" -c nginx/nginx.conf.sample
   # or
   # openresty -p "$(pwd)" -c nginx/nginx.conf.sample
   ```

   The `-p "$(pwd)"` flag sets the nginx prefix to the project root, so
   relative paths like `./nginx/lua/example_rule.lua` work.

3. Send a test proxied request (nginx as HTTP proxy):

   ```bash
   # Proxies the request through nginx to the backend at 127.0.0.1:8080
   curl -x 127.0.0.1:8081 -i http://127.0.0.1:8080/
   ```

   - The request is sent to nginx on `127.0.0.1:8081`, which then proxies
     it to `http://127.0.0.1:8080/`.
   - The Lua rule runs on the proxy, adding the `X-Lua-Rule: active` header
     and logging to the nginx error log.

4. Stop nginx/OpenResty:

   ```bash
   nginx -s stop
   # or
   # openresty -s stop
   ```

## Notes

- Ports and paths can be adjusted in `nginx/nginx.conf.sample`.
- For more complex logic, create additional Lua modules under
  `nginx/lua/` and require them from `example_rule.lua`.
