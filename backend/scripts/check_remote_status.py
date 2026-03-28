import os

import paramiko


HOST = os.environ["DEPLOY_HOST"]
USERNAME = os.environ["DEPLOY_USER"]
PASSWORD = os.environ["DEPLOY_PASS"]


def run(client: paramiko.SSHClient, command: str) -> None:
    stdin, stdout, stderr = client.exec_command(command)
    code = stdout.channel.recv_exit_status()
    print(f"--- {command} (rc={code})")
    out = stdout.read().decode("utf-8", errors="ignore").strip()
    err = stderr.read().decode("utf-8", errors="ignore").strip()
    if out:
        print(out)
    if err:
        print(err)


def main() -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        username=USERNAME,
        password=PASSWORD,
        timeout=20,
        auth_timeout=60,
        banner_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        commands = [
            f'echo "{PASSWORD}" | sudo -S systemctl is-active ghostcall-dashboard',
            f'echo "{PASSWORD}" | sudo -S systemctl is-active ghostcall-frontend',
            'ss -ltnp | grep -E ":8000|:3000" || true',
            f'echo "{PASSWORD}" | sudo -S ufw status || true',
        ]
        for item in commands:
            run(client, item)
    finally:
        client.close()


if __name__ == "__main__":
    main()
