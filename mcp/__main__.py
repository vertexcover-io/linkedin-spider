import os
import sys
from typing import Annotated, Callable

from cyclopts import App, Parameter

app = App(name="linkedin-mcp")


def configure_and_run_mcp_server(transport: str, **kwargs):
    from .server_sse import configure_mcp_server

    try:
        configure_mcp_server(transport=transport, **kwargs)
    except KeyboardInterrupt:
        print("Aborted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def get_host_port() -> tuple[str, int]:
    return os.getenv("HOST", "127.0.0.1"), int(os.getenv("PORT", "8000"))


TRANSPORT_HANDLERS: dict[str, Callable[[], None]] = {
    "stdio": lambda: configure_and_run_mcp_server("stdio"),
    "sse": lambda: configure_and_run_mcp_server("sse", host_port := get_host_port())[0],
    "http": lambda: configure_and_run_mcp_server("http", host_port := get_host_port())[0],
    "streamable-http": lambda: configure_and_run_mcp_server("streamable-http", host_port := get_host_port())[0],
}


@app.default
def main():
    transport = os.getenv("TRANSPORT", "").lower()

    handler = TRANSPORT_HANDLERS.get(transport)
    if handler:
        handler()
    else:
        if transport:
            print(f"Unsupported transport: {transport}")
            print("Supported transports:", ", ".join(TRANSPORT_HANDLERS))
            sys.exit(1)
        app.help_print()


@app.command(name="stdio")
def run_stdio_server():
    configure_and_run_mcp_server("stdio")


def make_network_command(transport_name: str):
    def command(
        *,
        host: Annotated[str, Parameter(name=("-H", "--host"))] = "127.0.0.1",
        port: Annotated[int, Parameter(name=("-p", "--port"))] = 8000,
    ):
        configure_and_run_mcp_server(transport_name, host=host, port=port)

    command.__name__ = f"run_{transport_name.replace('-', '_')}_server"
    app.command(name=transport_name)(command)


for transport in ("http", "sse", "streamable-http"):
    make_network_command(transport)


if __name__ == "__main__":
    app()
