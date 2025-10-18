import os
from typing import TypedDict, Annotated
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import pandas as pd
from fastapi import FastAPI, Depends, status, UploadFile, HTTPException, Request
from sqlmodel import Field, Session, SQLModel, create_engine, select, delete
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ValidationError, model_validator


# region Models

class Product(SQLModel, table=True):
    sku: str = Field(primary_key=True, unique=True)
    name: str = Field(index=True)
    brand: str = Field(index=True)
    color: str | None = Field(index=True)
    size: str | None = Field(index=True)
    mrp: float = Field(ge=0, description="mrp must be greater than zero")
    price: float = Field(ge=0, description="price must be greater than zero")
    quantity: int | None = Field(None, ge=0, description="Quantity must not be negative")

    @model_validator(mode="after")
    def validate_product(self) -> "Product":
        if self.mrp < self.price:
            raise ValueError("Price can not be greater than mrp.")
        return self

# endregion

# region SQLite

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connet_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connet_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

get_db = get_session

def clear_db(db: Session):
    db.exec(delete(Product))
    db.commit()

# endregion

# region Validation
class ValidationResult(TypedDict):
    data: Product
    message: str | None
    is_valid: bool
# endregion

# region Main

class ProductResponse(BaseModel):
    previous: str | None = None
    next: str | None = None
    count: int
    results: list[Product]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database and tables...")
    create_db_and_tables()
    yield
    print("Shutting down...")
    # print("Clearing database...")
    # with Session(engine) as session:
    #     clear_db(session)
    # print("Database cleared.\n")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Welcome!"}

@app.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_file(file: UploadFile, session: Session = Depends(get_db)):
    filename = file.filename
    file_extension = os.path.splitext(filename)[1]
    if file_extension not in [".csv", ".xlsx"]:
        raise HTTPException(status_code=422, detail="Invalid file format. Only .csv and .xlsx files are allowed.")
    
    if (file_extension == ".csv"):
        df = pd.read_csv(file.file)
    else:
        df = pd.read_excel(file.file)
    
    required_columns = {"sku", "name", "brand", "mrp", "price"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(status_code=422, detail=f"Missing required columns: {required_columns - set(df.columns)}")
    
    inserted, skipped = 0, 0
    failed = []

    for _, row in df.iterrows():
        try:
            product = Product(
                sku = str(row["sku"]),
                name = str(row["name"]),
                brand = str(row["brand"]),
                color = str(row["color"]) if not pd.isna(row.get("color", None)) else None,
                size = str(row["size"]) if not pd.isna(row.get("size", None)) else None,
                mrp = float(row["mrp"]),
                price = float(row["price"]),
                quantity = int(row["quantity"]) if not pd.isna(row.get("quantity", 0)) else None
            )
            product = Product.model_validate(product)
            session.add(product)
            session.flush()
            inserted += 1
        except IntegrityError as e:
            session.rollback()
            failed.append({"row": row.to_dict(), "error": "Duplicate SKU"})
            skipped += 1
        except Exception as e:
            session.rollback()
            failed.append({"row": row.to_dict(), "error": str(e)})
            skipped += 1

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # return {"message": f"File {filename} processed.", "inserted": inserted, "skipped": skipped}
    return {"stored": inserted, "failed": failed}

@app.post("/clear_db", status_code=status.HTTP_200_OK)
def clear_database(session: Session = Depends(get_db)):
    clear_db(session)
    return {"message": "Database cleared successfully."}

@app.get("/products")
def get_products(request: Request, limit: int = 10, page: int = 1, session: Session = Depends(get_db)):
    offset = (page-1) * limit

    query = select(Product)
    total_products = session.exec(query).all()
    total = len(total_products)
    products = session.exec(query.offset(offset).limit(limit)).all()
    count = len(products)

    next_page_number = page + 1 if offset + limit < total else None
    previous_page_number = page - 1 if page > 1 else None

    current_url = str(request.url)
    parsed = urlparse(current_url)
    query_params = parse_qs(parsed.query)
    next_page = None
    previous_page = None

    if next_page_number is not None:
        query_params["page"] = [str(next_page_number)]
        next_query = urlencode(query_params, doseq=True)
        next_parsed = parsed._replace(query=next_query)
        next_page = urlunparse(next_parsed)
    
    if previous_page_number is not None:
        query_params["page"] = [str(previous_page_number)]
        previous_query = urlencode(query_params, doseq=True)
        previous_parsed = parsed._replace(query=previous_query)
        previous_page = urlunparse(previous_parsed)

    # return ProductResponse(previous=previous_page, next=next_page, count=count, results=products)
    return products

@app.get("/products/search")
def get_products_with_search(request: Request, brand: str | None = None, color: str | None = None, minPrice: float | None = None, maxPrice: float | None = None, limit: int = 10, page: int = 1, session: Session = Depends(get_db)):
    query = select(Product)
    if brand:
        query = query.where(Product.brand == brand)
    if color:
        query = query.where(Product.color == color)
    if minPrice is not None:
        query = query.where(Product.price >= minPrice)
    if maxPrice is not None:
        query = query.where(Product.price <= maxPrice)
    
    total_products = session.exec(query).all()
    total = len(total_products)
    products = session.exec(query).all()
    count = len(products)

    offset = (page-1)*limit

    next_page_number = page + 1 if offset + limit < total else None
    previous_page_number = page - 1 if page > 1 else None

    current_url = str(request.url)
    parsed = urlparse(current_url)
    query_params = parse_qs(parsed.query)
    next_page = None
    previous_page = None

    if next_page_number is not None:
        query_params["page"] = [str(next_page_number)]
        next_query = urlencode(query_params, doseq=True)
        next_parsed = parsed._replace(query=next_query)
        next_page = urlunparse(next_parsed)
    
    if previous_page_number is not None:
        query_params["page"] = [str(previous_page_number)]
        previous_query = urlencode(query_params, doseq=True)
        previous_parsed = parsed._replace(query=previous_query)
        previous_page = urlunparse(previous_parsed)

    # return ProductResponse(previous=previous_page, next=next_page, count=count, results=products)
    return products

# endregion