import uvicorn
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from approvalfetcher.routes.approval import router as approval_router
from approvalfetcher.routes.system import router as system_router
from approvalfetcher.clients.web3_client import Web3Client
from approvalfetcher.services.approval_service import ApprovalService

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    client = Web3Client()
    await client.__aenter__()
    app.state.web3_client = client
    app.state.approval_service = ApprovalService(client)
    print("✓ Initialized Web3Client and ApprovalService")

    yield

    # Shutdown: Cleanup
    await client.__aexit__(None, None, None)
    print("✓ Cleaned up Web3Client")

app = FastAPI(title="ERC20 Approvals API", version="0.1.0", lifespan=lifespan)

app.include_router(approval_router)
app.include_router(system_router)

if __name__ == "__main__":
    uvicorn.run("approvalfetcher.main_server:app", host="127.0.0.1", port=8000, reload=True)