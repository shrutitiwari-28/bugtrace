import ast

from audit import audit_patch
from benchmark.bugs import BUGS


def test_ids_unique_and_split_sizes():
    ids = [b["id"] for b in BUGS]
    assert len(ids) == len(set(ids)) == 15
    assert sum(b["split"] == "tuning" for b in BUGS) == 10
    assert sum(b["split"] == "heldout" for b in BUGS) == 5


def test_all_code_is_valid_python():
    for b in BUGS:
        for key in ("source", "reference", "test", "regression"):
            ast.parse(b[key])


def test_reference_fix_differs_from_bug():
    for b in BUGS:
        assert b["source"] != b["reference"], b["id"]


def test_reference_fixes_pass_the_audit():
    for b in BUGS:
        assert audit_patch(b["reference"]) == [], b["id"]
