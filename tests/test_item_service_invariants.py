import pytest
import pytest_asyncio
import math
import asyncio
import random
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, precondition, run_state_machine_as_test
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.entities import Base, Item
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.item import ItemService

ATTACK_VECTORS = ["'; DROP TABLE items; --", "1' OR '1'='1", "<script>alert('xss')</script>", "../../etc/passwd", "A" * 500]

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    await engine.dispose()

safe_text = st.text(alphabet=st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters=("\x00",)), min_size=1, max_size=50).filter(lambda s: s.strip() != "")

@st.composite
def malicious_text(draw):
    return draw(st.one_of(safe_text, st.sampled_from(ATTACK_VECTORS)))

@st.composite
def valid_item_create(draw):
    name = draw(malicious_text())
    try:
        return ItemCreate(name=name, description=draw(st.one_of(st.none(), safe_text)), price=draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)), is_active=draw(st.booleans()))
    except ValidationError:
        return ItemCreate(name="fallback_valid_name", description="fallback", price=1.0, is_active=True)

@st.composite
def valid_item_update(draw):
    try:
        return ItemUpdate(name=draw(st.one_of(st.none(), safe_text)), description=draw(st.one_of(st.none(), safe_text)), price=draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=1000.0, allow_nan=False))), is_active=draw(st.one_of(st.none(), st.booleans())))
    except ValidationError:
        return ItemUpdate()

class TestItemServiceInvariants:

    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=valid_item_create())
    @pytest.mark.asyncio
    async def test_i1_price_strictly_positive(self, payload: ItemCreate, db_session: AsyncSession):
        service = ItemService(db_session)
        created = await service.create_item(payload)
        assert created.price > 0
        assert math.isfinite(created.price)

    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payloads=st.lists(valid_item_create(), min_size=0, max_size=20), offset=st.integers(min_value=0, max_value=50), limit=st.integers(min_value=1, max_value=100))
    @pytest.mark.asyncio
    async def test_i3_pagination_metadata_consistency(self, payloads, offset: int, limit: int, db_session: AsyncSession):
        service = ItemService(db_session)
        for p in payloads: await service.create_item(p)
        page = await service.list_items(offset=offset, limit=limit)
        assert len(page.items) <= limit
        assert page.page == (offset // limit) + 1

    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(unknown_id=st.integers(min_value=10_000, max_value=1_000_000))
    @pytest.mark.asyncio
    async def test_i5_get_unknown_returns_404(self, unknown_id: int, db_session: AsyncSession):
        service = ItemService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_item(unknown_id)
        assert exc_info.value.status_code == 404

    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=valid_item_create(), concurrent_deletes=st.integers(min_value=2, max_value=5))
    @pytest.mark.asyncio
    async def test_race_condition_double_delete(self, payload: ItemCreate, concurrent_deletes: int, db_session: AsyncSession):
        service = ItemService(db_session)
        try:
            created = await service.create_item(payload)
        except ValidationError:
            return

        # Cada hilo tendrá su propia sesión para evitar el IllegalStateChangeError
        async def attempt_delete():
            async with async_sessionmaker(bind=db_session.bind, class_=AsyncSession, expire_on_commit=False)() as session:
                temp_service = ItemService(session)
                try:
                    await temp_service.delete_item(created.id)
                    return "success"
                except HTTPException as e:
                    return f"error_{e.status_code}"
                except Exception as e:
                    return f"unhandled_{type(e).__name__}"

        results = await asyncio.gather(*[attempt_delete() for _ in range(concurrent_deletes)])
        
        assert results.count("success") == 1, f"Resultados obtenidos: {results}"
        assert results.count("error_404") == concurrent_deletes - 1
        assert not any(r.startswith("unhandled_") for r in results), f"Errores no controlados: {results}"

class MilitaryGradeStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.loop.run_until_complete(self._setup_db())
        SessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
        self.session = SessionLocal()
        self.service = ItemService(self.session)
        self.created_ids = set()

    async def _setup_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def teardown(self):
        self.loop.run_until_complete(self.session.close())
        self.loop.run_until_complete(self.engine.dispose())
        self.loop.close()

    @rule(payload=valid_item_create())
    def create_item(self, payload):
        item = self.loop.run_until_complete(self.service.create_item(payload))
        self.created_ids.add(item.id)

    @rule(update_payload=valid_item_update())
    @precondition(lambda self: len(self.created_ids) > 0)
    def update_item(self, update_payload):
        item_id = random.choice(list(self.created_ids))
        if item_id not in self.created_ids: return
        try:
            self.loop.run_until_complete(self.service.update_item(item_id, update_payload))
        except (HTTPException, ValidationError): pass

    @rule()
    @precondition(lambda self: len(self.created_ids) > 0)
    def delete_item(self):
        item_id = random.choice(list(self.created_ids))
        if item_id in self.created_ids:
            try:
                self.loop.run_until_complete(self.service.delete_item(item_id))
                self.created_ids.remove(item_id)
            except HTTPException: pass

    @invariant()
    def database_is_never_corrupt(self):
        async def _verify():
            result = await self.session.execute(select(Item))
            return result.scalars().all()
        all_items = self.loop.run_until_complete(_verify())
        for item in all_items:
            assert item.price > 0, f"Precio corrupto detectado: {item.price}"
            assert math.isfinite(item.price), "Precio infinito detectado"

def test_stateful_military_grade():
    run_state_machine_as_test(
        MilitaryGradeStateMachine,
        settings=settings(max_examples=10, stateful_step_count=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    )