"""SQLAlchemy 2.0 models and seed data for the catalog service (complete; you may extend it)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    sku: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(32), index=True)
    price_cents: Mapped[int] = mapped_column(Integer)


class Inventory(Base):
    __tablename__ = "inventory"
    sku: Mapped[str] = mapped_column(ForeignKey("products.sku"), primary_key=True)
    store_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    on_hand: Mapped[int] = mapped_column(Integer)
    reserved: Mapped[int] = mapped_column(Integer, default=0)


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("idempotency_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    sku: Mapped[str] = mapped_column(String(32))
    store_id: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[int] = mapped_column(Integer)
    available_after: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now(dt.timezone.utc))


def make_engine(url: str = "sqlite+pysqlite:///:memory:"):
    if url.endswith(":memory:"):
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url)


def make_sessionmaker(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


CATEGORIES = ["tents", "sleeping", "lighting", "cooking", "packs", "apparel", "furniture"]

_ROWS = [
    ("KO-TENT-1P", "Solo Trek 1P Tent", "Ultralight one-person backpacking tent, 1.2 kg.", "tents", 18900),
    ("KO-TENT-2P", "Ridgeline 2P Tent", "Two-person backpacking tent with two doors, 1.9 kg.", "tents", 24900),
    ("KO-TENT-3P", "Basecamp 3P Tent", "Roomy three-person tent for car camping.", "tents", 32900),
    ("KO-TENT-6P", "Lodge 6P Cabin Tent", "Family cabin tent with a room divider.", "tents", 44900),
    ("KO-TARP-10", "Shelter Tarp 10x10", "Ripstop tarp with 16 tie-outs.", "tents", 7400),
    ("KO-BAG-20F", "Alpine 20F Sleeping Bag", "Down mummy bag rated to 20F.", "sleeping", 15900),
    ("KO-BAG-40F", "Summer 40F Sleeping Bag", "Synthetic rectangular bag for warm nights.", "sleeping", 8900),
    ("KO-BAG-KID", "Cub Kids Sleeping Bag", "Kids bag rated to 40F with a glow zipper.", "sleeping", 5900),
    ("KO-PAD-INF", "Cloudrest Inflatable Pad", "Insulated inflatable sleeping pad, R-value 4.2.", "sleeping", 7900),
    ("KO-PAD-FOAM", "Closed-cell Foam Pad", "Indestructible foam pad, R-value 2.0.", "sleeping", 3900),
    ("KO-COT-1", "Fold-up Camp Cot", "Steel frame cot, holds 300 lb.", "sleeping", 8900),
    ("KO-LAMP-1", "Trail Lantern", "Rechargeable LED lantern, 400 lumens.", "lighting", 3450),
    ("KO-HEAD-300", "Beacon 300 Headlamp", "300 lumen headlamp with red mode.", "lighting", 2900),
    ("KO-HEAD-600", "Beacon 600 Headlamp", "600 lumen rechargeable headlamp.", "lighting", 4900),
    ("KO-STRING-1", "Campsite String Lights", "Solar string lights, 20 ft.", "lighting", 2400),
    ("KO-STOVE-1", "Ember Canister Stove", "Compact canister stove with igniter.", "cooking", 5900),
    ("KO-STOVE-2", "Twin Burner Camp Stove", "Two-burner propane stove for car camping.", "cooking", 11900),
    ("KO-POT-SET", "Nesting Cook Set", "Aluminum pots and pans that nest.", "cooking", 4500),
    ("KO-COOL-45", "Glacier 45qt Cooler", "Rotomolded cooler, keeps ice for five days.", "cooking", 21900),
    ("KO-COOL-20", "Glacier 20qt Cooler", "Small rotomolded cooler.", "cooking", 14900),
    ("KO-BOTL-1L", "Insulated 1L Bottle", "Stainless bottle, keeps drinks cold 24 h.", "cooking", 3200),
    ("KO-FILT-1", "Streamline Water Filter", "Squeeze filter, 0.1 micron.", "cooking", 3900),
    ("KO-PACK-28", "Daytripper 28L Pack", "Day pack with a hydration sleeve.", "packs", 8900),
    ("KO-PACK-45", "Switchback 45L Pack", "Backpacking pack with an adjustable torso.", "packs", 16900),
    ("KO-PACK-65", "Expedition 65L Pack", "Load-hauling pack for long trips.", "packs", 22900),
    ("KO-PACK-KID", "Scout Kids Pack", "Small pack for young hikers.", "packs", 4900),
    ("KO-JKT-RAIN", "Downpour Rain Jacket", "Waterproof breathable rain jacket.", "apparel", 12900),
    ("KO-JKT-FLC", "Hearth Fleece Jacket", "Midweight fleece jacket.", "apparel", 7900),
    ("KO-JKT-DOWN", "Summit Down Jacket", "800-fill down jacket.", "apparel", 22900),
    ("KO-HAT-SUN", "Wide Brim Sun Hat", "UPF 50 sun hat.", "apparel", 3400),
    ("KO-SOCK-WL", "Merino Hiking Socks", "Merino wool hiking socks, 2 pack.", "apparel", 2600),
    ("KO-GLOV-1", "Trail Gloves", "Lightweight touchscreen gloves.", "apparel", 2900),
    ("KO-CHAIR-1", "Fireside Camp Chair", "Folding chair with a cup holder.", "furniture", 5400),
    ("KO-CHAIR-2", "Backpacker Chair", "Ultralight chair, 900 g.", "furniture", 8900),
    ("KO-TABLE-1", "Fold-flat Camp Table", "Aluminum roll-top table.", "furniture", 6900),
    ("KO-HAMK-1", "Canopy Hammock", "Single hammock with straps.", "furniture", 6400),
    ("KO-HAMK-2", "Canopy Double Hammock", "Two-person hammock with straps.", "furniture", 7900),
    ("KO-SHADE-1", "Beach Shade Canopy", "Pop-up shade, UPF 50.", "furniture", 8900),
    ("KO-RUG-1", "Outdoor Rug 5x7", "Reversible outdoor rug.", "furniture", 4900),
    ("KO-BENCH-1", "Picnic Bench", "Folding wooden bench.", "furniture", 8900),
]

_STORES = ["012", "045", "087"]


def seed(session: Session) -> None:
    for i, (sku, name, desc, cat, price) in enumerate(_ROWS):
        session.add(Product(sku=sku, name=name, description=desc, category=cat, price_cents=price))
        for j, store in enumerate(_STORES):
            on_hand = (i * 7 + j * 3) % 9  # deterministic; some zeros
            session.add(Inventory(sku=sku, store_id=store, on_hand=on_hand, reserved=0))
    session.commit()
