import orjson

from xme.psp.schema import PSP


def test_psp_json_schema_has_block_defs():
    schema = PSP.model_json_schema(PSP)
    j = orjson.dumps(schema)
    assert b"Block" in j and b"properties" in j
