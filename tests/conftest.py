import subprocess

PROXY_ADDR = "127.0.0.1:8081"


def run_curl_via_proxy(target_url: str, *extra_args: str) -> subprocess.CompletedProcess:
    """Run curl via the nginx HTTP proxy and return the CompletedProcess.

    Usage in tests:

        proc = run_curl_via_proxy("http://127.0.0.1:8080/", "-H", "X-Killswitch: on")
    """

    return subprocess.run(
        [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "-x",
            PROXY_ADDR,
            *extra_args,
            target_url,
        ],
        capture_output=True,
        text=True,
    )
