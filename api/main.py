from __future__ import annotations

import logging
import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pythonjsonlogger import json as jsonlogger

from models import AnnotateRequest, AnnotateResponse
from vcf_builder import variants_to_vcf

FASTVEP_URL = os.environ.get("FASTVEP_URL", "http://localhost:8080").rstrip("/")

_origins_raw = os.environ.get("CORS_ORIGINS", "*")
CORS_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

_handler = logging.StreamHandler()
_handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logger = logging.getLogger(__name__)

app = FastAPI(title="fastVEP JSON API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{FASTVEP_URL}/api/status")
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("health check failed: %s", exc)
            raise HTTPException(status_code=503, detail="fastvep-web unreachable")
    return {"status": "ok", "backend": "ok"}


@app.post("/annotate")
async def annotate(req: AnnotateRequest) -> JSONResponse:
    logger.info(
        "annotate variants=%d acmg=%s pick=%s",
        len(req.variants),
        req.acmg,
        req.pick,
    )
    vcf_text = variants_to_vcf(req.variants)

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{FASTVEP_URL}/api/annotate",
                json={"vcf": vcf_text, "acmg": req.acmg, "pick": req.pick},
            )
            resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot reach fastvep-web at {FASTVEP_URL}",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="fastvep-web timed out",
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=exc.response.text,
            )

    if not resp.content:
        raise HTTPException(
            status_code=502,
            detail=f"fastvep-web returned an empty body (status {resp.status_code})",
        )

    try:
        return JSONResponse(content=resp.json())
    except Exception:
        raise HTTPException(
            status_code=502,
            detail=f"fastvep-web returned non-JSON (status {resp.status_code}): {resp.text[:500]}",
        )
