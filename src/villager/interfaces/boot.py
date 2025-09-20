import typer
from fastapi import FastAPI

from interfaces.interface import boot

app = typer.Typer(
    name="villager",
    no_args_is_help=True
)


@app.command()
def serve(host: str = '0.0.0.0', port: int = 37695):
    """
    Villager server.
    :param host:
    :param port:
    :return:
    """
    _server_app = FastAPI()
    boot(_server_app)
    import uvicorn

    uvicorn.run(_server_app, host=host, port=port)


def main():
    app()
