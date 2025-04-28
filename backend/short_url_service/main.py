from fastapi import FastAPI

from .util.UrlHandle import UrlHandle,HashBasedShortUrl,CreateURLRequest,CreateURLResponse
app = FastAPI()


@app.post("/short-url")
def create_short_url(create_url_request:CreateURLRequest) -> CreateURLResponse:
    return UrlHandle(HashBasedShortUrl).generate_short_url(create_url_request)
@app.get("/short-url/{short_url}")
def redirect_to_original_url(short_url:str):
    return UrlHandle(HashBasedShortUrl).redirect_url(short_url)