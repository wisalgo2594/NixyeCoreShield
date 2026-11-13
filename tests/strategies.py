# tests/strategies.py

from typing import Optional
import re
from hypothesis import strategies as st
from hypothesis.strategies import composite
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, precondition

# Importaciones de la app
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.item import ItemService

# =============================================================================
# ADVERSARIAL VECTORS (ATTACK SURFACE)
# =============================================================================
ATTACK_VECTORS = [
    "\u202a\u202b\u202c\u202d\u202e",  # Bidi overrides
    "\u200b\u200c\u200d\u2060\ufeff",  # Zero-width chars
    "🔥" * 50,                         # Emoji bomb
    "SELECT * FROM items; DROP TABLE items;", # SQL Injection
    "'; EXEC xp_cmdshell 'dir c:\\'; --",     # Advanced SQLi
    "<script>alert(1)</script>",       # XSS attempt
    "\x00\x01\x02\x03\x04\x05",       # C0 Control characters
    "\n\r\t",                          # Whitespace bombs
]

# =============================================================================
# SAFE TEXT GENERATOR (UTF-8 ENFORCED)
# =============================================================================
def _safe_text_strategy(min_size=1, max_size=255):
    return st.text(
        alphabet=st.characters(
            codec="utf-8", # FORZAMOS UTF-8 (Evita surrogates \ud800)
            blacklist_categories=("Cs", "Cc"), # Bloqueamos Surrogates y Controles
            blacklist_characters=("\x00",)
        ),
        min_size=min_size,
        max_size=max_size
    ).filter(lambda s: s.strip() != "")

@composite
def adversarial_name(draw) -> str:
    strategy = draw(st.one_of(
        _safe_text_strategy(),
        st.sampled_from(ATTACK_VECTORS)
    ))
    return strategy[:255] if len(strategy) > 255 else strategy

@composite
def adversarial_price(draw) -> float:
    return draw(st.one_of(
        st.floats(min_value=0.000001, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        st.sampled_from([0.000001, 1.0, 999999.999, 1000000.0]),
        st.floats(min_value=1e-308, max_value=1e-307)
    ))

# =============================================================================
# COMPOSITE STRATEGIES
# =============================================================================
@composite
def valid_item_create(draw) -> ItemCreate:
    return ItemCreate(
        name=draw(adversarial_name()),
        description=draw(st.one_of(st.none(), adversarial_name())),
        price=draw(adversarial_price()),
        is_active=draw(st.booleans()),
    )

@composite
def valid_item_update(draw) -> ItemUpdate:
    return ItemUpdate(
        name=draw(st.one_of(st.none(), adversarial_name())),
        description=draw(st.one_of(st.none(), adversarial_name())),
        price=draw(st.one_of(st.none(), adversarial_price())),
        is_active=draw(st.one_of(st.none(), st.booleans())),
    )

# =============================================================================
# STATEFUL TESTING
# =============================================================================
class ItemServiceStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.created_items = set()
        
    @rule(item=valid_item_create())
    def create(self, item: ItemCreate):
        pass

    @rule()
    @precondition(lambda self: len(self.created_items) > 0)
    def delete_random(self):
        pass

    @invariant()
    def database_never_corrupt(self):
        pass

# TestStateMachine = ItemServiceStateMachine.TestCase