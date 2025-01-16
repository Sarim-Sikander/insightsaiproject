from __future__ import annotations

from sqlalchemy import Column, Date, Float, Index, String, Text

from app.core.database.session import Base


class Documents(Base):
    __tablename__: str = "documents"

    document_id = Column(String(255), primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    date = Column(Date, nullable=True)
    topics = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)

    revenue = Column(Float, nullable=True)
    net_profit = Column(Float, nullable=True)
    revenue_growth_rate = Column(Float, nullable=True)
    operational_cost_reduction = Column(Float, nullable=True)

    __table_args__ = (
        Index(
            "ix_documents_content_topics_conclusion",
            "content",
            "topics",
            "conclusion",
            mysql_prefix="FULLTEXT",
        ),
    )
