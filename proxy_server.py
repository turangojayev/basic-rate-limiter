import random

from fastapi import FastAPI
from starlette.responses import JSONResponse
import uvicorn

app = FastAPI()


@app.get("/health-1")
async def main_route():
    i = random.randint(0, 100)
    ok_response = {"message": "Hello World"}
    bad_response = {"message": "Bad response"}
    proxy_error = {"message": "Proxy Error"}
    if i > 80:
        return JSONResponse(status_code=429, content=proxy_error)
    if i > 60:
        return JSONResponse(status_code=500, content=bad_response)
    return JSONResponse(status_code=200, content=ok_response)


@app.get("/health-2")
async def main_route():
    i = random.randint(0, 100)
    ok_response = {"message": "Hello World"}
    bad_response = {"message": "Internal Server Error"}
    proxy_error = {"message": "Proxy Error"}
    if i > 70:
        return JSONResponse(status_code=500, content=bad_response)
    if i > 50:
        return JSONResponse(status_code=429, content=proxy_error)
    return JSONResponse(status_code=200, content=ok_response)


@app.get("/health-3")
async def main_route():
    ok_response = {"message": "Hello World"}
    return JSONResponse(status_code=200, content=ok_response)


# if __name__ == '__main__':
#     uvicorn.run(app, host="0.0.0.0", port=8080)
