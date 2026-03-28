import os
import tarfile
import tempfile
from pathlib import Path

import paramiko


HOST = os.environ["DEPLOY_HOST"]
USERNAME = os.environ["DEPLOY_USER"]
PASSWORD = os.environ["DEPLOY_PASS"]
PORT = int(os.environ.get("DEPLOY_PORT", "22"))

LOCAL_BACKEND_DIR = Path(__file__).resolve().parents[1]
REMOTE_BASE_DIR = f"/home/{USERNAME}/ghostcall"
REMOTE_BACKEND_DIR = f"{REMOTE_BASE_DIR}/backend"
SERVICE_NAME = "ghostcall-dashboard"
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))

EXCLUDE_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", ".mypy_cache"}
EXCLUDE_FILES = {"ghostcall.db"}


def _connect() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        timeout=20,
        auth_timeout=60,
        banner_timeout=60,
        look_for_keys=False,
        allow_agent=False,
    )
    return client


def _run(client: paramiko.SSHClient, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    if code != 0:
        raise RuntimeError(f"remote command failed({code}): {command}\nstdout:\n{out}\nstderr:\n{err}")
    return out.strip()


def _sudo(command: str) -> str:
    escaped = command.replace('"', '\\"')
    return f'echo "{PASSWORD}" | sudo -S bash -lc "{escaped}"'


def _build_archive() -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="ghostcall_deploy_"))
    archive_path = temp_dir / "backend.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in LOCAL_BACKEND_DIR.rglob("*"):
            relative = item.relative_to(LOCAL_BACKEND_DIR)
            parts = set(relative.parts)
            if EXCLUDE_DIRS.intersection(parts):
                continue
            if item.is_file() and item.name in EXCLUDE_FILES:
                continue
            tar.add(item, arcname=relative)
    return archive_path


def _upload_archive(client: paramiko.SSHClient, local_archive: Path) -> None:
    remote_archive = f"{REMOTE_BASE_DIR}/backend.tar.gz"
    _run(client, f"mkdir -p {REMOTE_BASE_DIR}")
    sftp = client.open_sftp()
    try:
        sftp.put(str(local_archive), remote_archive)
    finally:
        sftp.close()
    _run(client, f"mkdir -p {REMOTE_BACKEND_DIR}")
    _run(client, f"rm -rf {REMOTE_BACKEND_DIR}/*")
    _run(client, f"tar -xzf {remote_archive} -C {REMOTE_BACKEND_DIR}")
    _run(client, f"rm -f {remote_archive}")


def deploy() -> None:
    client = _connect()
    try:
        print("1) 准备远端目录")
        _run(client, f"mkdir -p {REMOTE_BACKEND_DIR}")
        _run(client, f"rm -rf {REMOTE_BACKEND_DIR}/*")

        print("2) 打包并上传后端代码")
        archive_path = _build_archive()
        _upload_archive(client, archive_path)

        print("3) 安装系统依赖与Python环境")
        _run(client, _sudo("apt-get update -y"))
        _run(client, _sudo("apt-get install -y python3 python3-venv python3-pip"))
        _run(client, f"python3 -m venv {REMOTE_BACKEND_DIR}/.venv")
        _run(
            client,
            f"{REMOTE_BACKEND_DIR}/.venv/bin/pip install --upgrade pip "
            "fastapi uvicorn sqlalchemy pydantic-settings pyjwt python-multipart",
        )

        print("4) 初始化数据库并生成mock数据")
        _run(client, f"cd {REMOTE_BACKEND_DIR} && ./.venv/bin/python scripts/seed_mock_data.py")

        print("5) 配置并启动systemd服务")
        service_content = f"""[Unit]
Description=GhostCall Dashboard Service
After=network.target

[Service]
Type=simple
User={USERNAME}
WorkingDirectory={REMOTE_BACKEND_DIR}
ExecStart={REMOTE_BACKEND_DIR}/.venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port {BACKEND_PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
        tmp_service = f"/tmp/{SERVICE_NAME}.service"
        _run(client, f"cat > {tmp_service} << 'EOF'\n{service_content}\nEOF")
        _run(client, _sudo(f"mv {tmp_service} /etc/systemd/system/{SERVICE_NAME}.service"))
        _run(client, _sudo("systemctl daemon-reload"))
        _run(client, _sudo(f"systemctl enable {SERVICE_NAME}"))
        _run(client, _sudo(f"systemctl restart {SERVICE_NAME}"))
        _run(client, _sudo(f"systemctl is-active {SERVICE_NAME}"))

        print("6) 尝试放行防火墙端口")
        try:
            _run(client, _sudo(f"ufw allow {BACKEND_PORT}/tcp"))
        except Exception:
            pass

        print("7) 服务联通性检查")
        local_health = _run(client, f"curl -sS http://127.0.0.1:{BACKEND_PORT}/api/dashboard/overview | head -c 120")
        print(local_health)
        print("部署完成")
    finally:
        client.close()


if __name__ == "__main__":
    deploy()
