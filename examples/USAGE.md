# Example usage

This project configures nginx as a small HTTP forward proxy that runs a Lua
rule on each proxied request. These examples assume you start nginx with:

```bash
cd cloudflare_lua_testing
nginx -p "$(pwd)" -c nginx/nginx.conf.sample
```

## Basic HTTP proxying with curl

With a backend server running on `127.0.0.1:8080` (for example,
`python -m http.server 8080`), you can send requests through nginx using the
`-x` (proxy) option:

```bash
curl -x 127.0.0.1:8081 -v http://127.0.0.1:8080/
```

- curl connects to nginx on `127.0.0.1:8081`.
- nginx proxies the request to `http://127.0.0.1:8080/`.
- the Lua rule in `nginx/lua/example_rule.lua` runs before proxying.

## Triggering the simulated killswitch error

The Lua rule includes a simulated "killswitch" inspired by the
Cloudflare 5 December 2025 outage. It can be toggled via a header or
query parameter.

When the killswitch is **off** (default), the rule initialises internal
state and proxying succeeds.

When the killswitch is **on**, the rule skips initialisation of a nested
`execute` object, but later code still assumes it exists, which triggers
a Lua runtime error ("attempt to index field 'execute' (a nil value)").

### Using a header

```bash
curl -x 127.0.0.1:8081 -v \
  -H 'X-Killswitch: on' \
  http://127.0.0.1:8080/
```

### Using a query parameter

```bash
curl -x 127.0.0.1:8081 -v \
  'http://127.0.0.1:8080/?killswitch=on'
```

In both cases you should see a 5xx error from nginx/OpenResty and the
Lua error in the nginx error log.
