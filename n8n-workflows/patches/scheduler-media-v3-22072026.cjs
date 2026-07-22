// BE (22/07/2026, po zywym tescie 16:11 - wiersz 184): upload mediow X v3.
// Dowod: INIT multipart na /2/media/upload dal 400 "Missing media field in JSON" -
// endpoint bez pod-sciezki to PROSTY upload. Wlasciwy kontrakt chunked (docs.x.com,
// zweryfikowane per-endpoint 22/07):
//   INIT:     POST /2/media/upload/initialize  (JSON: media_type, total_bytes, media_category)
//   APPEND:   POST /2/media/upload/{id}/append (multipart: media + segment_index)
//   FINALIZE: POST /2/media/upload/{id}/finalize (bez body; response z processing_info)
//   STATUS:   GET  /2/media/upload?command=STATUS&media_id= (bez zmian)
// OAuth1: body JSON/multipart poza sygnatura (tylko oauth_*). Patch OBU workflow.
const fs = require('fs');

const ALLOWED = ['saveDataErrorExecution', 'saveDataSuccessExecution', 'saveManualExecutions',
  'saveExecutionProgress', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'];

const NEW_XUPLOAD = `async function xUpload(K, media){
  const isVideo=media.mime.indexOf("video")===0;
  // v3 (22/07): chunked przez pod-sciezki initialize/append/finalize (kontrakt docs.x.com;
  // /2/media/upload BEZ pod-sciezki to prosty upload i INIT tam dawal 400 "Missing media field").
  const ib=JSON.stringify({media_type:media.mime,total_bytes:media.buf.length,
                           media_category:isVideo?"tweet_video":"tweet_image"});
  const iu="https://api.x.com/2/media/upload/initialize";
  const ir=await _req({hostname:"api.x.com",path:"/2/media/upload/initialize",method:"POST",
    headers:{Authorization:oauthAuth("POST",iu,K,null),"Content-Type":"application/json",
             "Content-Length":Buffer.byteLength(ib)}},Buffer.from(ib));
  const mid=_mid(ir.json);
  if(!mid){return {error:"INIT "+ir.status+" "+JSON.stringify(ir.json).slice(0,180)};}
  // APPEND w kawalkach po 4MB (wideo do ~20MB z Telegrama = do 5 kawalkow)
  const CH=4*1024*1024;
  for(let seg=0; seg*CH<media.buf.length; seg++){
    const part=media.buf.slice(seg*CH,(seg+1)*CH);
    const ap=_mpb({segment_index:String(seg)},part);
    const au="https://api.x.com/2/media/upload/"+mid+"/append";
    const ar=await _req({hostname:"api.x.com",path:"/2/media/upload/"+mid+"/append",method:"POST",
      headers:{Authorization:oauthAuth("POST",au,K,null),"Content-Type":ap.ct,"Content-Length":ap.buf.length}},ap.buf);
    if(ar.status<200||ar.status>=300){return {error:"APPEND seg"+seg+" "+ar.status+" "+JSON.stringify(ar.json).slice(0,150)};}
  }
  const fu="https://api.x.com/2/media/upload/"+mid+"/finalize";
  const fr=await _req({hostname:"api.x.com",path:"/2/media/upload/"+mid+"/finalize",method:"POST",
    headers:{Authorization:oauthAuth("POST",fu,K,null),"Content-Length":0}});
  if(fr.status<200||fr.status>=300){return {error:"FINALIZE "+fr.status+" "+JSON.stringify(fr.json).slice(0,180)};}
  // wideo: przetwarzanie asynchroniczne - poll STATUS do succeeded (max ~100s)
  let pi=(fr.json&&(fr.json.processing_info||(fr.json.data&&fr.json.data.processing_info)))||null;
  let waited=0;
  while(pi&&pi.state&&pi.state!=="succeeded"){
    if(pi.state==="failed"){return {error:"processing failed"};}
    const wait=Math.min((pi.check_after_secs||3),10)*1000;
    if(waited>100000){return {error:"processing timeout"};}
    await _sleep(wait); waited+=wait;
    const sp={command:"STATUS",media_id:String(mid)};
    const sq=Object.keys(sp).map(function(k){return _enc(k)+"="+_enc(sp[k]);}).join("&");
    const sr=await _req({hostname:"api.x.com",path:"/2/media/upload?"+sq,method:"GET",
      headers:{Authorization:oauthAuth("GET","https://api.x.com/2/media/upload",K,sp)}});
    pi=(sr.json&&(sr.json.processing_info||(sr.json.data&&sr.json.data.processing_info)))||null;
    if(!pi){break;}
  }
  return {media_id:String(_mid(fr.json)||mid)};
}`;

function patchCode(code) {
  if (code.indexOf('/2/media/upload/initialize') !== -1) return null; // juz v3
  const start = code.indexOf('async function xUpload');
  const endMarker = 'return {media_id:String(_mid(fr.json)||mid)};\n}';
  const end = code.indexOf(endMarker);
  if (start === -1 || end === -1) return null;
  return code.slice(0, start) + NEW_XUPLOAD + code.slice(end + endMarker.length);
}

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };
  for (const [id, label] of [['x1jJEbcWAe3FnpCa', 'scheduler'], ['G3nEIt5lIkiKemiK', 'xpublisher']]) {
    const w = await (await fetch(`${base}/api/v1/workflows/${id}`, { headers: H })).json();
    fs.writeFileSync(`${__dirname}/bk_${label}_mediav3_${Date.now()}.json`, JSON.stringify(w));
    let changed = false;
    for (const n of w.nodes) {
      if (n.name === 'Publish To X' && n.type === 'n8n-nodes-base.code') {
        const nc = patchCode(n.parameters.jsCode || '');
        if (nc) { n.parameters.jsCode = nc; changed = true; console.log(label + ': xUpload -> v3 (initialize/append/finalize)'); }
        else { console.log(label + ': juz v3 / marker nieznaleziony'); }
      }
    }
    if (!changed) continue;
    const settings = {};
    for (const k of ALLOWED) if (w.settings && w.settings[k] !== undefined) settings[k] = w.settings[k];
    const put = await fetch(`${base}/api/v1/workflows/${id}`, { method: 'PUT', headers: H,
      body: JSON.stringify({ name: w.name, nodes: w.nodes, connections: w.connections, settings }) });
    console.log(label + ' PUT:', put.status);
    if (put.status !== 200) { console.log(await put.text()); process.exit(1); }
    const d = await fetch(`${base}/api/v1/workflows/${id}/deactivate`, { method: 'POST', headers: H });
    const a = await fetch(`${base}/api/v1/workflows/${id}/activate`, { method: 'POST', headers: H });
    console.log(label + ' deactivate:', d.status, 'activate:', a.status);
  }
  console.log('DONE');
}
main().catch(e => { console.error(e.message); process.exit(1); });
