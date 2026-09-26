from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, ROLE_ADMIN
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryCreate(BaseModel):
    CategoryName: str
    Description: str | None = None


class CategoryUpdate(BaseModel):
    CategoryName: str
    Description: str | None = None


def _serialize(c: Category):
    return {
        "CategoryID": c.CategoryID,
        "CategoryName": c.CategoryName,
        "Description": c.Description,
        "IsActive": c.IsActive,
        "QuestionCount": len(c.questions),
    }


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).filter(Category.IsActive.is_(True)).order_by(Category.CategoryName).all()
    return [_serialize(c) for c in categories]


@router.post("/")
def create_category(category: CategoryCreate, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.CategoryName == category.CategoryName).first():
        raise HTTPException(status_code=409, detail="Category already exists")

    new_category = Category(CategoryName=category.CategoryName, Description=category.Description, IsActive=True)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return {"message": "Category created successfully", "CategoryID": new_category.CategoryID}


@router.get("/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.CategoryID == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return _serialize(category)


@router.put("/{category_id}")
def update_category(category_id: int, category: CategoryUpdate, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.CategoryID == category_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")

    existing.CategoryName = category.CategoryName
    existing.Description = category.Description
    db.commit()

    return {"message": "Category updated successfully"}


@router.delete("/{category_id}")
def delete_category(category_id: int, current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.CategoryID == category_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")

    existing.IsActive = False
    db.commit()

    return {"message": "Category deleted successfully"}
