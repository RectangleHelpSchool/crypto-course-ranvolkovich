from contextlib import asynccontextmanager, AsyncExitStack
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from approvalfetcher.clients.coingecko_client import CoinGeckoClient
from approvalfetcher.clients.web3_client import Web3Client
from approvalfetcher.routes.approval import router as approval_router
from approvalfetcher.routes.system import router as system_router
from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.services.price_service import PriceService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with AsyncExitStack() as stack:
        web3_client = await stack.enter_async_context(Web3Client())
        coingecko_client = await stack.enter_async_context(CoinGeckoClient())

        app.state.web3_client = web3_client
        app.state.coingecko_client = coingecko_client
        app.state.approval_service = ApprovalService(web3_client)
        app.state.price_service = PriceService(coingecko_client)

        print("✓ Initialized Web3Client, CoinGeckoClient, ApprovalService, and PriceService")
        yield
        print("✓ Cleaned up clients")


app = FastAPI(title="ERC20 Approvals API", version="0.1.0", lifespan=lifespan)

app.include_router(approval_router)
app.include_router(system_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
