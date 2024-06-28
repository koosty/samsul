import uvicorn
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from router.chat import router as chat_router
from router.auth import router as auth_router
from router.document import router as document_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(document_router)
app.mount("/", StaticFiles(directory="html",html = True), name="html")
if __name__ == "__main__":
    print("Run")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get('PORT', 8000)))

