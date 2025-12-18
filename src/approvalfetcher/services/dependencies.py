from typing import cast
from fastapi import Request
from approvalfetcher.clients.web3_client import Web3Client
from approvalfetcher.clients.coingecko_client import CoinGeckoClient
from approvalfetcher.services.approval_service import ApprovalService
from approvalfetcher.services.price_service import PriceService

def get_web3_client(request: Request) -> Web3Client:
    return cast(Web3Client, request.app.state.web3_client)

def get_coingecko_client(request: Request) -> CoinGeckoClient:
    return cast(CoinGeckoClient, request.app.state.coingecko_client)

def get_approval_service(request: Request) -> ApprovalService:
    return cast(ApprovalService, request.app.state.approval_service)

def get_price_service(request: Request) -> PriceService:
    return cast(PriceService, request.app.state.price_service)
