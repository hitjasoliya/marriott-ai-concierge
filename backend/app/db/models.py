from sqlalchemy import Column, Integer, Float, Text, String, Index
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=False, default="Marriott")
    city = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    semantic_text = Column(Text, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    rating = Column(Float, nullable=True)
    amenities = Column(JSONB, nullable=True)
    price_per_night = Column(Integer, nullable=True)
    hotel_type = Column(String(50), nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=True)

    __table_args__ = (
        Index(
            "hotels_geo_idx",
            geom,
            postgresql_using="gist",
        ),
        Index(
            "hotels_embedding_idx",
            embedding,
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 200},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
