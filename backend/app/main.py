from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, AsyncSessionLocal
from app.routers import auth
import os
from sqlalchemy.future import select
from app.security.auth import get_password_hash

app = FastAPI(
    title="Secure Software Design Application",
    description="A secure web application for CS 4417/6417.",
    version="1.0.0",
)

# Restrict CORS to specific frontend origin in production
origins = [
    "http://localhost:5173", # Vite default React dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.on_event("startup")
async def startup_event():
    # In a real app, use Alembic for migrations.
    # For this project, we can create tables directly for simplicity.
    from app.models.user import User, AuditLog
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-seed the administrative user upon server startup
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL")
    admin_pw = os.getenv("DEFAULT_ADMIN_PASSWORD")
    
    if admin_email and admin_pw:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(email=admin_email))
            user = result.scalar_one_or_none()
            if not user:
                hashed_pw = get_password_hash(admin_pw)
                admin = User(
                    email=admin_email,
                    hashed_password=hashed_pw,
                    role="admin"
                )
                session.add(admin)
                await session.commit()
                print(f"Auto-seeded admin user: {admin_email}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Secure Backend API."}
