#!/usr/bin/env python
import argparse, json, hashlib, os, sys

def load_ndjson(path):
    if not os.path.exists(path): return []
    with open(path,"r",encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

def write_ndjson(path, items):
    with open(path,"w",encoding="utf-8") as f:
        for o in items:
            f.write(json.dumps(o, separators=((",",":")))+"\n")

def merkle_root(hex_hashes):
    layer=[bytes.fromhex(h) for h in hex_hashes]
    if not layer: return ""
    while len(layer)>1:
        if len(layer)%2==1: layer.append(layer[-1])
        layer=[hashlib.sha256(layer[i]+layer[i+1]).digest() for i in range(0,len(layer),2)]
    return layer[0].hex()

def recompute_chain(items):
    prev=None
    hex_hashes=[]
    for o in items:
        core={k:o[k] for k in o if k not in ["hash","parent_hash","merkle_root_day"]}
        s=json.dumps(core, separators=((",",":"))).encode()
        h=hashlib.sha256(s + (bytes.fromhex(prev) if prev else b"" )).hexdigest()
        o["parent_hash"]=prev
        o["hash"]=h
        hex_hashes.append(h)
        prev=h
    root=merkle_root(hex_hashes)
    for o in items:
        o["merkle_root_day"]=root
    return items

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args=ap.parse_args()
    items=load_ndjson(args.inp)
    items=recompute_chain(items)
    write_ndjson(args.out, items)
    print(json.dumps({"entries": len(items), "merkle_root_day": items[-1]["merkle_root_day"] if items else ""}, indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())