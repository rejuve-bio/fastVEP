from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator

_VCF_DELIMITERS = ("\t", "\n", "\r")


class Variant(BaseModel):
    chr: str = Field(min_length=1)
    pos: int = Field(gt=0)
    ref: str = Field(min_length=1)
    alt: str = Field(min_length=1)

    @field_validator("chr", "ref", "alt")
    @classmethod
    def reject_vcf_delimiters(cls, value: str) -> str:
        if any(d in value for d in _VCF_DELIMITERS):
            raise ValueError("must not contain tab or newline characters")
        return value


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
