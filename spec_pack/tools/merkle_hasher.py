#!/usr/bin/env python3
import argparse, json, hashlib, time
def h64(b): return hashlib.sha256(b).hexdigest()
def load(path):
    with open(path,"r",encoding="utf-8") as f: return [json.loads(l) for l in f if l.strip()]
def dump(path, items):
    with open(path,"w",encoding="utf-8") as f:
        for o in items: f.write(json.dumps(o, separators=((",", ":")))+"\n")
def merkle_root(ids):
    layer = [bytes.fromhex(h64(i.encode())) for i in ids]
    if not layer: return None
    while len(layer) > 1:
        if len(layer) % 2 == 1: layer.append(layer[-1])
        layer = [hashlib.sha256(layer[i]+layer[i+1]).digest() for i in range(0,len(layer),2)]
    return layer[0].hex()
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args=ap.parse_args()
    items=load(args.inp)
    prev=None; day=str(time.strftime("%Y%m%d"))
    ids=[]
    for o in items:
        base=json.dumps({k:o[k] for k in o if k not in ["hash","parent_hash","merkle_root_day"]}, separators=((",", ":"))).encode()
        h=h64(base+(prev.encode() if prev else b""))
        o["parent_hash"]=prev
        o["hash"]=h
        ids.append(h)
        prev=h
    root=merkle_root(ids)
    for o in items: o["merkle_root_day"]=root
    dump(args.out, items)
