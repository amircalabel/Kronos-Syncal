from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi import Depends

from app.auth import oauth
from app.database import get_db
from app.models import Usuario


router = APIRouter(prefix="/auth")


@router.get("/login")
async def login(request: Request):
    redirect_uri = str(request.url_for("callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        return JSONResponse(
            status_code=401,
            content={"detail": "No fue posible verificar la identidad de Google"},
        )

    email = userinfo["email"]
    usuario = db.get(Usuario, email)
    if usuario is None:
        usuario = Usuario(
            email=email,
            nombre=userinfo.get("name") or email,
            google_sub=userinfo.get("sub"),
        )
        db.add(usuario)
    else:
        usuario.nombre = userinfo.get("name") or usuario.nombre
        usuario.google_sub = userinfo.get("sub") or usuario.google_sub
    db.commit()

    request.session["user"] = {
        "email": email,
        "name": userinfo.get("name"),
        "sub": userinfo.get("sub"),
    }
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.get("/me")
async def me(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse(status_code=401, content={"detail": "No autenticado"})
    return user
