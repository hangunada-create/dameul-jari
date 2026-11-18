"""기억자리 배포 폴더(dist) 만들기: index.html, manifest, 서비스워커, 아이콘."""
import json, os, re, shutil
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
VERSION = "2.5.2"
shutil.rmtree(DIST, ignore_errors=True)
os.makedirs(os.path.join(DIST, "icons"))

body = open(os.path.join(ROOT, "app.html"), encoding="utf-8").read()
title = re.search(r"<title>.*?</title>", body).group(0)
body = body.replace(title, "", 1)
html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#23407F">
<meta name="description" content="기억을 궁전 곳곳에 담습니다. 실제 장소 사진으로 만드는 장소법 연습 앱">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/icon-192.png">
{title}
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
{body}
</body>
</html>
"""
open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(html)

# 아이콘: 남색 바탕에 황토색 아치(문) 하나와 그 안의 점 하나 = '자리'
def icon(size, maskable=False):
    s = 4
    S = size * s
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bg = (35, 64, 127, 255)
    if maskable:
        d.rectangle([0, 0, S, S], fill=bg)
        k = 0.62
    else:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=bg)
        k = 0.78
    w = S * k
    ox = (S - w) / 2
    ochre = (216, 165, 82, 255)
    cream = (243, 243, 238, 255)
    # 아치
    aw, ah = w * 0.56, w * 0.70
    ax, ay = S / 2 - aw / 2, S / 2 - ah / 2 + w * 0.02
    t = w * 0.075
    d.rectangle([ax, ay + aw / 2, ax + aw, ay + ah], fill=ochre)
    d.ellipse([ax, ay, ax + aw, ay + aw], fill=ochre)
    ix, iy, iw = ax + t, ay + t, aw - 2 * t
    d.rectangle([ix, iy + iw / 2, ix + iw, ay + ah], fill=bg)
    d.ellipse([ix, iy, ix + iw, iy + iw], fill=bg)
    # 문턱(바닥선)
    d.rectangle([ox + w * 0.12, ay + ah, ox + w * 0.88, ay + ah + t * 0.9], fill=ochre)
    # 자리에 놓인 점
    r = w * 0.085
    cx, cy = S / 2, ay + ah * 0.62
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=cream)
    return im.resize((size, size), Image.LANCZOS)

for n in (192, 512):
    icon(n).save(os.path.join(DIST, "icons", f"icon-{n}.png"))
    icon(n, True).save(os.path.join(DIST, "icons", f"maskable-{n}.png"))

manifest = {
    "name": "담을자리 – 사진으로 만드는 기억의 궁전",
    "short_name": "담을자리",
    "description": "기억을 궁전 곳곳에 담습니다. 실제 장소 사진으로 만드는 장소법 연습 앱",
    "lang": "ko",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#ECEDE8",
    "theme_color": "#23407F",
    "categories": ["education", "productivity"],
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icons/maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
        {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
json.dump(manifest, open(os.path.join(DIST, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

sw = """// 담을자리 오프라인 캐시와 복습 알림 v__VERSION__
const CACHE="dameul-__VERSION__";
const SHELL=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET")return;
  e.respondWith(caches.match(e.request,{ignoreSearch:e.request.mode==="navigate"}).then(hit=>{
    const net=fetch(e.request).then(res=>{if(res&&(res.ok||res.type==="opaque")){const cp=res.clone();caches.open(CACHE).then(c=>c.put(e.request,cp))}return res}).catch(()=>hit||caches.match("./"));
    return hit||net;
  }));
});
/* 복습 알림: 브라우저가 하루 몇 번 깨워 주면, 정한 시각이 지났고 복습할 목록이 있을 때 하루 한 번만 알린다 */
function idb(){return new Promise((res,rej)=>{const r=indexedDB.open("dameul",1);r.onupgradeneeded=()=>{const d=r.result;["kv","photos"].forEach(n=>{if(!d.objectStoreNames.contains(n))d.createObjectStore(n)})};r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
function kvGet(d,k){return new Promise((res,rej)=>{const q=d.transaction("kv").objectStore("kv").get(k);q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error)})}
function kvPut(d,k,v){return new Promise((res,rej)=>{const tx=d.transaction("kv","readwrite");tx.objectStore("kv").put(v,k);tx.oncomplete=()=>res();tx.onerror=()=>rej(tx.error)})}
async function checkDue(){
  const d=await idb();const s=await kvGet(d,"db");if(!s)return;
  const db=JSON.parse(s);if(!(db.settings||{}).notifyOn)return;
  const now=new Date();const t0=new Date(now);t0.setHours(0,0,0,0);const today=t0.getTime();
  let total=0;
  for(const p of db.palaces){
    const due=db.lists.filter(l=>!l.example&&l.palaceId===p.id&&l.built&&l.due<=today);total+=due.length;
    const nt=p.notify;if(!nt||!nt.on||!due.length)continue;
    if(now.getHours()<(nt.hour==null?20:nt.hour))continue;
    const key="lastNotified:"+p.id;if((await kvGet(d,key))===today)continue;
    await self.registration.showNotification(`‘${p.name}’을(를) 걸을 차례입니다`,{body:due.length===1?`‘${due[0].title}’ 복습할 차례입니다.`:`‘${due[0].title}’ 외 ${due.length-1}개를 복습할 차례입니다.`,icon:"icons/icon-192.png",badge:"icons/icon-192.png",tag:"dameul-"+p.id});
    await kvPut(d,key,today);
  }
  try{if(self.navigator.setAppBadge)await self.navigator.setAppBadge(total)}catch(e){}
}
self.addEventListener("periodicsync",e=>{if(e.tag==="review-check")e.waitUntil(checkDue())});
self.addEventListener("notificationclick",e=>{e.notification.close();e.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(cs=>{for(const c of cs){if("focus" in c)return c.focus()}return self.clients.openWindow("./")}))});
""".replace("__VERSION__", VERSION)
open(os.path.join(DIST, "sw.js"), "w", encoding="utf-8").write(sw)
print("built", os.listdir(DIST))
