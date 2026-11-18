// 담을자리 오프라인 캐시와 복습 알림 v2.4.2
const CACHE="dameul-2.4.2";
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
