const http = require('http');

const PORT = 5000;
const HOST = '0.0.0.0';

const server = http.createServer((req, res) => {
  res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  res.setHeader('Content-Type', 'text/html');
  res.writeHead(200);
  res.end(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PixelRoot</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }
    .container {
      text-align: center;
      padding: 2rem;
      max-width: 800px;
    }
    h1 {
      font-size: 3rem;
      margin-bottom: 1rem;
      background: linear-gradient(90deg, #00d4ff, #7c3aed);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .subtitle {
      font-size: 1.2rem;
      color: #94a3b8;
      margin-bottom: 2rem;
      line-height: 1.6;
    }
    .features {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1.5rem;
      margin-top: 2rem;
    }
    .feature {
      background: rgba(255,255,255,0.05);
      padding: 1.5rem;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .feature h3 {
      color: #00d4ff;
      margin-bottom: 0.5rem;
    }
    .feature p {
      color: #94a3b8;
      font-size: 0.9rem;
    }
    .status {
      margin-top: 2rem;
      padding: 1rem;
      background: rgba(124, 58, 237, 0.2);
      border-radius: 8px;
      border: 1px solid rgba(124, 58, 237, 0.3);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>PixelRoot</h1>
    <p class="subtitle">
      A hardware-anchored media authenticity framework that embeds cryptographic provenance 
      directly into image pixels at the moment of capture.
    </p>
    <div class="features">
      <div class="feature">
        <h3>CMOS Integration</h3>
        <p>Sensor-level pixel modulation for authentic capture</p>
      </div>
      <div class="feature">
        <h3>Blockchain Logging</h3>
        <p>Real-time tamper-evident verification</p>
      </div>
      <div class="feature">
        <h3>No Metadata</h3>
        <p>Provenance embedded in pixels, not mutable metadata</p>
      </div>
    </div>
    <div class="status">
      <p>Project documentation imported. Ready for implementation.</p>
    </div>
  </div>
</body>
</html>`);
});

server.listen(PORT, HOST, () => {
  console.log('PixelRoot server running at http://' + HOST + ':' + PORT);
});
