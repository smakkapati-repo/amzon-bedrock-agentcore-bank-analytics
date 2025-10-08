const { spawn } = require('child_process');
const path = require('path');

// Start React development server
const reactProcess = spawn('npm', ['start'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: true
});

reactProcess.on('error', (err) => {
  console.error('Failed to start React app:', err);
  process.exit(1);
});

reactProcess.on('close', (code) => {
  console.log(`React app exited with code ${code}`);
  process.exit(code);
});

// Handle process termination
process.on('SIGINT', () => {
  reactProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  reactProcess.kill('SIGTERM');
});