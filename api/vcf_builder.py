from __future__ import annotations

from models import Variant


def variants_to_vcf(variants: list[Variant]) -> str:
    lines = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
    ]
    for v in variants:
        lines.append(f"{v.chr}\t{v.pos}\t.\t{v.ref}\t{v.alt}\t.\t.\t.")
    return "\n".join(lines) + "\n"
