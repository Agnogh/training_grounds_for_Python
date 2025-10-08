// ===================================================
// Total.js start script
// https://www.totaljs.com
// ===================================================

const options = {};

// options.ip = '127.0.0.1';
options.port = parseInt(process.env.PORT);
// options.unixsocket = require('path').join(require('os').tmpdir(), 'app_name');
// options.config = { name: 'Total.js' };
// options.sleep = 3000;
// options.inspector = 9229;
// options.watch = ['private'];
// options.livereload = 'https://yourhostname';

// Enables cluster:
// options.cluster = 'auto';
// options.cluster_limit = 10; // max 10. threads (works only with "auto" scaling)

// Enables threads:
// options.cluster = 'auto';
// options.cluster_limit = 10; // max 10. threads (works only with "auto" scaling)
// options.timeout = 5000;
// options.threads = '/api/';
// options.logs = 'isolated';

var type = process.argv.indexOf('--release', 1) !== -1 || process.argv.indexOf('release', 1) !== -1 ? 'release' : 'debug';
// require('total4/' + type)(options);
require('total4').http('release', options);

// this better works or I am pulling out from Code institute !

// to start Python child proces
const { spawn } = require('child_process');

// Use python3 on Linux/Heroku, python on Windows (so I am covered). Allow override via env.
const PY = process.env.PYTHON_EXE || (process.platform === 'win32' ? 'python' : 'python3');

// Run *run.py* (I need to change this to switch from python_battlegrounds.py to run.py)
const SCRIPT = 'run.py';

// -u = unbuffered stdout so logs appear immediately
const py = spawn(PY, ['-u', SCRIPT], { stdio: 'inherit', env: process.env });

py.on('close', (code) => {
  console.log(`[PY] exited with code ${code}`);
});