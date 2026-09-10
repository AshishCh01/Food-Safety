from sqlalchemy.orm import Session

from app.models.complaint_category import ComplaintCategory
from app.repositories import complaint_category_repository
from app.schemas.complaint_category import ComplaintCategoryRead, ComplaintSubcategoryRead

def list_categories(db: Session) -> list[ComplaintCategory]:
    return complaint_category_repository.list_active(db)


def to_category_read(category: ComplaintCategory) -> ComplaintCategoryRead:
    return ComplaintCategoryRead(
        id=category.id,
        key=category.key,
        name=category.name,
        description=category.description,
        is_active=category.is_active,
        subcategories=[
            ComplaintSubcategoryRead(
                id=sub.id,
                key=sub.key,
                name=sub.name,
                description=sub.description,
                is_active=sub.is_active
            )
            for sub in category.subcategories if sub.is_active
        ]
    )
