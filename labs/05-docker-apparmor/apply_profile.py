"""Run the Flask container under the AppArmor profile and confirm it is applied.

Requires: Linux host with AppArmor, the profile already loaded
(see deploy.sh), and `pip install -r requirements-sdk.txt`.
"""
import sys

import lab_common as lc


def main():
    cli = lc.client()
    lc.build_image(cli)

    container = lc.run_container(cli, "lab5-confined", lc.PROFILE)
    try:
        info = cli.api.inspect_container(container.id)
        security_opt = info["HostConfig"].get("SecurityOpt") or []
        applied = info.get("AppArmorProfile")
        print(f"HostConfig.SecurityOpt : {security_opt}")
        print(f"AppArmorProfile        : {applied}")

        if f"apparmor={lc.PROFILE}" not in security_opt or applied != lc.PROFILE:
            print("FAIL: profile is not applied to the container")
            return 1

        port = lc.host_port(cli, container)
        status, body = lc.wait_for_http(f"http://127.0.0.1:{port}/")
        print(f"GET / -> {status} {body.strip()!r}")
        if status != 200:
            print("FAIL: app is not serving under the profile")
            return 1

        print("PASS: profile applied and the app still serves requests")
        return 0
    finally:
        lc.remove(container)


if __name__ == "__main__":
    sys.exit(main())
