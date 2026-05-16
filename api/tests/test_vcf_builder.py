import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Variant
from vcf_builder import variants_to_vcf


def _rows(vcf: str) -> list[str]:
    return [line for line in vcf.splitlines() if not line.startswith("#")]


def _header_lines(vcf: str) -> list[str]:
    return [line for line in vcf.splitlines() if line.startswith("#")]


def test_single_variant_row_count():
    v = Variant(chr="chr1", pos=100, ref="A", alt="G")
    vcf = variants_to_vcf([v])
    assert len(_rows(vcf)) == 1


def test_multi_variant_row_count():
    variants = [
        Variant(chr="chr1", pos=100, ref="A", alt="G"),
        Variant(chr="chr2", pos=200, ref="C", alt="T"),
        Variant(chr="chrX", pos=300, ref="G", alt="A"),
    ]
    vcf = variants_to_vcf(variants)
    assert len(_rows(vcf)) == 3


def test_column_values():
    v = Variant(chr="chr17", pos=43071077, ref="A", alt="T")
    vcf = variants_to_vcf([v])
    row = _rows(vcf)[0]
    cols = row.split("\t")
    assert cols[0] == "chr17"
    assert cols[1] == "43071077"
    assert cols[3] == "A"
    assert cols[4] == "T"


def test_tab_separated():
    v = Variant(chr="chr1", pos=1, ref="A", alt="G")
    vcf = variants_to_vcf([v])
    row = _rows(vcf)[0]
    assert "\t" in row
    assert len(row.split("\t")) == 8


def test_ends_with_newline():
    v = Variant(chr="chr1", pos=1, ref="A", alt="G")
    vcf = variants_to_vcf([v])
    assert vcf.endswith("\n")


def test_has_vcf_header():
    v = Variant(chr="chr1", pos=1, ref="A", alt="G")
    vcf = variants_to_vcf([v])
    headers = _header_lines(vcf)
    assert any("fileformat=VCFv4.2" in h for h in headers)
    assert any("#CHROM" in h for h in headers)
