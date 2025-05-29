from fastmcp import FastMCP
import subprocess
import re

# Khởi tạo FastMCP server với tên "PingShellServer"
mcp = FastMCP(name="PingShellServer")

# Hàm kiểm tra tính hợp lệ của hostname/IP

def valid_host(host: str) -> bool:
    # Chỉ cho phép ký tự chữ, số, dấu chấm và dấu gạch ngang
    return re.match(r"^[A-Za-z0-9.-]+$", host) is not None

@mcp.tool()
def ping_host(host: str, count: int = 4) -> str:
    """Thực hiện lệnh ping đến host và trả về kết quả."""
    if not valid_host(host):
        return f"Lỗi: Host không hợp lệ '{host}'."
    try:
        completed = subprocess.run(
            ["ping", "-c", str(count), host],
            capture_output=True,
            text=True,
            timeout=30
        )
        if completed.returncode == 0:
            return completed.stdout
        return completed.stdout + "\n" + completed.stderr
    except subprocess.TimeoutExpired:
        return f"Lỗi: Ping tới '{host}' vượt quá thời gian chờ."
    except Exception as e:
        return f"Lỗi khi thực thi ping: {e}"

@mcp.tool()
def run_command(command: str) -> str:
    """Chạy lệnh shell bất kỳ trên máy chủ và trả về kết quả stdout và stderr."""
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = completed.stdout
        if completed.stderr:
            output += "\n" + completed.stderr
        return output
    except subprocess.TimeoutExpired:
        return f"Lỗi: Lệnh '{command}' vượt quá thời gian chờ."
    except Exception as e:
        return f"Lỗi khi chạy lệnh '{command}': {e}"

# Prompt cho các tool
@mcp.prompt()
def ping_host_prompt(host: str, count: int = 4) -> str:
    return f"Ping host '{host}' với {count} gói tin."

@mcp.prompt()
def run_command_prompt(command: str) -> str:
    return f"Run command: {command}"

if __name__ == "__main__":
    # Chạy MCP server qua HTTP trên port 7745
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=7745
    )
