import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Shield, Database, Cpu, Link, CheckCircle, XCircle, Image, Clock, MapPin, Hash } from 'lucide-react';

function App() {
  const [view, setView] = useState('home');
  const [stats, setStats] = useState({ totalImages: 0, totalVerifications: 0 });
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchImages();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchImages = async () => {
    try {
      const res = await fetch('/api/images');
      const data = await res.json();
      setImages(data);
    } catch (err) {
      console.error('Failed to fetch images:', err);
    }
  };

  const handleRegister = async (file) => {
    setLoading(true);
    setUploadResult(null);
    
    try {
      const formData = new FormData();
      formData.append('image', file);
      
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            formData.append('latitude', pos.coords.latitude);
            formData.append('longitude', pos.coords.longitude);
          },
          () => {}
        );
      }

      const res = await fetch('/api/register', {
        method: 'POST',
        body: formData
      });
      
      const data = await res.json();
      setUploadResult(data);
      fetchStats();
      fetchImages();
    } catch (err) {
      console.error('Registration failed:', err);
      setUploadResult({ error: 'Failed to register image' });
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (file, hash = null) => {
    setLoading(true);
    setVerifyResult(null);
    
    try {
      const formData = new FormData();
      formData.append('image', file);
      if (hash) formData.append('hash', hash);

      const res = await fetch('/api/verify', {
        method: 'POST',
        body: formData
      });
      
      const data = await res.json();
      setVerifyResult(data);
      fetchStats();
    } catch (err) {
      console.error('Verification failed:', err);
      setVerifyResult({ error: 'Failed to verify image' });
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = useCallback((e, action) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      if (action === 'register') handleRegister(file);
      else handleVerify(file);
    }
  }, []);

  const handleFileSelect = (e, action) => {
    const file = e.target.files[0];
    if (file) {
      if (action === 'register') handleRegister(file);
      else handleVerify(file);
    }
  };

  const formatDate = (timestamp) => {
    return new Date(parseInt(timestamp)).toLocaleString();
  };

  const truncateHash = (hash) => {
    if (!hash) return '';
    return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
  };

  return (
    <div className="app">
      <nav>
        <div className="nav-content">
          <div className="logo">PixelRoot</div>
          <div className="nav-links">
            <button className={`nav-link ${view === 'home' ? 'active' : ''}`} onClick={() => setView('home')}>Home</button>
            <button className={`nav-link ${view === 'register' ? 'active' : ''}`} onClick={() => setView('register')}>Register</button>
            <button className={`nav-link ${view === 'verify' ? 'active' : ''}`} onClick={() => setView('verify')}>Verify</button>
            <button className={`nav-link ${view === 'dashboard' ? 'active' : ''}`} onClick={() => setView('dashboard')}>Dashboard</button>
          </div>
        </div>
      </nav>

      {view === 'home' && (
        <>
          <section className="hero">
            <div className="container">
              <h1>PixelRoot</h1>
              <p>
                A hardware-anchored media authenticity framework that embeds cryptographic provenance 
                directly into image pixels at the moment of capture. Combat deepfakes with 
                tamper-evident blockchain verification.
              </p>
              <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                <button className="btn btn-primary" onClick={() => setView('register')}>Register Image</button>
                <button className="btn btn-secondary" onClick={() => setView('verify')}>Verify Image</button>
              </div>
              <div className="hero-stats">
                <div className="stat">
                  <div className="stat-value">{stats.totalImages}</div>
                  <div className="stat-label">Images Registered</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.totalVerifications}</div>
                  <div className="stat-label">Verifications</div>
                </div>
              </div>
            </div>
          </section>

          <section className="features">
            <div className="feature-card">
              <div className="feature-icon">
                <Cpu size={24} color="white" />
              </div>
              <h3>CMOS Integration</h3>
              <p>Sensor-level pixel modulation embeds cryptographic data directly at capture time, making forgery extremely difficult.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <Link size={24} color="white" />
              </div>
              <h3>Blockchain Logging</h3>
              <p>Image hashes are immediately logged to blockchain, creating an immutable record of authentic media.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <Shield size={24} color="white" />
              </div>
              <h3>Hardware Root of Trust</h3>
              <p>MAC address, timestamp, and GPS coordinates are embedded via hardware, not software metadata.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <Database size={24} color="white" />
              </div>
              <h3>Instant Verification</h3>
              <p>Social media platforms can verify image authenticity in seconds without forensic analysis.</p>
            </div>
          </section>

          <section className="section">
            <h2 className="section-title">How It Works</h2>
            <div className="blockchain-viz">
              <div className="blockchain-header">
                <Hash size={24} color="var(--accent-primary)" />
                <h3>PixelRoot Verification Pipeline</h3>
              </div>
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div className="block">
                  <div className="block-number">1</div>
                  <div className="block-info">
                    <div style={{ fontWeight: 600 }}>Capture</div>
                    <div className="block-time">Image captured with embedded pixel signature (MAC + timestamp + GPS)</div>
                  </div>
                </div>
                <div className="chain-link">|</div>
                <div className="block">
                  <div className="block-number">2</div>
                  <div className="block-info">
                    <div style={{ fontWeight: 600 }}>Hash Generation</div>
                    <div className="block-time">SHA-256 hash computed from image data + metadata</div>
                  </div>
                </div>
                <div className="chain-link">|</div>
                <div className="block">
                  <div className="block-number">3</div>
                  <div className="block-info">
                    <div style={{ fontWeight: 600 }}>Blockchain Submit</div>
                    <div className="block-time">Hash logged to blockchain within seconds of capture</div>
                  </div>
                </div>
                <div className="chain-link">|</div>
                <div className="block">
                  <div className="block-number">4</div>
                  <div className="block-info">
                    <div style={{ fontWeight: 600 }}>Verification</div>
                    <div className="block-time">Anyone can verify authenticity via blockchain lookup</div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </>
      )}

      {view === 'register' && (
        <section className="section">
          <h2 className="section-title">Register Image</h2>
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            Upload an image to generate its PixelRoot signature and register it on the blockchain.
          </p>
          
          <label
            className={`upload-zone ${dragOver ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => handleDrop(e, 'register')}
          >
            <input type="file" accept="image/*" onChange={(e) => handleFileSelect(e, 'register')} />
            <div className="upload-icon">
              <Upload size={48} />
            </div>
            <p style={{ marginBottom: '0.5rem' }}>Drag and drop an image or click to select</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Supports JPEG, PNG, GIF, WebP (max 10MB)</p>
          </label>

          {loading && (
            <div className="loading">
              <div className="spinner"></div>
            </div>
          )}

          {uploadResult && uploadResult.success && (
            <div className="result-card">
              <div className="result-header">
                <div className="result-status verified">
                  <CheckCircle size={24} />
                  <span>Image Registered Successfully</span>
                </div>
              </div>
              <div className="result-details">
                <div className="detail-row">
                  <span className="detail-label">Image Hash</span>
                  <span className="detail-value">{uploadResult.data.imageHash}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">MAC Address</span>
                  <span className="detail-value">{uploadResult.data.macAddress}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Timestamp</span>
                  <span className="detail-value">{formatDate(uploadResult.data.timestamp)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Location</span>
                  <span className="detail-value">{uploadResult.data.location.lat.toFixed(6)}, {uploadResult.data.location.lng.toFixed(6)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Blockchain TX</span>
                  <span className="detail-value">{uploadResult.data.blockchainTx}</span>
                </div>
              </div>
              
              <div style={{ marginTop: '1.5rem' }}>
                <h4 style={{ marginBottom: '0.5rem' }}>Pixel Signature Positions (First 10)</h4>
                <div className="pixel-visualization">
                  {Array.from({ length: 120 }, (_, i) => {
                    const isEncoded = i < 10;
                    const hue = isEncoded ? 180 : Math.random() * 360;
                    return (
                      <div
                        key={i}
                        className={`pixel ${isEncoded ? 'encoded' : ''}`}
                        style={{
                          backgroundColor: isEncoded 
                            ? 'var(--accent-primary)' 
                            : `hsl(${hue}, 50%, ${30 + Math.random() * 20}%)`
                        }}
                      />
                    );
                  })}
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                  Highlighted pixels contain embedded cryptographic data (150 total across full image)
                </p>
              </div>
            </div>
          )}

          {uploadResult && uploadResult.error && (
            <div className="result-card">
              <div className="result-status unverified">
                <XCircle size={24} />
                <span>{uploadResult.error}</span>
              </div>
            </div>
          )}
        </section>
      )}

      {view === 'verify' && (
        <section className="section">
          <h2 className="section-title">Verify Image</h2>
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
            Upload an image to check if it has been registered and verify its authenticity.
          </p>
          
          <label
            className={`upload-zone ${dragOver ? 'dragover' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => handleDrop(e, 'verify')}
          >
            <input type="file" accept="image/*" onChange={(e) => handleFileSelect(e, 'verify')} />
            <div className="upload-icon">
              <Shield size={48} />
            </div>
            <p style={{ marginBottom: '0.5rem' }}>Drop an image to verify its authenticity</p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>We'll check if this image is registered on the blockchain</p>
          </label>

          {loading && (
            <div className="loading">
              <div className="spinner"></div>
            </div>
          )}

          {verifyResult && (
            <div className="result-card">
              <div className="result-header">
                <div className={`result-status ${verifyResult.verified ? 'verified' : 'unverified'}`}>
                  {verifyResult.verified ? <CheckCircle size={24} /> : <XCircle size={24} />}
                  <span>{verifyResult.verified ? 'Verified Authentic' : 'Not Verified'}</span>
                </div>
              </div>
              
              {verifyResult.verified ? (
                <div className="result-details">
                  <div className="detail-row">
                    <span className="detail-label">Image Hash</span>
                    <span className="detail-value">{verifyResult.data.imageHash}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Device MAC</span>
                    <span className="detail-value">{verifyResult.data.macAddress}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Captured At</span>
                    <span className="detail-value">{formatDate(verifyResult.data.timestamp)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Location</span>
                    <span className="detail-value">{verifyResult.data.location.lat.toFixed(6)}, {verifyResult.data.location.lng.toFixed(6)}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Blockchain TX</span>
                    <span className="detail-value">{verifyResult.data.blockchainTx}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Registered</span>
                    <span className="detail-value">{new Date(verifyResult.data.registeredAt).toLocaleString()}</span>
                  </div>
                </div>
              ) : (
                <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>
                  This image was not found in our registry. It may not have been registered with PixelRoot, 
                  or it may have been altered since registration.
                </p>
              )}
            </div>
          )}
        </section>
      )}

      {view === 'dashboard' && (
        <section className="section">
          <h2 className="section-title">Registered Images</h2>
          
          <div className="hero-stats" style={{ marginBottom: '2rem' }}>
            <div className="stat">
              <div className="stat-value">{stats.totalImages}</div>
              <div className="stat-label">Total Registered</div>
            </div>
            <div className="stat">
              <div className="stat-value">{stats.totalVerifications}</div>
              <div className="stat-label">Total Verifications</div>
            </div>
          </div>

          {images.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              <Image size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <p>No images registered yet. Be the first to register an image!</p>
              <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => setView('register')}>
                Register Image
              </button>
            </div>
          ) : (
            <div className="image-grid">
              {images.map((img) => (
                <div key={img.id} className="image-card">
                  <img 
                    src={`/uploads/${img.file_path}`} 
                    alt={img.original_filename}
                    className="image-preview"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                  <div className="image-info">
                    <div className="image-hash">{truncateHash(img.image_hash)}</div>
                    <div className="image-meta">
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={12} />
                        {formatDate(img.timestamp)}
                      </span>
                      <span className="verified-badge">
                        <CheckCircle size={12} />
                        Verified
                      </span>
                    </div>
                    <div className="image-meta" style={{ marginTop: '0.5rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <MapPin size={12} />
                        {parseFloat(img.latitude).toFixed(2)}, {parseFloat(img.longitude).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <footer>
        <p>PixelRoot - Hardware-Anchored Media Authenticity Framework</p>
        <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>Combating deepfakes with cryptographic provenance</p>
      </footer>
    </div>
  );
}

export default App;
