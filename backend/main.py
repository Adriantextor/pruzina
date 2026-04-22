import asyncio
import uvicorn
from restapi_server import app
from websocket_server import start_websocket_server


async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=8081, log_level="info")
    server = uvicorn.Server(config)
    ws_task = asyncio.create_task(start_websocket_server())
    await server.serve()
    ws_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
