// BE (21/07/2026, incydent "grafiki nie wychodza + ksiega klamie"):
// A1) upload mediow X: INIT/APPEND/FINALIZE przenosza parametry z QUERY do multipart BODY
//     (kontrakt zweryfikowany docs.x.com media-upload-chunked 21/07: wszystkie parametry
//     w multipart/form-data; STATUS = GET z query. Blad zywy: INIT 400 "query parameter
//     [media_type] is not one of []" - egzekucje 72054/72183). Poprawka w OBU workflow
//     (Scheduler x1jJEbcWAe3FnpCa + Subagent X Publisher G3nEIt5lIkiKemiK - wspolny kod).
// A2) Mark Published (Scheduler) dopisuje ksiege per-wiersz: INSERT published_posts +
//     agent_messages RESPONSE + domkniecie content_items gdy nie ma juz wierszy w locie.
//     (Dotad Scheduler tylko przelaczal wiersz - raporty/dedup/CM nie widzialy publikacji;
//     stad falszywe "dzis nic nie wyszlo" od CM 21/07 15:49.)
// Wzorzec: bk_*.json backup + PUT z filtrowanymi settings + deactivate/activate po PUT.
const fs = require('fs');

const ALLOWED = ['saveDataErrorExecution', 'saveDataSuccessExecution', 'saveManualExecutions',
  'saveExecutionProgress', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'];

const OLD_UPLOAD_MARKER = 'parametry w QUERY = podpisywane, multipart body poza sygnatura';

const NEW_HELPERS_HEADER = [
  '// WSPOLNE HELPERY MEDIA v2 (21/07/2026, docs.x.com media-upload-chunked): Telegram getFile/download',
  '// -> X v2 POST /2/media/upload. KONTRAKT: WSZYSTKIE parametry (command/media_type/total_bytes/',
  '// media_category/media_id/segment_index) w multipart/form-data BODY - nie w query stringu',
  '// (query dawal INIT 400 "query parameter [media_type] is not one of []"). STATUS = GET z query.',
  '// OAuth1: przy multipart sygnatura obejmuje wylacznie oauth_* (body poza sygnatura).',
].join('\n');

const NEW_XUPLOAD = `function _mpb(fields, fileBuf){
  const bnd="agsb"+Date.now()+Math.floor(Math.random()*1e6);
  const parts=[];
  for(const k of Object.keys(fields)){
    parts.push(Buffer.from("--"+bnd+"\\r\\nContent-Disposition: form-data; name=\\""+k+"\\"\\r\\n\\r\\n"+fields[k]+"\\r\\n"));
  }
  if(fileBuf){
    parts.push(Buffer.from("--"+bnd+"\\r\\nContent-Disposition: form-data; name=\\"media\\"; filename=\\"m\\"\\r\\nContent-Type: application/octet-stream\\r\\n\\r\\n"));
    parts.push(fileBuf); parts.push(Buffer.from("\\r\\n"));
  }
  parts.push(Buffer.from("--"+bnd+"--\\r\\n"));
  return {buf:Buffer.concat(parts), ct:"multipart/form-data; boundary="+bnd};
}
async function xUpload(K, media){
  const U="https://api.x.com/2/media/upload";
  const isVideo=media.mime.indexOf("video")===0;
  const ip=_mpb({command:"INIT",total_bytes:String(media.buf.length),media_type:media.mime,
                 media_category:isVideo?"tweet_video":"tweet_image"});
  const ir=await _req({hostname:"api.x.com",path:"/2/media/upload",method:"POST",
    headers:{Authorization:oauthAuth("POST",U,K,null),"Content-Type":ip.ct,"Content-Length":ip.buf.length}},ip.buf);
  const mid=_mid(ir.json);
  if(!mid){return {error:"INIT "+ir.status+" "+JSON.stringify(ir.json).slice(0,180)};}
  // APPEND w kawalkach po 4MB (wideo do ~20MB z Telegrama = do 5 kawalkow)
  const CH=4*1024*1024;
  for(let seg=0; seg*CH<media.buf.length; seg++){
    const part=media.buf.slice(seg*CH,(seg+1)*CH);
    const ap=_mpb({command:"APPEND",media_id:String(mid),segment_index:String(seg)},part);
    const ar=await _req({hostname:"api.x.com",path:"/2/media/upload",method:"POST",
      headers:{Authorization:oauthAuth("POST",U,K,null),"Content-Type":ap.ct,"Content-Length":ap.buf.length}},ap.buf);
    if(ar.status<200||ar.status>=300){return {error:"APPEND seg"+seg+" "+ar.status+" "+JSON.stringify(ar.json).slice(0,150)};}
  }
  const fz=_mpb({command:"FINALIZE",media_id:String(mid)});
  const fr=await _req({hostname:"api.x.com",path:"/2/media/upload",method:"POST",
    headers:{Authorization:oauthAuth("POST",U,K,null),"Content-Type":fz.ct,"Content-Length":fz.buf.length}},fz.buf);
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
      headers:{Authorization:oauthAuth("GET",U,K,sp)}});
    pi=(sr.json&&(sr.json.processing_info||(sr.json.data&&sr.json.data.processing_info)))||null;
    if(!pi){break;}
  }
  return {media_id:String(_mid(fr.json)||mid)};
}`;

const NEW_MARK_PUBLISHED = `UPDATE post_queue SET status = CASE WHEN {{ $json.ok }} THEN 'published' ELSE 'failed' END, updated_at=NOW() WHERE id = {{ $json.postId }};
INSERT INTO published_posts (platform, brand, content, topic, post_url, post_id, published_at, content_item_id, metadata)
SELECT pq.platform, pq.brand, pq.content, pq.topic, '{{ $json.tweet_url }}', '{{ $json.tweet_id }}', NOW(), pq.content_item_id, '{"source":"scheduler"}'::jsonb
FROM post_queue pq WHERE pq.id = {{ $json.postId }} AND {{ $json.ok }};
INSERT INTO agent_messages (from_agent_id, to_agent_id, message_type, payload, status)
SELECT (SELECT agent_id FROM agent_registry WHERE agent_name='x-agent'),
       (SELECT agent_id FROM agent_registry WHERE agent_name='content-manager'),
       'response',
       jsonb_build_object('channel', pq.platform, 'ok', {{ $json.ok }}, 'tweet_url', '{{ $json.tweet_url }}', 'content_item_id', pq.content_item_id::text, 'pq_id', pq.id, 'source', 'scheduler'),
       'unread'
FROM post_queue pq
WHERE pq.id = {{ $json.postId }}
  AND (SELECT agent_id FROM agent_registry WHERE agent_name='x-agent') IS NOT NULL;
UPDATE content_items ci SET status='published'
WHERE ci.id = (SELECT content_item_id FROM post_queue WHERE id = {{ $json.postId }})
  AND ci.status='dispatching'
  AND NOT EXISTS (SELECT 1 FROM post_queue q WHERE q.content_item_id=ci.id AND q.status IN ('review','scheduled','queued','dispatching'));`;

function patchCode(code) {
  if (code.indexOf(OLD_UPLOAD_MARKER) === -1) return null; // juz zapatchowane albo inny kod
  // podmien komentarz-naglowek helperow
  code = code.replace(/\/\/ WSPOLNE HELPERY MEDIA[^\n]*\n\/\/ \(chunked[^\n]*\n/, NEW_HELPERS_HEADER + '\n');
  // podmien cala funkcje xUpload (od "async function xUpload" do konca "return {media_id...};\n}")
  const start = code.indexOf('async function xUpload');
  const endMarker = 'return {media_id:String(_mid(fr.json)||mid)};\n}';
  const end = code.indexOf(endMarker);
  if (start === -1 || end === -1) return null;
  code = code.slice(0, start) + NEW_XUPLOAD + code.slice(end + endMarker.length);
  return code;
}

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };
  for (const [id, label, alsoLedger] of [['x1jJEbcWAe3FnpCa', 'scheduler', true],
                                         ['G3nEIt5lIkiKemiK', 'xpublisher', false]]) {
    const w = await (await fetch(`${base}/api/v1/workflows/${id}`, { headers: H })).json();
    fs.writeFileSync(`${__dirname}/bk_${label}_media_${Date.now()}.json`, JSON.stringify(w));
    let changed = false;
    for (const n of w.nodes) {
      if (n.name === 'Publish To X' && n.type === 'n8n-nodes-base.code') {
        const nc = patchCode(n.parameters.jsCode || '');
        if (nc) { n.parameters.jsCode = nc; changed = true; console.log(label + ': xUpload -> multipart body'); }
        else { console.log(label + ': upload JUZ zapatchowany / marker nieznaleziony'); }
      }
      if (alsoLedger && n.name === 'Mark Published') {
        if ((n.parameters.query || '').indexOf('published_posts') === -1) {
          n.parameters.query = NEW_MARK_PUBLISHED; changed = true;
          console.log(label + ': Mark Published -> ksiega per-wiersz');
        } else { console.log(label + ': Mark Published juz z ksiega'); }
      }
    }
    if (!changed) { console.log(label + ': bez zmian, pomijam PUT'); continue; }
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
