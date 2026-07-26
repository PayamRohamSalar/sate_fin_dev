"""Employer (مشمولین) model for the SATE financial system.

Represents organizations subject to research-and-technology funding mandates.
An employer may be a Mother company, a Subsidiary of another employer, or an
Independent entity. The ``parent_code`` foreign key is self-referential,
allowing hierarchical grouping of subsidiary employers under their parent.
"""

from sqlalchemy import CheckConstraint, Column, ForeignKey, String

from core.database import Base, SoftDeleteMixin


class Employer(SoftDeleteMixin, Base):
    """Organization liable for mandated research-and-technology funding.

    Attributes
    ----------
    classification_code : str
        Unique classification code; primary key (max 20 chars).
    name : str
        Official name of the employer (max 200 chars).
    employer_type : str
        Structural type: one of ``Mother``, ``Subsidiary`` or ``Independent``.
    parent_code : str or None
        Classification code of the parent (mother) employer. Self-referential
        foreign key to ``employers.classification_code``; ``None`` for mother
        or independent employers.
    province : str
        Province where the employer is located (max 50 chars).
    affairs_category : str or None
        Optional functional category of the employer's affairs.
    upper_organization : str
        Name of the supervising/executing body above this employer.
    status : str
        Lifecycle status; defaults to ``Active``.
    """

    __tablename__ = "employers"

    classification_code = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    employer_type = Column(String(20), nullable=False)
    parent_code = Column(
        String(20),
        ForeignKey("employers.classification_code"),
        nullable=True,
    )
    province = Column(String(50), nullable=False)
    affairs_category = Column(String(100), nullable=True)
    upper_organization = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="Active")

    __table_args__ = (
        CheckConstraint(
            "employer_type IN ('Mother', 'Subsidiary', 'Independent')",
            name="check_employer_type",
        ),
        CheckConstraint(
            "status IN ('Active', 'Inactive')",
            name="check_employer_status",
        ),
    )

    def __repr__(self):
        return (
            f"<Employer(code={self.classification_code!r}, "
            f"name={self.name!r}, type={self.employer_type!r})>"
        )
