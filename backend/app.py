from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome!"}

@app.get("/products")
def get_products(limit: int = 10, page: int = 0):
    return {"next": None, "previous": None, "count": limit, "results": []}
