import React, { startTransition, useEffect, useState } from 'react';
import {
  ArrowRight,
  CheckCircle,
  Clock,
  Copy,
  Cpu,
  Database,
  Hash,
  Image,
  Link,
  MapPin,
  Menu,
  RefreshCcw,
  Shield,
  Upload,
  X,
  XCircle,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview' },
  { id: 'register', label: 'Register' },
  { id: 'verify', label: 'Verify' },
  { id: 'registry', label: 'Registry' },
];

const FEATURE_PILLARS = [
  {
    title: 'Capture-bound provenance',
    description:
      'Every registry entry binds image bytes to device identity, capture time, and location state before it enters the feed.',
    icon: Cpu,
  },
  {
    title: 'Verification-first API',
    description:
      'The backend now exposes health, registry, and verification endpoints with explicit storage and algorithm metadata.',
    icon: Shield,
  },
  {
    title: 'Operator visibility',
    description:
      'The interface shows live registry counts, storage mode, and signature version so operators can trust the system state.',
    icon: Database,
  },
  {
    title: 'Ledger transparency',
    description:
      'This build clearly marks blockchain receipts as simulated until a real chain integration is connected.',
    icon: Link,
  },
];

const PIPELINE_STEPS = [
  'Capture or upload an image to create a provenance record.',
  'PixelRoot derives a deterministic signature from device, time, and location context.',
  'The registry stores the image fingerprint, signature preview, and ledger receipt.',
  'Verification recomputes the fingerprint and confirms whether the bytes still match the registry.',
];

const INITIAL_HEALTH = {
  status: 'loading',
  storage: { mode: 'file', ready: false },
  algorithm: { version: 'v2', metadataBits: 128, coordinateEncoding: '24-bit-per-coordinate' },
  uploadLimitBytes: 10 * 1024 * 1024,
};

function shortHash(value, head = 12, tail = 10) {
  if (!value) {
    return 'Unavailable';
  }

  if (value.length <= head + tail + 3) {
    return value;
  }

  return `${value.slice(0, head)}...${value.slice(-tail)}`;
}

function formatDateTime(value) {
  if (!value) {
    return 'Unavailable';
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes)) {
    return 'Unknown size';
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatStorageMode(mode) {
  if (mode === 'postgres') {
    return 'PostgreSQL';
  }

  return 'Local file store';
}

function formatLocation(location) {
  if (!location) {
    return 'Unavailable';
  }

  if (location.source !== 'device') {
    return 'Unavailable at capture. Neutral origin was used for the demo signature.';
  }

  return `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`;
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, options);
  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    throw new Error(payload?.error || `Request failed with status ${response.status}`);
  }

  return payload;
}

function requestGeolocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }

    let settled = false;
    const timeoutId = window.setTimeout(() => {
      if (!settled) {
        settled = true;
        resolve(null);
      }
    }, 4000);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (!settled) {
          settled = true;
          window.clearTimeout(timeoutId);
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        }
      },
      () => {
        if (!settled) {
          settled = true;
          window.clearTimeout(timeoutId);
          resolve(null);
        }
      },
      {
        enableHighAccuracy: false,
        maximumAge: 60000,
        timeout: 3000,
      }
    );
  });
}

function createDraft(file) {
  return {
    file,
    name: file.name,
    size: file.size,
    previewUrl: URL.createObjectURL(file),
  };
}

function buildSignaturePreview(signaturePreview) {
  const totalCells = 64;
  const highlighted = new Set(
    signaturePreview.map((item) => ((item.row % 8) * 8) + (item.col % 8))
  );

  return Array.from({ length: totalCells }, (_, index) => highlighted.has(index));
}

function CopyButton({ value, label, onCopy }) {
  return (
    <button className="ghost-button" type="button" onClick={() => onCopy(value, label)}>
      <Copy size={14} />
      Copy
    </button>
  );
}

function SectionHeader({ eyebrow, title, description, action }) {
  return (
    <div className="section-header">
      <div>
        {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {action || null}
    </div>
  );
}

function MetricCard({ label, value, caption }) {
  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      <span className="metric-caption">{caption}</span>
    </div>
  );
}

function FeatureCard({ feature }) {
  const Icon = feature.icon;

  return (
    <article className="feature-card">
      <div className="feature-icon">
        <Icon size={20} />
      </div>
      <h3>{feature.title}</h3>
      <p>{feature.description}</p>
    </article>
  );
}

function StatusBadge({ healthy, label }) {
  return (
    <span className={`status-badge ${healthy ? 'ok' : 'warn'}`}>
      <span className="status-dot" />
      {label}
    </span>
  );
}

function FileDropzone({
  id,
  title,
  description,
  hint,
  busy,
  draft,
  actionLabel,
  onSelectFile,
}) {
  const [dragActive, setDragActive] = useState(false);

  function pickFile(fileList) {
    const file = fileList?.[0];
    if (!file || !file.type.startsWith('image/')) {
      return;
    }
    onSelectFile(file);
  }

  return (
    <div className="panel upload-panel">
      <div className="panel-header">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>

      <label
        className={`dropzone ${dragActive ? 'drag-active' : ''} ${busy ? 'busy' : ''}`}
        htmlFor={id}
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragActive(false);
          pickFile(event.dataTransfer.files);
        }}
      >
        <input
          id={id}
          type="file"
          accept="image/*"
          onChange={(event) => {
            pickFile(event.target.files);
            event.target.value = '';
          }}
        />
        <div className="dropzone-icon">
          <Upload size={24} />
        </div>
        <strong>{actionLabel}</strong>
        <span>{hint}</span>
      </label>

      {draft ? (
        <div className="draft-preview">
          <img className="draft-image" src={draft.previewUrl} alt={draft.name} />
          <div className="draft-meta">
            <strong>{draft.name}</strong>
            <span>{formatFileSize(draft.size)}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function DetailList({ rows, onCopy }) {
  return (
    <div className="detail-list">
      {rows.map((row) => (
        <div className="detail-row" key={row.label}>
          <div>
            <span className="detail-label">{row.label}</span>
            <strong className="detail-value">{row.value}</strong>
          </div>
          {row.copyValue ? (
            <CopyButton value={row.copyValue} label={row.label} onCopy={onCopy} />
          ) : null}
        </div>
      ))}
    </div>
  );
}

function SignaturePreview({ signaturePreview }) {
  const cells = buildSignaturePreview(signaturePreview);

  return (
    <div className="signature-panel">
      <div className="signature-header">
        <strong>Signature preview</strong>
        <span>First 16 embedded coordinates projected into an 8x8 visual grid.</span>
      </div>
      <div className="signature-grid">
        {cells.map((active, index) => (
          <div
            key={index}
            className={`signature-cell ${active ? 'active' : ''}`}
          />
        ))}
      </div>
    </div>
  );
}

function OperationResult({ mode, result, onCopy }) {
  if (!result) {
    return null;
  }

  if (result.error) {
    return (
      <div className="panel result-panel error">
        <div className="result-heading">
          <XCircle size={20} />
          <div>
            <h3>{mode === 'register' ? 'Registration failed' : 'Verification failed'}</h3>
            <p>{result.error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'verify' && result.verified === false) {
    return (
      <div className="panel result-panel warning">
        <div className="result-heading">
          <XCircle size={20} />
          <div>
            <h3>Image not verified</h3>
            <p>{result.message}</p>
          </div>
        </div>
      </div>
    );
  }

  const record = result.data;
  const rows = [
    {
      label: 'Image hash',
      value: shortHash(record.imageHash, 18, 14),
      copyValue: record.imageHash,
    },
    {
      label: 'Algorithm version',
      value: record.algorithmVersion.toUpperCase(),
    },
    {
      label: 'Ledger receipt',
      value: shortHash(record.blockchainTx, 14, 12),
      copyValue: record.blockchainTx,
    },
    {
      label: 'Captured at',
      value: formatDateTime(record.timestamp),
    },
    {
      label: 'Location state',
      value: formatLocation(record.location),
    },
    {
      label: 'Storage mode',
      value: formatStorageMode(result.storageMode || 'file'),
    },
  ];

  if (mode === 'verify') {
    rows.push({
      label: 'Registered at',
      value: formatDateTime(record.createdAt),
    });
  }

  return (
    <div className="panel result-panel success">
      <div className="result-heading">
        <CheckCircle size={20} />
        <div>
          <h3>{mode === 'register' ? 'Provenance record created' : 'Image verified against registry'}</h3>
          <p>
            {mode === 'register'
              ? 'The registry stored a fresh provenance record and generated a simulated ledger receipt.'
              : 'The uploaded bytes matched an existing registry record.'}
          </p>
        </div>
      </div>
      <DetailList rows={rows} onCopy={onCopy} />
      <SignaturePreview signaturePreview={record.pixelSignaturePreview} />
    </div>
  );
}

function RegistryCard({ image, onCopy }) {
  return (
    <article className="registry-card">
      <div className="registry-image-shell">
        <img
          className="registry-image"
          src={image.fileUrl}
          alt={image.originalFilename}
          onError={(event) => {
            event.currentTarget.style.visibility = 'hidden';
          }}
        />
        <StatusBadge healthy={image.verified} label={image.verified ? 'Verified record' : 'Pending'} />
      </div>
      <div className="registry-body">
        <div className="registry-row">
          <strong>{image.originalFilename}</strong>
          <CopyButton value={image.imageHash} label="Image hash" onCopy={onCopy} />
        </div>
        <p className="registry-hash">{shortHash(image.imageHash, 14, 12)}</p>
        <div className="registry-meta">
          <span>
            <Clock size={14} />
            {formatDateTime(image.createdAt)}
          </span>
          <span>
            <Hash size={14} />
            {image.algorithmVersion.toUpperCase()}
          </span>
        </div>
        <div className="registry-meta">
          <span>
            <MapPin size={14} />
            {formatLocation(image.location)}
          </span>
        </div>
      </div>
    </article>
  );
}

function App() {
  const [activeView, setActiveView] = useState('overview');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [health, setHealth] = useState(INITIAL_HEALTH);
  const [stats, setStats] = useState({
    totalImages: 0,
    totalVerifications: 0,
    storageMode: 'file',
  });
  const [images, setImages] = useState([]);
  const [pageError, setPageError] = useState('');
  const [copiedLabel, setCopiedLabel] = useState('');
  const [isBooting, setIsBooting] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [busyAction, setBusyAction] = useState('');
  const [registerDraft, setRegisterDraft] = useState(null);
  const [verifyDraft, setVerifyDraft] = useState(null);
  const [registerResult, setRegisterResult] = useState(null);
  const [verifyResult, setVerifyResult] = useState(null);

  useEffect(() => {
    loadOperationalData({ boot: true });
  }, []);

  useEffect(() => () => {
    if (registerDraft?.previewUrl) {
      URL.revokeObjectURL(registerDraft.previewUrl);
    }

    if (verifyDraft?.previewUrl) {
      URL.revokeObjectURL(verifyDraft.previewUrl);
    }
  }, [registerDraft, verifyDraft]);

  async function loadOperationalData({ boot = false } = {}) {
    setPageError('');

    if (boot) {
      setIsBooting(true);
    } else {
      setIsRefreshing(true);
    }

    try {
      const [healthPayload, statsPayload, imagesPayload] = await Promise.all([
        apiRequest('/api/health'),
        apiRequest('/api/stats'),
        apiRequest('/api/images'),
      ]);

      startTransition(() => {
        setHealth(healthPayload);
        setStats(statsPayload);
        setImages(imagesPayload);
      });
    } catch (error) {
      setPageError(error.message);
    } finally {
      if (boot) {
        setIsBooting(false);
      } else {
        setIsRefreshing(false);
      }
    }
  }

  function replaceDraft(setter, currentDraft, file) {
    if (currentDraft?.previewUrl) {
      URL.revokeObjectURL(currentDraft.previewUrl);
    }

    setter(createDraft(file));
  }

  async function handleRegister(file) {
    replaceDraft(setRegisterDraft, registerDraft, file);
    setRegisterResult(null);
    setBusyAction('register');

    try {
      const formData = new FormData();
      formData.append('image', file);

      const location = await requestGeolocation();
      if (location) {
        formData.append('latitude', `${location.latitude}`);
        formData.append('longitude', `${location.longitude}`);
      }

      const payload = await apiRequest('/api/register', {
        method: 'POST',
        body: formData,
      });

      setRegisterResult({
        ...payload,
        storageMode: stats.storageMode,
      });
      await loadOperationalData();
      setActiveView('register');
    } catch (error) {
      setRegisterResult({ error: error.message });
    } finally {
      setBusyAction('');
    }
  }

  async function handleVerify(file) {
    replaceDraft(setVerifyDraft, verifyDraft, file);
    setVerifyResult(null);
    setBusyAction('verify');

    try {
      const formData = new FormData();
      formData.append('image', file);

      const payload = await apiRequest('/api/verify', {
        method: 'POST',
        body: formData,
      });

      setVerifyResult({
        ...payload,
        storageMode: stats.storageMode,
      });
      await loadOperationalData();
      setActiveView('verify');
    } catch (error) {
      setVerifyResult({ error: error.message });
    } finally {
      setBusyAction('');
    }
  }

  async function copyValue(value, label) {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedLabel(`${label} copied`);
      window.setTimeout(() => setCopiedLabel(''), 1500);
    } catch (error) {
      setCopiedLabel(`Clipboard unavailable for ${label.toLowerCase()}`);
      window.setTimeout(() => setCopiedLabel(''), 1800);
    }
  }

  function renderOverview() {
    return (
      <>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">Operational provenance console</div>
            <h1>Professional image authenticity workflow for capture, registry, and verification.</h1>
            <p>
              PixelRoot now runs as a real operator surface: explicit storage health, deterministic
              signature versioning, honest ledger messaging, and a registry that remains usable
              even without a configured database.
            </p>
            <div className="hero-actions">
              <button className="primary-button" type="button" onClick={() => setActiveView('register')}>
                Register image
                <ArrowRight size={16} />
              </button>
              <button className="secondary-button" type="button" onClick={() => setActiveView('verify')}>
                Verify image
              </button>
            </div>
            <div className="hero-trust-row">
              <StatusBadge healthy={health.status === 'ok'} label={health.status === 'ok' ? 'System healthy' : 'Attention needed'} />
              <span>{formatStorageMode(stats.storageMode)}</span>
              <span>{health.algorithm.version.toUpperCase()} signature model</span>
            </div>
          </div>

          <div className="hero-console panel">
            <div className="panel-header">
              <div>
                <h3>System status</h3>
                <p>Live runtime details from the backend health endpoint.</p>
              </div>
              <button className="ghost-button" type="button" onClick={() => loadOperationalData()} disabled={isRefreshing}>
                <RefreshCcw size={14} className={isRefreshing ? 'spinning' : ''} />
                Refresh
              </button>
            </div>

            <div className="status-grid">
              <MetricCard
                label="Registered images"
                value={stats.totalImages}
                caption="All active provenance records"
              />
              <MetricCard
                label="Successful verifications"
                value={stats.totalVerifications}
                caption="Positive registry matches"
              />
              <MetricCard
                label="Storage backend"
                value={formatStorageMode(stats.storageMode)}
                caption={health.storage.dataFile || 'Persistent service storage'}
              />
              <MetricCard
                label="Upload limit"
                value={formatFileSize(health.uploadLimitBytes)}
                caption={health.algorithm.coordinateEncoding}
              />
            </div>
          </div>
        </section>

        <section className="section">
          <SectionHeader
            eyebrow="What changed"
            title="The app now behaves like an operational product, not a static demo."
            description="These improvements address the runtime, data model, and the operator workflow together."
          />
          <div className="feature-grid">
            {FEATURE_PILLARS.map((feature) => (
              <FeatureCard feature={feature} key={feature.title} />
            ))}
          </div>
        </section>

        <section className="section split-layout">
          <div className="panel">
            <SectionHeader
              eyebrow="Verification flow"
              title="Four steps from capture to trust."
              description="The workflow now surfaces what is simulated, what is persisted, and what the operator can verify immediately."
            />
            <div className="timeline">
              {PIPELINE_STEPS.map((step, index) => (
                <div className="timeline-step" key={step}>
                  <div className="timeline-marker">{index + 1}</div>
                  <p>{step}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <SectionHeader
              eyebrow="Registry preview"
              title="Latest records"
              description="Recent provenance entries appear here as soon as the registry updates."
            />
            {images.length === 0 ? (
              <div className="empty-state">
                <Image size={32} />
                <p>No images registered yet. Use the register workflow to create the first provenance record.</p>
              </div>
            ) : (
              <div className="preview-stack">
                {images.slice(0, 3).map((image) => (
                  <RegistryCard image={image} key={image.id} onCopy={copyValue} />
                ))}
              </div>
            )}
          </div>
        </section>
      </>
    );
  }

  function renderRegister() {
    return (
      <section className="section operation-layout">
        <div>
          <SectionHeader
            eyebrow="Register"
            title="Create a new provenance record."
            description="Upload an image and PixelRoot will generate a deterministic registry record using the current signature model."
          />
          <FileDropzone
            id="register-file"
            title="Registration input"
            description="The system will request geolocation when available. If location access is unavailable, the signature falls back to a neutral origin and the UI labels it accordingly."
            hint="JPEG, PNG, GIF, or WebP up to 10 MB"
            actionLabel={busyAction === 'register' ? 'Registering image...' : 'Drop an image here or select a file'}
            busy={busyAction === 'register'}
            draft={registerDraft}
            onSelectFile={handleRegister}
          />
        </div>

        <div className="operation-side">
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Registration outcome</h3>
                <p>The result includes algorithm version, ledger receipt, and a preview of embedded signature coordinates.</p>
              </div>
            </div>
            {busyAction === 'register' ? <div className="busy-banner">Creating provenance record...</div> : null}
            <OperationResult mode="register" result={registerResult} onCopy={copyValue} />
          </div>
        </div>
      </section>
    );
  }

  function renderVerify() {
    return (
      <section className="section operation-layout">
        <div>
          <SectionHeader
            eyebrow="Verify"
            title="Check whether an image matches the registry."
            description="Verification recomputes the fingerprint against every stored record, including legacy v1 hashes if they exist."
          />
          <FileDropzone
            id="verify-file"
            title="Verification input"
            description="Use the original registered image for a positive match. Any byte-level change will cause the verification step to fail."
            hint="Upload the image you want to validate"
            actionLabel={busyAction === 'verify' ? 'Verifying image...' : 'Drop an image here or select a file'}
            busy={busyAction === 'verify'}
            draft={verifyDraft}
            onSelectFile={handleVerify}
          />
        </div>

        <div className="operation-side">
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Verification outcome</h3>
                <p>Positive matches return the original registry metadata and signature preview.</p>
              </div>
            </div>
            {busyAction === 'verify' ? <div className="busy-banner">Running verification...</div> : null}
            <OperationResult mode="verify" result={verifyResult} onCopy={copyValue} />
          </div>
        </div>
      </section>
    );
  }

  function renderRegistry() {
    return (
      <section className="section">
        <SectionHeader
          eyebrow="Registry"
          title="Browse recent provenance records."
          description="The registry view is backed by the same data served to verification, with file-backed persistence when no database is configured."
          action={(
            <button className="ghost-button" type="button" onClick={() => loadOperationalData()} disabled={isRefreshing}>
              <RefreshCcw size={14} className={isRefreshing ? 'spinning' : ''} />
              Refresh
            </button>
          )}
        />

        {images.length === 0 ? (
          <div className="panel empty-state large">
            <Image size={40} />
            <p>The registry is empty. Create a record from the register view to populate it.</p>
          </div>
        ) : (
          <div className="registry-grid">
            {images.map((image) => (
              <RegistryCard image={image} key={image.id} onCopy={copyValue} />
            ))}
          </div>
        )}
      </section>
    );
  }

  return (
    <div className="app-shell">
      <div className="background-orb orb-a" />
      <div className="background-orb orb-b" />

      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">PR</div>
          <div>
            <strong>PixelRoot</strong>
            <span>Image authenticity console</span>
          </div>
        </div>

        <nav className={`nav ${mobileNavOpen ? 'open' : ''}`}>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-link ${activeView === item.id ? 'active' : ''}`}
              type="button"
              onClick={() => {
                setActiveView(item.id);
                setMobileNavOpen(false);
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="topbar-actions">
          {copiedLabel ? <span className="copy-toast">{copiedLabel}</span> : null}
          <button
            className="menu-button"
            type="button"
            onClick={() => setMobileNavOpen((value) => !value)}
            aria-label="Toggle navigation"
          >
            {mobileNavOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </header>

      <main className="main-content">
        {pageError ? (
          <div className="page-banner error">
            <XCircle size={18} />
            <span>{pageError}</span>
          </div>
        ) : null}

        {isBooting ? (
          <section className="boot-panel panel">
            <RefreshCcw size={18} className="spinning" />
            <span>Loading operational state...</span>
          </section>
        ) : null}

        {!isBooting && activeView === 'overview' ? renderOverview() : null}
        {!isBooting && activeView === 'register' ? renderRegister() : null}
        {!isBooting && activeView === 'verify' ? renderVerify() : null}
        {!isBooting && activeView === 'registry' ? renderRegistry() : null}
      </main>

      <footer className="footer">
        <div>
          <strong>PixelRoot</strong>
          <p>Hardware-anchored provenance with professional operator visibility.</p>
        </div>
        <div className="footer-meta">
          <span>{formatStorageMode(stats.storageMode)}</span>
          <span>{health.algorithm.version.toUpperCase()} metadata model</span>
          <span>{health.status === 'ok' ? 'Healthy' : 'Needs attention'}</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
