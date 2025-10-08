const { spawn } = require('child_process');

console.log('🚀 Starting Flask backend...');

// Start Flask backend
const backend = spawn('python', ['../simple_api.py'], {
  cwd: __dirname,
  stdio: 'pipe'
});

backend.stdout.on('data', (data) => {
  console.log(`Backend: ${data}`);
});

backend.stderr.on('data', (data) => {
  console.error(`Backend Error: ${data}`);
});

// Wait a moment then start React
setTimeout(() => {
  console.log('🚀 Starting React frontend...');
  const frontend = spawn('npm', ['start'], {
    cwd: __dirname,
    stdio: 'inherit',
    shell: true
  });
}, 2000);