s1:
	python spec_pack/tools/run_s1.py

s2:
	python spec_pack/tools/s2_contradiction.py
	python spec_pack/tools/s2_check.py

ci:
	./spec_pack/tools/ci_local.sh

freeze:
	mkdir -p artifacts && zip -r artifacts/spec_pack_v0.2-pre.zip spec_pack
	shasum -a 256 artifacts/spec_pack_v0.2-pre.zip > artifacts/spec_pack_v0.2-pre.sha256

a2h:
	python spec_pack/tools/a2h_compile.py --emit
	python spec_pack/tools/merkle_hasher.py --in spec_pack/samples/journal.ndjson --out spec_pack/samples/journal.ndjson

a2h_check:
	python spec_pack/tools/a2h_compile.py --check