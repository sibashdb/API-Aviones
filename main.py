from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables
from routers import aircraft
from fastapi.staticfiles import StaticFiles 

tags_metadata = [
    {
        "name": "SkySpecs Core",
        "description": "Endpoints principales para gestionar aeronaves, fabricantes, especificaciones y etiquetas."
    },
]

app = FastAPI(
    title="SkySpecs API ",
    version="2.0.0",
    openapi_tags=tags_metadata,
)

# Mount static uploads directory after app creation
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(aircraft.router)

@app.get("/", tags=["Sistema"])
def home():
    return {
        "status": "Online", 
        "service": "SkySpecs API", 
        "engine": "PostgreSQL via Supabase"
    }