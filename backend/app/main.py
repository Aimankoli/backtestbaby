from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.routes import auth

app = FastAPI(
    title="BacktestMCP API",
    description="Natural language backtesting engine API",
    version="1.0.0"
)

# CORS middleware - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    await connect_to_mongo()
    print("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    await close_mongo_connection()
    print("Application shutdown complete")


# Include routers
app.include_router(auth.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "BacktestMCP API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
