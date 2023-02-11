import aio_pika
from di import bind_by_type, Container
from di.api.providers import DependencyProviderType
from di.api.scopes import Scope
from di.dependent import Dependent
from di.executors import AsyncExecutor
from didiator import CommandMediator, EventMediator, Mediator, QueryMediator
from didiator.interface.utils.di_builder import DiBuilder
from didiator.utils.di_builder import DiBuilderImpl
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession

from src.application.common.interfaces.mapper import Mapper
from src.application.common.interfaces.uow import UnitOfWork
from src.application.user.interfaces.persistence import UserReader, UserRepo
from src.infrastructure.constants import APP_SCOPE, REQUEST_SCOPE
from src.infrastructure.db.main import build_sa_engine, build_sa_session, build_sa_session_factory
from src.infrastructure.db.repositories.user import UserReaderImpl, UserRepoImpl
from src.infrastructure.db.uow import SQLAlchemyUoW
from src.infrastructure.event_bus.event_bus import EventBusImpl
from src.infrastructure.mapper.main import build_mapper
from src.infrastructure.mediator import get_mediator
from src.infrastructure.message_broker.interface import MessageBroker
from src.infrastructure.message_broker.main import build_rq_channel, build_rq_channel_pool, build_rq_connection_pool
from src.infrastructure.message_broker.message_broker import MessageBrokerImpl


def init_di_builder() -> DiBuilder:
    di_container = Container()
    di_executor = AsyncExecutor()
    di_scopes = [APP_SCOPE, REQUEST_SCOPE]
    di_builder = DiBuilderImpl(di_container, di_executor, di_scopes=di_scopes)
    return di_builder


def setup_di_builder(di_builder: DiBuilder) -> None:
    di_builder.bind(bind_by_type(Dependent(lambda *args: di_builder, scope=APP_SCOPE), DiBuilder))
    di_builder.bind(bind_by_type(Dependent(build_mapper, scope=APP_SCOPE), Mapper))
    setup_mediator_factory(di_builder, get_mediator, REQUEST_SCOPE)
    setup_db_factories(di_builder)
    setup_event_bus_factories(di_builder)


def setup_mediator_factory(
    di_builder: DiBuilder,
    mediator_factory: DependencyProviderType,
    scope: Scope,
) -> None:
    di_builder.bind(bind_by_type(Dependent(mediator_factory, scope=scope), Mediator))
    di_builder.bind(bind_by_type(Dependent(mediator_factory, scope=scope), QueryMediator))
    di_builder.bind(bind_by_type(Dependent(mediator_factory, scope=scope), CommandMediator))
    di_builder.bind(bind_by_type(Dependent(mediator_factory, scope=scope), EventMediator))


def setup_db_factories(di_builder: DiBuilder) -> None:
    di_builder.bind(bind_by_type(Dependent(build_sa_engine, scope=APP_SCOPE), AsyncEngine))
    di_builder.bind(bind_by_type(Dependent(build_sa_session_factory, scope=APP_SCOPE), async_sessionmaker[AsyncSession]))
    di_builder.bind(bind_by_type(Dependent(build_sa_session, scope=REQUEST_SCOPE), AsyncSession))
    di_builder.bind(bind_by_type(Dependent(SQLAlchemyUoW, scope=REQUEST_SCOPE), UnitOfWork))
    di_builder.bind(bind_by_type(Dependent(UserRepoImpl, scope=REQUEST_SCOPE), UserRepo, covariant=True))
    di_builder.bind(bind_by_type(Dependent(UserReaderImpl, scope=REQUEST_SCOPE), UserReader, covariant=True))


def setup_event_bus_factories(di_builder: DiBuilder) -> None:
    di_builder.bind(bind_by_type(
        Dependent(build_rq_connection_pool, scope=APP_SCOPE), aio_pika.pool.Pool[aio_pika.abc.AbstractConnection],
    ))
    di_builder.bind(bind_by_type(
        Dependent(build_rq_channel_pool, scope=APP_SCOPE), aio_pika.pool.Pool[aio_pika.abc.AbstractChannel],
    ))
    di_builder.bind(bind_by_type(Dependent(build_rq_channel, scope=APP_SCOPE), aio_pika.abc.AbstractChannel))
    di_builder.bind(bind_by_type(Dependent(MessageBrokerImpl, scope=APP_SCOPE), MessageBroker))
    di_builder.bind(bind_by_type(Dependent(EventBusImpl, scope=APP_SCOPE), EventBusImpl))
