// BE (22/07/2026, decyzja Tomasza: "zatwierdzone ma isc samo" takze na LinkedIn):
// galaz LinkedIn w AGS Scheduler - publikacja PRZEZ SCHEDULER (sloty per wiersz!),
// nie przez delegata (ignorowal sloty - incydent 20/07). Zmiany:
//  1. Get Keys: + linkedin_access_token/linkedin_author_urn (li_token/li_author).
//  2. Route Platform (IF 2.2 wg wzorca AP-301): x -> Publish To X; inne -> LinkedIn.
//  3. Publish To LinkedIn (Scheduler): kod 1:1 z Subagent LinkedIn Publisher v2
//     (registerUpload + PUT + ugcPosts, obrazy dzialaja), kontrakt wyjscia jak X
//     (ok/postId/tweet_id/tweet_url) -> Mark Published LI (ta sama ksiega per-wiersz)
//     -> LI Confirm (telegram).
// Po patchu: SQL Tomasza przelacza channels linkedin na 'post_queue'.
const fs = require('fs');

const ALLOWED = ['saveDataErrorExecution', 'saveDataSuccessExecution', 'saveManualExecutions',
  'saveExecutionProgress', 'executionTimeout', 'errorWorkflow', 'timezone', 'executionOrder'];

const LI_CODE = `// Scheduler "Publish To LinkedIn" (22/07): kanon 'zatwierdzone publikuje sie ZAWSZE'
// wraca na LinkedIn PRZEZ SCHEDULER. Kod przeniesiony 1:1 z Subagent LinkedIn Publisher v2
// (registerUpload feedshare-image -> PUT -> ugcPosts). Kontrakt wyjscia jak Publish To X.
const K0=$('Get Keys').first().json;
const token=K0.li_token, author=K0.li_author, TG=K0.tg||'';
const text=($json.content||'').toString();
const postId=$json.id;
if(!text.trim()){ return [{json:{ok:false,postId:postId,error:'empty content'}}]; }
if(!token||!author){ return [{json:{ok:false,postId:postId,error:'missing linkedin_access_token/linkedin_author_urn in app_secrets'}}]; }
const https=require('https');
function req(opts, bodyBuf){
  return new Promise(function(resolve,reject){
    const r=https.request(opts,function(res){
      const d=[];res.on('data',function(c){d.push(c);});
      res.on('end',function(){const buf=Buffer.concat(d);let j={};
        try{j=JSON.parse(buf.toString('utf8'));}catch(e){}
        resolve({status:res.statusCode,json:j,buf:buf,hdr:res.headers});});});
    r.on('error',reject); if(bodyBuf){r.write(bodyBuf);} r.end();});
}
async function tgFetch(fileId){
  if(!TG){return null;}
  const gf=await req({hostname:'api.telegram.org',path:'/bot'+TG+'/getFile?file_id='+encodeURIComponent(fileId),method:'GET'});
  const fp=gf.json&&gf.json.result&&gf.json.result.file_path; if(!fp){return null;}
  const dl=await req({hostname:'api.telegram.org',path:'/file/bot'+TG+'/'+fp,method:'GET'});
  if(dl.status!==200||!dl.buf||!dl.buf.length){return null;}
  return dl.buf;
}
async function liUpload(buf, isVideo){
  const recipe=isVideo?'urn:li:digitalmediaRecipe:feedshare-video':'urn:li:digitalmediaRecipe:feedshare-image';
  const regBody=JSON.stringify({registerUploadRequest:{recipes:[recipe],
    owner:author,serviceRelationships:[{relationshipType:'OWNER',identifier:'urn:li:userGeneratedContent'}]}});
  const reg=await req({hostname:'api.linkedin.com',path:'/v2/assets?action=registerUpload',method:'POST',
    headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json',
             'X-Restli-Protocol-Version':'2.0.0','Content-Length':Buffer.byteLength(regBody)}},Buffer.from(regBody));
  const v=reg.json&&reg.json.value; if(!v){return {error:'registerUpload '+reg.status};}
  const asset=v.asset;
  const mech=v.uploadMechanism&&v.uploadMechanism['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest'];
  const up=mech&&mech.uploadUrl; if(!(asset&&up)){return {error:'no uploadUrl'};}
  const mu=up.match(/^https:\\/\\/([^\\/]+)(\\/.*)$/); if(!mu){return {error:'bad uploadUrl'};}
  const put=await req({hostname:mu[1],path:mu[2],method:'PUT',
    headers:{'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream','Content-Length':buf.length}},buf);
  if(put.status<200||put.status>=300){return {error:'PUT '+put.status};}
  return {asset:asset};
}
let mediaList=$json.media; if(typeof mediaList==='string'){try{mediaList=JSON.parse(mediaList);}catch(e){mediaList=[];}}
if(!Array.isArray(mediaList)){mediaList=[];}
const vids=mediaList.filter(function(m){return m&&m.file_id&&m.kind==='video';});
const pics=mediaList.filter(function(m){return m&&m.file_id&&m.kind!=='video';});
const useList=vids.length?[vids[0]]:pics.slice(0,4);
const isVideoPost=vids.length>0;
const assets=[],merrs=[];
for(const md of useList){
  const buf=await tgFetch(md.file_id); if(!buf){merrs.push('tg download fail');continue;}
  const upd=await liUpload(buf,isVideoPost); if(upd.asset){assets.push(upd.asset);}else{merrs.push(upd.error||'upload fail');}
}
const share={shareCommentary:{text:text},shareMediaCategory:assets.length?(isVideoPost?'VIDEO':'IMAGE'):'NONE'};
if(assets.length){share.media=assets.map(function(a){return {status:'READY',media:a};});}
const payload=JSON.stringify({author:author,lifecycleState:'PUBLISHED',
  specificContent:{'com.linkedin.ugc.ShareContent':share},
  visibility:{'com.linkedin.ugc.MemberNetworkVisibility':'PUBLIC'}});
const result=await req({hostname:'api.linkedin.com',path:'/v2/ugcPosts',method:'POST',
  headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json',
           'X-Restli-Protocol-Version':'2.0.0','Content-Length':Buffer.byteLength(payload)}},Buffer.from(payload));
const urn=(result.json&&result.json.id)||(result.hdr&&result.hdr['x-restli-id'])||'';
const url=urn?('https://www.linkedin.com/feed/update/'+urn):'';
return [{json:{ok:(result.status===201||result.status===200),postId:postId,
  tweet_id:String(urn),tweet_url:url,tweet_text:text.slice(0,120),x_status:result.status,
  li_err:(result.json&&result.json.message)||null,media_assets:assets,media_errors:merrs}}];`;

async function main() {
  const base = process.env.N8N_BASE_URL, key = process.env.N8N_API_KEY;
  if (!base || !key) { console.log('BRAK N8N_BASE_URL / N8N_API_KEY'); process.exit(1); }
  const H = { 'X-N8N-API-KEY': key, 'Content-Type': 'application/json' };
  const id = 'x1jJEbcWAe3FnpCa';
  const w = await (await fetch(`${base}/api/v1/workflows/${id}`, { headers: H })).json();
  fs.writeFileSync(`${__dirname}/bk_scheduler_libranch_${Date.now()}.json`, JSON.stringify(w));
  if (w.nodes.find(n => n.name === 'Route Platform')) { console.log('JUZ MA galaz LI - nic nie robie'); return; }

  const keys = w.nodes.find(n => n.name === 'Get Keys');
  if (keys.parameters.query.indexOf('li_token') === -1) {
    keys.parameters.query = keys.parameters.query.replace(
      " FROM app_secrets;",
      ", max(CASE WHEN key='linkedin_access_token' THEN value END) AS li_token, max(CASE WHEN key='linkedin_author_urn' THEN value END) AS li_author FROM app_secrets;");
    console.log('Get Keys: + li_token/li_author');
  }
  const mark = w.nodes.find(n => n.name === 'Mark Published');
  const pubx = w.nodes.find(n => n.name === 'Publish To X');
  const conf = w.nodes.find(n => n.name === 'Scheduler Confirm');

  // IF wg AP-301: ksztalt warunkow skopiowany z dzialajacego if 2.2 (HITL 'Is Cm Callback?')
  const routeNode = {
    parameters: { conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose', version: 2 },
                                conditions: [{ id: 'rp1', leftValue: '={{ $json.platform }}', rightValue: 'x',
                                               operator: { type: 'string', operation: 'equals' } }],
                                combinator: 'and' }, options: {} },
    id: 'routeplat1', name: 'Route Platform', type: 'n8n-nodes-base.if', typeVersion: 2.2,
    position: [pubx.position[0] - 200, pubx.position[1] + 60] };
  const liNode = { parameters: { jsCode: LI_CODE }, id: 'lipub1', name: 'Publish To LinkedIn (Scheduler)',
    type: 'n8n-nodes-base.code', typeVersion: 2, position: [pubx.position[0], pubx.position[1] + 220] };
  const markLi = { parameters: { operation: 'executeQuery', query: mark.parameters.query, options: {} },
    id: 'limark1', name: 'Mark Published LI', type: 'n8n-nodes-base.postgres', typeVersion: mark.typeVersion,
    position: [mark.position[0], mark.position[1] + 220], credentials: mark.credentials };
  const confLi = { parameters: { method: 'POST',
      url: "=https://api.telegram.org/bot{{ $('Get Keys').first().json.tg }}/sendMessage",
      sendBody: true, specifyBody: 'json',
      jsonBody: "={{ JSON.stringify({ chat_id: 2106351328, text: ($('Publish To LinkedIn (Scheduler)').item.json.ok ? '\\u2705 Opublikowano zaplanowany post LinkedIn:\\n' + $('Publish To LinkedIn (Scheduler)').item.json.tweet_url : '\\u26a0\\ufe0f Nie udalo sie opublikowac posta LinkedIn (status ' + $('Publish To LinkedIn (Scheduler)').item.json.x_status + ': ' + ($('Publish To LinkedIn (Scheduler)').item.json.li_err || 'brak szczegolow') + ')') }) }}",
      options: { response: { response: { neverError: true } }, timeout: 10000 } },
    id: 'liconf1', name: 'LI Confirm', type: 'n8n-nodes-base.httpRequest', typeVersion: conf.typeVersion,
    position: [conf.position[0], conf.position[1] + 220] };

  w.nodes.push(routeNode, liNode, markLi, confLi);
  w.connections['Fetch Due'] = { main: [[{ node: 'Route Platform', type: 'main', index: 0 }]] };
  w.connections['Route Platform'] = { main: [
    [{ node: 'Publish To X', type: 'main', index: 0 }],
    [{ node: 'Publish To LinkedIn (Scheduler)', type: 'main', index: 0 }]] };
  w.connections['Publish To LinkedIn (Scheduler)'] = { main: [[{ node: 'Mark Published LI', type: 'main', index: 0 }]] };
  w.connections['Mark Published LI'] = { main: [[{ node: 'LI Confirm', type: 'main', index: 0 }]] };

  const settings = {};
  for (const k of ALLOWED) if (w.settings && w.settings[k] !== undefined) settings[k] = w.settings[k];
  const put = await fetch(`${base}/api/v1/workflows/${id}`, { method: 'PUT', headers: H,
    body: JSON.stringify({ name: w.name, nodes: w.nodes, connections: w.connections, settings }) });
  console.log('PUT:', put.status);
  if (put.status !== 200) { console.log(await put.text()); process.exit(1); }
  const d = await fetch(`${base}/api/v1/workflows/${id}/deactivate`, { method: 'POST', headers: H });
  const a = await fetch(`${base}/api/v1/workflows/${id}/activate`, { method: 'POST', headers: H });
  console.log('deactivate:', d.status, 'activate:', a.status);
  const v = await (await fetch(`${base}/api/v1/workflows/${id}`, { headers: H })).json();
  console.log('verify: active:', v.active, '| nodes:', v.nodes.length,
    '| route:', !!v.nodes.find(n => n.name === 'Route Platform'),
    '| lipub:', !!v.nodes.find(n => n.name === 'Publish To LinkedIn (Scheduler)'),
    '| keys li:', v.nodes.find(n => n.name === 'Get Keys').parameters.query.includes('li_token'));
}
main().catch(e => { console.error(e.message); process.exit(1); });
