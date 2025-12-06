-- example_rule.lua
-- Minimal illustration of the pattern described in Cloudflare's
-- "Cloudflare outage on December 5, 2025":
-- - a rule with action "execute"
-- - a killswitch that skips initialising `execute`
-- - later code that unconditionally indexes `rule_result.execute`

-- Toggle the simulated killswitch via header or query parameter:
--   X-Killswitch: on
--   ?killswitch=on

local killswitch_active =
    (ngx.req.get_headers()["X-Killswitch"] == "on") or
    (ngx.var.arg_killswitch == "on")

-- Pretend this is part of a larger ruleset system.
local ruleset_results = {
    [1] = { action = "log" },
}

local rule_result = { action = "execute", execute = nil }

if not killswitch_active then
    -- Normal path: create the `execute` sub-object as downstream code expects.
    rule_result.execute = { results_index = "1", results = nil }
end

-- Buggy pattern: assume `execute` always exists for action == "execute".
if rule_result.action == "execute" then
    rule_result.execute.results = ruleset_results[tonumber(rule_result.execute.results_index)]
end
