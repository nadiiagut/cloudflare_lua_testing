import pytest

from .conftest import run_curl_via_proxy


TARGET_URL = "http://127.0.0.1:8080/"


@pytest.mark.parametrize(
    "description, extra_args, target_url, expected_status",
    [
        (
            "no killswitch (normal path)",
            [],
            TARGET_URL,
            "200",
        ),
        (
            # This case encodes the *intended* behaviour: even when the
            # killswitch is active, the execute rule would still be
            # well-formed and the request would succeed (HTTP 200).
            #
            # With the current buggy Lua code
            #
            #   if rule_result.action == "execute" then
            #       rule_result.execute.results =
            #           ruleset_results[tonumber(rule_result.execute.results_index)]
            #   end
            #
            # the killswitch path leaves rule_result.execute == nil and this
            # line raises "attempt to index field 'execute' (a nil value)",
            # causing nginx/OpenResty to return a 5xx instead. This test is
            # therefore expected to FAIL while the bug is present.
            "killswitch via header (buggy execute path)",
            ["-H", "X-Killswitch: on"],
            TARGET_URL,
            "200",
        ),
        (
            "killswitch via query param (should trigger Lua error / 5xx)",
            [],
            TARGET_URL + "?killswitch=on",
            "500",
        ),
    ],
)
@pytest.mark.prio1
def test_lua_killswitch_paths(description, extra_args, target_url, expected_status):
    """Validate the Lua killswitch behaviour via nginx HTTP proxy.

    These tests assume nginx/OpenResty is running with:

        nginx -p "$(pwd)" -c nginx/nginx.conf.sample

    and a simple HTTP server is listening on 127.0.0.1:8080, for example:

        python -m http.server 8080
    """

    proc = run_curl_via_proxy(target_url, *extra_args)
    http_code = proc.stdout.strip()

    assert (
        http_code == expected_status
    ), f"{description}: expected HTTP {expected_status}, got {http_code}, stderr={proc.stderr}"
