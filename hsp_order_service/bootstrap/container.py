from dataclasses import dataclass

import grpc
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from hsp_order_service.config import Settings, get_settings
from hsp_order_service.infrastructure.db import (
    create_engine,
    create_session_factory,
    init_db,
)
from hsp_order_service.repository.in_memory import InMemoryEchoRepository
from hsp_order_service.repository.interfaces import EchoRepository, OrderRepository
from hsp_order_service.repository.mysql import SQLAlchemyEchoRepository
from hsp_order_service.repository.order_in_memory import InMemoryOrderRepository
from hsp_order_service.repository.order_mysql import SQLAlchemyOrderRepository
from hsp_order_service.service.echo_service import EchoService
from hsp_order_service.service.order_service import OrderService
from hsp_order_service.transport.grpc.server import build_grpc_server
from hsp_order_service.transport.http.app import create_http_app


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: AsyncEngine | None
    session_factory: async_sessionmaker[AsyncSession] | None
    echo_repository: EchoRepository
    order_repository: OrderRepository
    echo_service: EchoService
    order_service: OrderService
    http_app: FastAPI
    grpc_server: grpc.aio.Server


async def build_container() -> AppContainer:
    settings = get_settings()
    echo_repository: EchoRepository
    order_repository: OrderRepository

    if settings.use_mock_repository:
        engine = None
        session_factory = None
        echo_repository = InMemoryEchoRepository()
        order_repository = InMemoryOrderRepository()
    else:
        engine = create_engine(settings.mysql_dsn)
        await init_db(engine)
        session_factory = create_session_factory(engine)
        echo_repository = SQLAlchemyEchoRepository(session_factory)
        order_repository = SQLAlchemyOrderRepository(session_factory)

    echo_service = EchoService(echo_repository)
    order_service = OrderService(order_repository)
    http_app = create_http_app(echo_service, order_service)
    grpc_server = build_grpc_server(settings, echo_service, order_service)

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        echo_repository=echo_repository,
        order_repository=order_repository,
        echo_service=echo_service,
        order_service=order_service,
        http_app=http_app,
        grpc_server=grpc_server,
    )
