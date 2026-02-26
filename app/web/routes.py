from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def frontend_index() -> str:
    html_path = Path(__file__).resolve().parent / "ui" / "index.html"
    return html_path.read_text(encoding="utf-8")
