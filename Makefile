s1:
	python3 spec_pack/tools/run_s1.py

s2:
	python3 spec_pack/tools/s2_contradiction.py
	python3 spec_pack/tools/s2_check.py

ci:
	./spec_pack/tools/ci_local.sh

freeze:
	mkdir -p artifacts && zip -r artifacts/spec_pack_v0.2-pre.zip spec_pack
	shasum -a 256 artifacts/spec_pack_v0.2-pre.zip > artifacts/spec_pack_v0.2-pre.sha256

a2h_semantics:
	python3 spec_pack/tools/a2h_semantics.py --check && python3 spec_pack/tools/a2h_semantics.py --emit

a2h:
	python3 spec_pack/tools/a2h_compile.py --emit

a2h_check:
	python3 spec_pack/tools/a2h_compile.py --check