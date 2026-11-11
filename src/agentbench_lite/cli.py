import typer
import uvicorn
app = typer.Typer(help="AgentBench Lite command line")
@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Start the local API server."""
    uvicorn.run("agentbench_lite.api:app", host=host, port=port, reload=reload)
if __name__ == "__main__": app()
