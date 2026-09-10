from fastapi import APIRouter
from sqlalchemy import text

from ..database import engine


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


@router.get("/")
def get_categories():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT CategoryID, CategoryName, Description
                FROM Categories
                WHERE IsActive = 1
                ORDER BY CategoryName
            """)
        )

        categories = []

        for row in result:
            categories.append({
                "CategoryID": row.CategoryID,
                "CategoryName": row.CategoryName,
                "Description": row.Description
            })

        return categories