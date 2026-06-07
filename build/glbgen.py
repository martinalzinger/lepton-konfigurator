# glbgen.py – erzeugt einfache, druck-/web-taugliche GLB-Platzhaltermodelle (glTF 2.0 binär).
# Wird vom Ersatzteil-Build genutzt, solange noch keine echten STEP/GLB-Daten hinterlegt sind.
# Keine externen Pakete nötig (reines Python 3). Flat-Shading (pro Dreieck eine Normale).
import struct, math, json

STEEL=[0.72,0.74,0.78,1.0]   # Stahl/Metall
DARK =[0.12,0.12,0.13,1.0]   # Gummi/Riemen
COPPER=[0.78,0.55,0.34,1.0]  # Bronze/Lager

def _tri_normal(a,b,c):
    ux,uy,uz=b[0]-a[0],b[1]-a[1],b[2]-a[2]
    vx,vy,vz=c[0]-a[0],c[1]-a[1],c[2]-a[2]
    nx,ny,nz=uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
    l=math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
    return (nx/l,ny/l,nz/l)

def _mesh(verts, faces):
    """verts: Liste (x,y,z); faces: Liste (i,j,k) -> Flat-Shaded Positions/Normals/Indices."""
    pos=[]; nrm=[]; idx=[]
    n=0
    for (i,j,k) in faces:
        a,b,c=verts[i],verts[j],verts[k]
        nn=_tri_normal(a,b,c)
        for p in (a,b,c):
            pos.append(p); nrm.append(nn)
        idx+= [n,n+1,n+2]; n+=3
    return pos,nrm,idx

# ---------- 2D-Profile (in XZ-Ebene) ----------
def regular_polygon(r, seg):
    return [(r*math.cos(2*math.pi*i/seg), r*math.sin(2*math.pi*i/seg)) for i in range(seg)]

def star_poly(r_out, r_in, points):
    pts=[]
    for i in range(points*2):
        r=r_out if i%2==0 else r_in
        a=math.pi*i/points
        pts.append((r*math.cos(a), r*math.sin(a)))
    return pts

def gear_poly(r_tip, r_root, teeth):
    pts=[]; step=2*math.pi/teeth
    for i in range(teeth):
        a=i*step
        pts.append((r_root*math.cos(a+0.04*step), r_root*math.sin(a+0.04*step)))
        pts.append((r_tip *math.cos(a+0.16*step), r_tip *math.sin(a+0.16*step)))
        pts.append((r_tip *math.cos(a+0.34*step), r_tip *math.sin(a+0.34*step)))
        pts.append((r_root*math.cos(a+0.46*step), r_root*math.sin(a+0.46*step)))
        pts.append((r_root*math.cos(a+0.96*step), r_root*math.sin(a+0.96*step)))
    return pts

# ---------- 3D-Körper ----------
def prism(poly, thickness):
    """Extrudiert ein 2D-Profil (XZ) entlang Y. Deckel als Fächer vom Mittelpunkt."""
    h=thickness/2.0; N=len(poly)
    verts=[]
    for (x,z) in poly: verts.append((x, h, z))   # 0..N-1  top
    for (x,z) in poly: verts.append((x,-h, z))   # N..2N-1 bottom
    ct=len(verts); verts.append((0, h,0))         # center top
    cb=len(verts); verts.append((0,-h,0))         # center bottom
    faces=[]
    for i in range(N):
        j=(i+1)%N
        faces.append((i, j, N+j)); faces.append((i, N+j, N+i))   # Seitenwand
        faces.append((ct, j, i))                                  # Deckel oben
        faces.append((cb, N+i, N+j))                              # Boden unten
    return _mesh(verts,faces)

def box(sx,sy,sz):
    x,y,z=sx/2,sy/2,sz/2
    v=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    f=[(0,1,2),(0,2,3),(5,4,7),(5,7,6),(4,0,3),(4,3,7),(1,5,6),(1,6,2),(3,2,6),(3,6,7),(4,5,1),(4,1,0)]
    return _mesh(v,f)

def torus(R, r, su, sv):
    verts=[]
    for i in range(su):
        u=2*math.pi*i/su
        for j in range(sv):
            v=2*math.pi*j/sv
            x=(R+r*math.cos(v))*math.cos(u)
            y=r*math.sin(v)
            z=(R+r*math.cos(v))*math.sin(u)
            verts.append((x,y,z))
    faces=[]
    for i in range(su):
        for j in range(sv):
            a=i*sv+j; b=((i+1)%su)*sv+j; c=((i+1)%su)*sv+(j+1)%sv; d=i*sv+(j+1)%sv
            faces.append((a,b,c)); faces.append((a,c,d))
    return _mesh(verts,faces)

def merge(*parts):
    """Mehrere _mesh-Resultate zu einem zusammenfassen."""
    pos=[]; nrm=[]; idx=[]; off=0
    for (p,n,ix) in parts:
        pos+=p; nrm+=n; idx+=[x+off for x in ix]; off+=len(p)
    return pos,nrm,idx

# ---------- GLB-Serialisierung ----------
def _pad4(b, fill=b'\x00'):
    while len(b)%4: b+=fill
    return b

def build_glb(primitives):
    """primitives: Liste {geom:(pos,nrm,idx), color:[r,g,b,a]}. Ein Mesh, je Primitive ein Material."""
    bin_data=bytearray()
    accessors=[]; bufferViews=[]; materials=[]; prims=[]
    def add_view(byts, target):
        off=len(bin_data)
        bin_data.extend(byts)
        while len(bin_data)%4: bin_data.append(0)
        bufferViews.append({"buffer":0,"byteOffset":off,"byteLength":len(byts),"target":target})
        return len(bufferViews)-1
    for pr in primitives:
        pos,nrm,idx=pr["geom"]
        # POSITION
        flat=[]; mn=[1e9,1e9,1e9]; mx=[-1e9,-1e9,-1e9]
        for v in pos:
            for k in range(3):
                flat.append(v[k]); mn[k]=min(mn[k],v[k]); mx[k]=max(mx[k],v[k])
        pv=add_view(struct.pack("<%df"%len(flat),*flat), 34962)
        accessors.append({"bufferView":pv,"componentType":5126,"count":len(pos),"type":"VEC3","min":mn,"max":mx})
        a_pos=len(accessors)-1
        # NORMAL
        nf=[]
        for v in nrm: nf+= [v[0],v[1],v[2]]
        nv=add_view(struct.pack("<%df"%len(nf),*nf), 34962)
        accessors.append({"bufferView":nv,"componentType":5126,"count":len(nrm),"type":"VEC3"})
        a_nrm=len(accessors)-1
        # INDICES (uint32)
        iv=add_view(struct.pack("<%dI"%len(idx),*idx), 34963)
        accessors.append({"bufferView":iv,"componentType":5125,"count":len(idx),"type":"SCALAR"})
        a_idx=len(accessors)-1
        col=pr.get("color",STEEL)
        materials.append({"pbrMetallicRoughness":{"baseColorFactor":col,"metallicFactor":pr.get("metal",0.85),"roughnessFactor":pr.get("rough",0.42)},"name":pr.get("name","mat")})
        prims.append({"attributes":{"POSITION":a_pos,"NORMAL":a_nrm},"indices":a_idx,"material":len(materials)-1})
    gltf={
        "asset":{"version":"2.0","generator":"alzinger-glbgen"},
        "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0}],
        "meshes":[{"primitives":prims}],
        "materials":materials,"accessors":accessors,"bufferViews":bufferViews,
        "buffers":[{"byteLength":len(bin_data)}]
    }
    json_chunk=_pad4(json.dumps(gltf,separators=(",",":")).encode("utf8"), b' ')
    bin_chunk=_pad4(bytes(bin_data))
    total=12+8+len(json_chunk)+8+len(bin_chunk)
    out=bytearray()
    out+=struct.pack("<III",0x46546C67,2,total)
    out+=struct.pack("<II",len(json_chunk),0x4E4F534A)+json_chunk
    out+=struct.pack("<II",len(bin_chunk),0x004E4942)+bin_chunk
    return bytes(out)

# ---------- Vordefinierte Ersatzteil-Platzhalter ----------
def model(kind):
    if kind=="scheibe":   # Sternscheibe
        return build_glb([{"geom":prism(star_poly(60,40,6),14),"color":STEEL}])
    if kind=="welle":     # Welle / Achse
        return build_glb([{"geom":prism(regular_polygon(14,40),220),"color":STEEL,"rough":0.3}])
    if kind=="lager":     # Lager / Ring
        return build_glb([{"geom":torus(46,16,40,16),"color":COPPER,"metal":0.9,"rough":0.35}])
    if kind=="ritzel":    # Antriebsritzel / Zahnrad
        return build_glb([{"geom":prism(gear_poly(52,38,16),22),"color":STEEL,"rough":0.35}])
    if kind=="trommel":   # Umlenktrommel / Walze
        return build_glb([{"geom":prism(regular_polygon(55,48),300),"color":STEEL,"rough":0.4}])
    if kind=="keilriemen":# Keilriemen
        return build_glb([{"geom":torus(80,10,48,12),"color":DARK,"metal":0.0,"rough":0.7}])
    if kind=="abstreifer":# Abstreifer / Leiste
        return build_glb([{"geom":box(260,18,46),"color":DARK,"metal":0.1,"rough":0.6}])
    if kind=="gehaeuse":  # Gehäuse / E-Box
        return build_glb([{"geom":box(120,150,70),"color":STEEL,"rough":0.5}])
    # default: Würfel
    return build_glb([{"geom":box(80,80,80),"color":STEEL}])

if __name__=="__main__":
    import sys
    open(sys.argv[2],"wb").write(model(sys.argv[1]))
    print("ok", sys.argv[1], "->", sys.argv[2])
