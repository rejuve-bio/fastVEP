import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pydantic import ValidationError

from models import AnnotateRequest, Variant


def test_variants_list_accepted():
    req = AnnotateRequest(variants=[Variant(chr="chr1", pos=100, ref="A", alt="G")])
    assert len(req.variants) == 1


def test_single_variant_shorthand_expands():
    req = AnnotateRequest(chr="chr1", pos=100, ref="A", alt="G")
    assert req.variants is not None
    assert len(req.variants) == 1
    assert req.variants[0].chr == "chr1"
    assert req.variants[0].pos == 100


def test_missing_all_fields_raises():
    with pytest.raises(ValidationError):
        AnnotateRequest()


def test_partial_shorthand_raises():
    with pytest.raises(ValidationError):
        AnnotateRequest(chr="chr1", pos=100)


def test_acmg_defaults_true():
    req = AnnotateRequest(chr="chr1", pos=100, ref="A", alt="G")
    assert req.acmg is True


def test_pick_defaults_false():
    req = AnnotateRequest(chr="chr1", pos=100, ref="A", alt="G")
    assert req.pick is False


def test_acmg_can_be_overridden():
    req = AnnotateRequest(chr="chr1", pos=100, ref="A", alt="G", acmg=False)
    assert req.acmg is False


def test_variants_list_with_multiple():
    req = AnnotateRequest(
        variants=[
            Variant(chr="chr1", pos=100, ref="A", alt="G"),
            Variant(chr="chr2", pos=200, ref="C", alt="T"),
        ]
    )
    assert len(req.variants) == 2
