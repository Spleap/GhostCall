import os
import tarfile
import tempfile
from pathlib import Path

import paramiko


HOST = os.environ["DEPLOY_HOST"]
USERNAME = os.environ["DEPLOY_USER"]
PASSWORD = os.environ["DEPLOY_PASS"]
PORT = int(os.environ.get("DEPLOY_PORT", "22"))

LOCAL_FRONTEND_DIR = Path(__file__).resolve().parents[1]
REMOTE_BASE_DIR = f"/home/{USERNAME}/ghostcall"
REMOTE_FRONTEND_DIR = f"{REMOTE_BASE_DIR}/frontend"
SERVICE_NAME = "ghostcall-frontend"
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "3000"))
BACKEND_ORIGIN = os.environ.get("FRONTEND_BACKEND_ORIGIN", "http://127.0.0.1:8000")

EXCLUDE_DIRS = {".git", ".next", "node_modules", ".vercel", ".turbo"}


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
    temp_dir = Path(tempfile.mkdtemp(prefix="ghostcall_frontend_"))
    archive_path = temp_dir / "frontend.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in LOCAL_FRONTEND_DIR.rglob("*"):
            relative = item.relative_to(LOCAL_FRONTEND_DIR)
            parts = set(relative.parts)
            if EXCLUDE_DIRS.intersection(parts):
                continue
            tar.add(item, arcname=relative)
    return archive_path


def _upload_archive(client: paramiko.SSHClient, local_archive: Path) -> None:
    remote_archive = f"{REMOTE_BASE_DIR}/frontend.tar.gz"
    _run(client, f"mkdir -p {REMOTE_BASE_DIR}")
    sftp = client.open_sftp()
    try:
        sftp.put(str(local_archive), remote_archive)
    finally:
        sftp.close()
    _run(client, f"mkdir -p {REMOTE_FRONTEND_DIR}")
    _run(client, f"rm -rf {REMOTE_FRONTEND_DIR}/*")
    _run(client, f"tar -xzf {remote_archive} -C {REMOTE_FRONTEND_DIR}")
    _run(client, f"rm -f {remote_archive}")


def deploy() -> None:
    client = _connect()
    try:
        print("1) 打包并上传前端代码")
        archive_path = _build_archive()
        _upload_archive(client, archive_path)

        print("2) 安装 Node.js 运行环境")
        _run(client, _sudo("apt-get update -y"))
        _run(client, _sudo("apt-get install -y curl"))
        _run(client, _sudo("curl -fsSL https://deb.nodesource.com/setup_22.x | bash -"))
        _run(client, _sudo("apt-get install -y nodejs"))

        print("3) 安装依赖并构建前端")
        _run(client, f"cd {REMOTE_FRONTEND_DIR} && npm install")
        _run(client, f"cd {REMOTE_FRONTEND_DIR} && BACKEND_ORIGIN={BACKEND_ORIGIN} npm run build")

        print("4) 配置并启动前端服务")
        service_content = f"""[Unit]
Description=GhostCall Frontend Service
After=network.target

[Service]
Type=simple
User={USERNAME}
WorkingDirectory={REMOTE_FRONTEND_DIR}
Environment=BACKEND_ORIGIN={BACKEND_ORIGIN}
ExecStart=/usr/bin/npm run start -- --hostname 0.0.0.0 --port {FRONTEND_PORT}
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

        print("5) 尝试放行前端端口")
        try:
            _run(client, _sudo(f"ufw allow {FRONTEND_PORT}/tcp"))
        except Exception:
            pass

        print("6) 前端服务联通性检查")
        html = _run(client, f"curl -sS http://127.0.0.1:{FRONTEND_PORT} | head -c 120")
        print(html)
        print("前端部署完成")
    finally:
        client.close()


if __name__ == "__main__":
    deploy()
