from __future__ import annotations

from typing import Any
from pydantic import BaseModel, model_validator


class Variant(BaseModel):
    chr: str
    pos: int
    ref: str
    alt: str


class AnnotateRequest(BaseModel):
    variants: list[Variant] | None = None
    chr: str | None = None
    pos: int | None = None
    ref: str | None = None
    alt: str | None = None
    acmg: bool = True
    pick: bool = False

    @model_validator(mode="after")
    def resolve_variants(self) -> AnnotateRequest:
        if self.variants is None:
            if None in (self.chr, self.pos, self.ref, self.alt):
                raise ValueError(
                    "Provide either 'variants' list or top-level chr/pos/ref/alt fields"
                )
            self.variants = [
                Variant(chr=self.chr, pos=self.pos, ref=self.ref, alt=self.alt)
            ]
        return self


class AnnotateResponse(BaseModel):
    results: list[Any]
    count: int
    time_ms: float | None = None
