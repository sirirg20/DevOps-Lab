"""Compare a confined container with an unconfined control.

Each probe runs inside both containers. A probe the profile should block must
fail in the confined container and succeed in the control; that pairing shows
the profile, not something else, caused the failure. Probes use the Python
interpreter so each rule is tested on its own (a confined `cat` would fail at
exec time and never reach the file read).

Requires a Linux host with AppArmor and the profile loaded (see deploy.sh).
"""
import sys

import lab_common as lc

PY = "python"
PROBES = [
    # (description, command, blocked_by_profile)
    ("python runs and prints", [PY, "-c", "print('ok')"], False),
    ("read /etc/passwd", [PY, "-c", "open('/etc/passwd').read()"], True),
    ("write /var/tmp/probe", [PY, "-c", "open('/var/tmp/probe','w').write('x')"], True),
    ("write /tmp/probe", [PY, "-c", "open('/tmp/probe','w').write('x')"], False),
    ("exec /bin/sh", ["/bin/sh", "-c", "true"], True),
    ("exec /usr/bin/env", ["/usr/bin/env", "true"], True),
]


def run_probe(container, cmd):
    code, out = container.exec_run(cmd, demux=False)
    return code, (out or b"").decode(errors="replace").strip().splitlines()[-1:]


def main():
    cli = lc.client()
    lc.build_image(cli)
    confined = lc.run_container(cli, "lab5-confined", lc.PROFILE)
    control = lc.run_container(cli, "lab5-control", "unconfined")
    failures = 0
    try:
        print(f"{'probe':26} {'expect':8} {'confined':10} {'control':8} result")
        for desc, cmd, should_block in PROBES:
            c_code, _ = run_probe(confined, cmd)
            u_code, _ = run_probe(control, cmd)
            blocked = c_code != 0
            control_ok = u_code == 0
            good = (blocked == should_block) and control_ok
            failures += not good
            print(
                f"{desc:26} {'block' if should_block else 'allow':8} "
                f"exit={c_code:<5} exit={u_code:<3} {'PASS' if good else 'FAIL'}"
            )
        print("ALL CHECKS PASSED" if not failures else f"{failures} CHECK(S) FAILED")
        return 1 if failures else 0
    finally:
        lc.remove(confined)
        lc.remove(control)


if __name__ == "__main__":
    sys.exit(main())
