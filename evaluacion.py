"""Evaluación de Pathfinder A*: compara A*, Dijkstra y búsqueda voraz en 120 mapas.
Colocar junto a main.py y ejecutar: python evaluacion.py"""
import os, sys, random, time, statistics as st, json
os.environ["SDL_VIDEODRIVER"]="dummy"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pygame; pygame.init()
from queue import PriorityQueue
from pathfinder.algoritmo import astar
from pathfinder.algoritmo.nodo import Node, make_grid
from pathfinder.mapas import MAZES, set_cell
from pathfinder.config import WIDTH

class Fake: pass
def board(gen, seed, n=50):
    random.seed(seed)
    a=Fake(); a.rows=n; a.grid=make_grid(n,WIDTH); a.maze_head=None
    m=max(1,n//6); a.start=a.grid[m][n//2]; a.end=a.grid[n-1-m][n//2]
    a.start.make_start(); a.end.make_end()
    for _ in gen(a): pass
    # snap endpoints to free cells
    def free(node, avoid):
        if not node.is_barrier() and node is not avoid: return node
        from collections import deque
        q=deque([node.get_pos()]); seen={node.get_pos()}
        while q:
            i,j=q.popleft()
            for di,dj in [(-1,0),(0,1),(1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                p=(i+di,j+dj)
                if 0<=p[0]<n and 0<=p[1]<n and p not in seen:
                    c=a.grid[p[0]][p[1]]
                    if not c.is_barrier() and c is not avoid: return c
                    seen.add(p); q.append(p)
    a.start=free(a.start,a.end); a.end=free(a.end,a.start)
    a.start.make_start(); a.end.make_end()
    return a

def snapshot(a):
    return [[(nd.is_barrier(), nd.weight) for nd in r] for r in a.grid]
def restore(a, snap):
    for r,sr in zip(a.grid,snap):
        for nd,(b,w) in zip(r,sr):
            nd._color=(0,0,0) if b else (255,255,255); nd.weight=w
    a.start._color=(255,165,0); a.end._color=(64,224,208)
    for r in a.grid:
        for nd in r: nd.update_neighbors(a.grid)

def run_project(a, hfun):
    old=astar.h; astar.h=hfun
    Node.closed_count=0; info={}
    gen=astar.algorithm(a.grid,a.start,a.end,info); steps=0
    t0=time.perf_counter()
    try:
        while True: next(gen); steps+=1
    except StopIteration as s: found=s.value
    dt=time.perf_counter()-t0
    astar.h=old
    cost=info["g"][a.end] if found else None
    exp=sum(1 for r in a.grid for nd in r if nd.is_closed())+1
    return dict(found=found,cost=cost,exp=exp,ms=dt*1000,len=len(info.get("path",[]))-1 if found else None)

def greedy(a):
    h=astar.h; s,e=a.start,a.end
    pq=PriorityQueue(); c=0; pq.put((h(s.get_pos(),e.get_pos()),c,s))
    came={}; g={s:0}; seen={s}; exp=0
    t0=time.perf_counter()
    while not pq.empty():
        cur=pq.get()[2]; exp+=1
        if cur==e:
            return dict(found=True,cost=g[e],exp=exp,ms=(time.perf_counter()-t0)*1000)
        for nb in cur.neighbors:
            if nb not in seen:
                seen.add(nb); g[nb]=g[cur]+nb.weight; came[nb]=cur; c+=1
                pq.put((h(nb.get_pos(),e.get_pos()),c,nb))
    return dict(found=False,cost=None,exp=exp,ms=0)

res={}
SEEDS=range(1,31)
for name,gen in MAZES:
    rows=[]
    for sd in SEEDS:
        a=board(gen,sd); snap=snapshot(a)
        restore(a,snap); A=run_project(a, astar.h)
        restore(a,snap); D=run_project(a, lambda p,q:0)
        restore(a,snap); G=greedy(a)
        free=sum(1 for r in a.grid for nd in r if not nd.is_barrier())
        rows.append(dict(A=A,D=D,G=G,free=free))
    res[name]=rows
json.dump(res,open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados_evaluacion.json"),"w"),default=str)
for name,rows in res.items():
    ok=[r for r in rows if r["A"]["found"]]
    print(name, "found",len(ok),"/",len(rows))
    if not ok: continue
    mA=st.mean(r["A"]["exp"] for r in ok); mD=st.mean(r["D"]["exp"] for r in ok); mG=st.mean(r["G"]["exp"] for r in ok)
    same=sum(1 for r in ok if r["A"]["cost"]==r["D"]["cost"])
    gopt=sum(1 for r in ok if r["G"]["cost"]==r["A"]["cost"])
    gext=st.mean((r["G"]["cost"]-r["A"]["cost"])/r["A"]["cost"]*100 for r in ok)
    print(f"  expA {mA:.0f} expD {mD:.0f} expG {mG:.0f} ahorro A/D {100*(1-mA/mD):.1f}%  A==D cost {same}/{len(ok)}  G optimal {gopt}/{len(ok)} G extra cost {gext:.1f}%")
    print(f"  costA {st.mean(r['A']['cost'] for r in ok):.1f} costG {st.mean(r['G']['cost'] for r in ok):.1f} msA {st.mean(r['A']['ms'] for r in ok):.2f} max {max(r['A']['ms'] for r in ok):.2f} msD {st.mean(r['D']['ms'] for r in ok):.2f} free {st.mean(r['free'] for r in ok):.0f}")
