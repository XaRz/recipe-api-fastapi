from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import SessionLocal, engine
from models import Base, Recipe
import os

# Crear taules (només la primera vegada)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recipe API", version="1.0.0")

class RecipeCreate(BaseModel):
    title: str
    short_description: Optional[str] = None
    category_id: Optional[int] = None
    cuisine_id: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: str  # easy, medium, hard
    status: str = "draft"
    visibility: str = "public"

class RecipeResponse(BaseModel):
    id: int
    title: str
    short_description: Optional[str]
    total_time_minutes: Optional[int]
    difficulty: str
    calories_per_serving: Optional[float]
    protein_g_per_serving: Optional[float]

    class Config:
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["health"])
def read_root():
    return {"message": "Recipe API is running!"}

@app.get("/recipes", response_model=List[RecipeResponse], tags=["recipes"])
def read_recipes(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: easy, medium, hard"),
    max_total_time: Optional[int] = Query(None, description="Max total time in minutes"),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Recipe).filter(Recipe.visibility == "public")

    if difficulty:
        query = query.filter(Recipe.difficulty == difficulty)

    if max_total_time:
        query = query.filter(Recipe.total_time_minutes <= max_total_time)

    recipes = query.offset(skip).limit(limit).all()
    return recipes

@app.get("/recipes/{recipe_id}", response_model=RecipeResponse, tags=["recipes"])
def read_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@app.post("/recipes", response_model=RecipeResponse, tags=["recipes"])
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = Recipe(**recipe.dict())
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)