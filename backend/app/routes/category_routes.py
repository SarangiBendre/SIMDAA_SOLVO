from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text

from ..database import engine
from ..auth import get_current_user


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

# ============================================================
# Request Models
# ============================================================

class CategoryCreate(BaseModel):
    CategoryName: str
    Description: str | None = None


class CategoryUpdate(BaseModel):
    CategoryName: str
    Description: str | None = None

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

# ============================================================
# POST /categories/
# Create Category
# ============================================================

@router.post("/")
def create_category(category: CategoryCreate, current_user=Depends(get_current_user)):

    with engine.begin() as connection:

        existing = connection.execute(
            text("""
                SELECT CategoryID
                FROM Categories
                WHERE CategoryName = :name
            """),
            {"name": category.CategoryName}
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Category already exists"
            )

        result = connection.execute(
            text("""
                INSERT INTO Categories
                (
                    CategoryName,
                    Description,
                    IsActive
                )
                OUTPUT INSERTED.CategoryID
                VALUES
                (
                    :name,
                    :description,
                    1
                )
            """),
            {
                "name": category.CategoryName,
                "description": category.Description
            }
        )

        category_id = result.scalar_one()

    return {
        "message": "Category created successfully",
        "CategoryID": category_id
    }


# ============================================================
# GET /categories/{category_id}
# Get Single Category
# ============================================================

@router.get("/{category_id}")
def get_category(category_id: int):

    with engine.connect() as connection:

        category = connection.execute(
            text("""
                SELECT
                    CategoryID,
                    CategoryName,
                    Description,
                    IsActive
                FROM Categories
                WHERE CategoryID = :category_id
            """),
            {"category_id": category_id}
        ).first()

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

        return {
            "CategoryID": category.CategoryID,
            "CategoryName": category.CategoryName,
            "Description": category.Description,
            "IsActive": bool(category.IsActive)
        }


# ============================================================
# PUT /categories/{category_id}
# Update Category
# ============================================================

@router.put("/{category_id}")
def update_category(
    category_id: int,
    category: CategoryUpdate,
    current_user=Depends(get_current_user)
):

    with engine.begin() as connection:

        existing = connection.execute(
            text("""
                SELECT CategoryID
                FROM Categories
                WHERE CategoryID = :category_id
            """),
            {"category_id": category_id}
        ).first()

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

        connection.execute(
            text("""
                UPDATE Categories
                SET
                    CategoryName = :name,
                    Description = :description
                WHERE CategoryID = :category_id
            """),
            {
                "category_id": category_id,
                "name": category.CategoryName,
                "description": category.Description
            }
        )

    return {
        "message": "Category updated successfully"
    }


# ============================================================
# DELETE /categories/{category_id}
# Soft Delete Category
# ============================================================

@router.delete("/{category_id}")
def delete_category(category_id: int, current_user=Depends(get_current_user)):

    with engine.begin() as connection:

        existing = connection.execute(
            text("""
                SELECT CategoryID
                FROM Categories
                WHERE CategoryID = :category_id
            """),
            {"category_id": category_id}
        ).first()

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

        connection.execute(
            text("""
                UPDATE Categories
                SET IsActive = 0
                WHERE CategoryID = :category_id
            """),
            {"category_id": category_id}
        )

    return {
        "message": "Category deleted successfully"
    }