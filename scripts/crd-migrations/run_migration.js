// AGS CRD Migration Runner - Node.js ssh2
// Transfers SQL and runs it against pg_n8n container
'use strict';
const { Client } = require('C:\\Users\\Admin\\AppData\\Local\\Temp\\node_modules\\ssh2');
const fs = require('fs');

const SSH_CONFIG = {
  host: 'ivy147.mikrus.xyz',
  port: 10147,
  username: 'root',
  password: 'WknpiM1980!',
  tryKeyboard: true,
  readyTimeout: 20000
};

const SQL_FILE = 'C:\\Users\\Admin\\AppData\\Local\\Temp\\ags_migration.sql';

function makeConn() {
  const conn = new Client();
  conn.on('keyboard-interactive', (n, i, l, p, finish) => finish(['WknpiM1980!']));
  conn.on('error', err => { console.error('CONN_ERR:', err.message); });
  return conn;
}

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => resolve({ code, stdout, stderr }));
    });
  });
}

function sshExecWithStdin(conn, cmd, stdinData) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => resolve({ code, stdout, stderr }));
      stream.write(stdinData);
      stream.end();
    });
  });
}

async function runMigration() {
  const sqlContent = fs.readFileSync(SQL_FILE, 'utf8');
  const results = {};

  // Step 1: Write file to remote
  {
    const conn = makeConn();
    await new Promise((res, rej) => conn.on('ready', res).on('error', rej).connect(SSH_CONFIG));
    console.log('Connected - writing SQL to remote /tmp...');
    const r = await sshExecWithStdin(conn, 'cat > /tmp/ags_migration.sql', sqlContent);
    console.log('File write exit:', r.code, r.stderr || '');
    results.fileWriteCode = r.code;
    conn.end();
  }

  await new Promise(r => setTimeout(r, 500));

  // Step 2: Run migration
  {
    const conn = makeConn();
    await new Promise((res, rej) => conn.on('ready', res).on('error', rej).connect(SSH_CONFIG));
    console.log('Running migration...');
    const r = await sshExec(conn, 'docker exec -i pg_n8n psql -U ags_crd_user -d ags_crd -f /tmp/ags_migration.sql');
    console.log('Migration exit:', r.code);
    console.log('STDOUT:', r.stdout);
    if (r.stderr) console.log('STDERR:', r.stderr);
    results.migrationCode = r.code;
    results.migrationOutput = r.stdout;
    results.migrationStderr = r.stderr;
    conn.end();
  }

  await new Promise(r => setTimeout(r, 500));

  // Step 3: Verify tables
  {
    const conn = makeConn();
    await new Promise((res, rej) => conn.on('ready', res).on('error', rej).connect(SSH_CONFIG));
    const r = await sshExec(conn, "docker exec pg_n8n psql -U ags_crd_user -d ags_crd -c \"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;\"");
    console.log('Tables after:', r.stdout);
    results.tablesAfter = r.stdout;
    conn.end();
  }

  await new Promise(r => setTimeout(r, 500));

  // Step 4: Verify indexes
  {
    const conn = makeConn();
    await new Promise((res, rej) => conn.on('ready', res).on('error', rej).connect(SSH_CONFIG));
    const r = await sshExec(conn, "docker exec pg_n8n psql -U ags_crd_user -d ags_crd -c \"SELECT indexname FROM pg_indexes WHERE schemaname='public' ORDER BY indexname;\"");
    console.log('Indexes:', r.stdout);
    results.indexes = r.stdout;
    conn.end();
  }

  await new Promise(r => setTimeout(r, 500));

  // Step 5: Row counts
  {
    const conn = makeConn();
    await new Promise((res, rej) => conn.on('ready', res).on('error', rej).connect(SSH_CONFIG));
    const r = await sshExec(conn, "docker exec pg_n8n psql -U ags_crd_user -d ags_crd -c \"SELECT 'contacts' as tbl, COUNT(*) FROM contacts UNION ALL SELECT 'engagement_log', COUNT(*) FROM engagement_log UNION ALL SELECT 'hitl_sessions', COUNT(*) FROM hitl_sessions;\"");
    console.log('Row counts:', r.stdout);
    results.rowCounts = r.stdout;
    conn.end();
  }

  await new Promise(r => setTimeout(r, 500));

  // Step 6: Table sizes
  {
    const conn = makeConn();
    await new Promise((res, rej) => conn.on('ready', res).on('error', rej).connect(SSH_CONFIG));
    const r = await sshExec(conn, "docker exec pg_n8n psql -U ags_crd_user -d ags_crd -c \"SELECT table_name, pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;\"");
    console.log('Table sizes:', r.stdout);
    results.tableSizes = r.stdout;
    conn.end();
  }

  console.log('RESULTS_JSON:', JSON.stringify(results));
}

runMigration().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
