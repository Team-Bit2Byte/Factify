import express from 'express';
import multer from 'multer';
import cors from 'cors';
import { spawn, spawnSync } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import fsSync from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '..', '..');

const app = express();
const PORT = process.env.PORT || 3001;
const DEFAULT_OCR_ENGINE = process.env.OCR_ENGINE || (process.platform === 'darwin' ? (hasTesseractBinary() ? 'tesseract' : 'easyocr') : 'auto');
const DEFAULT_OCR_MODE = process.env.OCR_MODE || 'ocr';
const distDir = path.join(projectRoot, 'dist');
const hasBuiltFrontend = fsSync.existsSync(distDir);

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(projectRoot, 'uploads');
    try {
      await fs.mkdir(uploadDir, { recursive: true });
      cb(null, uploadDir);
    } catch (error) {
      cb(error, null);
    }
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    // Use basename to strip any directory components from original filename
    const sanitizedExt = path.extname(path.basename(file.originalname));
    cb(null, file.fieldname + '-' + uniqueSuffix + sanitizedExt);
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|webp|avif/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Only image files are allowed (JPEG, PNG, WEBP, AVIF)'));
    }
  }
});

// Middleware
const explicitAllowedOrigins = process.env.CORS_ORIGINS
  ? process.env.CORS_ORIGINS.split(',').map((origin) => origin.trim()).filter(Boolean)
  : [];

function isLocalDevOrigin(origin) {
  try {
    const parsed = new URL(origin);
    return ['localhost', '127.0.0.1', '0.0.0.0', '[::1]', '::1'].includes(parsed.hostname);
  } catch {
    return false;
  }
}

function isAllowedOrigin(origin) {
  if (!origin || origin === 'null') {
    return true;
  }

  if (explicitAllowedOrigins.includes(origin)) {
    return true;
  }

  if (isLocalDevOrigin(origin)) {
    return true;
  }

  if (hasBuiltFrontend) {
    try {
      const parsed = new URL(origin);
      return ['localhost', '127.0.0.1', '0.0.0.0', '[::1]', '::1'].includes(parsed.hostname);
    } catch {
      return false;
    }
  }

  return false;
}

app.use(cors({
  origin: (origin, callback) => {
    if (isAllowedOrigin(origin)) {
      callback(null, true);
    } else {
      callback(null, false);
    }
  },
  credentials: true
}));

app.use(express.json({ limit: '1mb' })); // Limit JSON payload size

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Factify API server is running' });
});

function shouldUseAlgorithms(rawValue) {
  if (typeof rawValue === 'boolean') {
    return rawValue;
  }
  if (typeof rawValue === 'string') {
    return !['false', '0', 'off', 'no'].includes(rawValue.trim().toLowerCase());
  }
  return true;
}

app.post('/api/analyze-url', async (req, res) => {
  const normalizedUrl = normalizeHttpUrl(req.body?.url);
  const useAlgorithms = shouldUseAlgorithms(req.body?.useAlgorithms);

  if (!normalizedUrl) {
    return res.status(400).json({ error: 'A valid http(s) URL is required' });
  }

  // Validate URL length to prevent DoS
  if (normalizedUrl.length > 2048) {
    return res.status(400).json({ error: 'URL too long (max 2048 characters)' });
  }

  const pythonScript = path.join(projectRoot, 'src', 'ml', 'scraper', 'text_scraper.py');
  console.log(`[API] Scraping URL: ${normalizedUrl}`);

  try {
    const result = await runPythonCommand(
      [
        pythonScript,
        '--url', normalizedUrl,
        '--format', 'json',
        ...(useAlgorithms ? [] : ['--disable-algorithms']),
      ],
      req
    );

    console.log(`[API] URL scrape complete: ${normalizedUrl}`);
    res.json({
      success: true,
      url: normalizedUrl,
      result,
    });
  } catch (error) {
    console.error('[API] Error scraping URL:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to scrape URL',
    });
  }
});

app.post('/api/analyze-text', async (req, res) => {
  const submittedText = typeof req.body?.text === 'string' ? req.body.text.trim() : '';
  const useAlgorithms = shouldUseAlgorithms(req.body?.useAlgorithms);

  if (!submittedText) {
    return res.status(400).json({ error: 'Text content is required' });
  }

  // Validate text length to prevent DoS (max 100KB)
  if (submittedText.length > 100000) {
    return res.status(413).json({ error: 'Text too large (max 100,000 characters)' });
  }

  const pythonScript = path.join(projectRoot, 'src', 'ml', 'text', 'analyze_text.py');

  try {
    const result = await runPythonCommand(
      [
        pythonScript,
        '--text', submittedText,
        '--format', 'json',
        ...(useAlgorithms ? [] : ['--disable-algorithms']),
      ],
      req
    );

    res.json({
      success: true,
      result,
    });
  } catch (error) {
    console.error('[API] Error analyzing text:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to analyze text',
    });
  }
});

// Image analysis endpoint
app.post('/api/analyze-image', upload.single('image'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No image file uploaded' });
  }

  const imagePath = req.file.path;
  const pythonScript = path.join(projectRoot, 'src', 'ml', 'ocr', 'test_image_to_text.py');

  console.log(`[API] Processing image: ${req.file.originalname}`);
  console.log(`[API] File path: ${imagePath}`);

  try {
    // Call Python script with JSON output
    const result = await runImageScript(pythonScript, imagePath, req);
    
    // Clean up uploaded file
    await fs.unlink(imagePath).catch(err => 
      console.warn(`[API] Could not delete temp file: ${err.message}`)
    );

    console.log(`[API] Analysis complete for: ${req.file.originalname}`);
    res.json({
      success: true,
      filename: req.file.originalname,
      result: result
    });

  } catch (error) {
    console.error(`[API] Error processing image:`, error);
    
    // Clean up uploaded file on error
    await fs.unlink(imagePath).catch(() => {});
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process image'
    });
  }
});

// Function to run Python script and capture output
function normalizeHttpUrl(rawUrl) {
  if (typeof rawUrl !== 'string' || !rawUrl.trim()) {
    return null;
  }

  // Validate URL length before parsing
  if (rawUrl.length > 2048) {
    return null;
  }

  try {
    const normalized = new URL(rawUrl.trim());
    if (!['http:', 'https:'].includes(normalized.protocol)) {
      return null;
    }
    return normalized.toString();
  } catch {
    return null;
  }
}

function hasTesseractBinary() {
  const result = spawnSync('tesseract', ['--version'], { stdio: 'ignore' });
  return result.status === 0;
}

function stripAnsi(value) {
  return value.replace(/\u001b\[[0-9;]*m/g, '');
}

function summarizePythonError(stderrData) {
  const clean = stripAnsi(stderrData || '').trim();

  if (!clean) {
    return 'Python script failed without error output.';
  }

  if (clean.includes("Tesseract OCR is not installed") || clean.includes("TesseractNotFoundError")) {
    return "Tesseract OCR is not installed or not available in PATH. Install it, or set OCR_ENGINE=easyocr before starting the backend.";
  }

  const lines = clean.split('\n').map((line) => line.trim()).filter(Boolean);
  return lines[lines.length - 1] || clean;
}

function runImageScript(scriptPath, imagePath, req) {
  const useAlgorithms = shouldUseAlgorithms(req?.body?.useAlgorithms);
  return runPythonCommand(
    [
      scriptPath,
      '--image', imagePath,
      '--format', 'json',
      '--mode', DEFAULT_OCR_MODE,
      '--engine', DEFAULT_OCR_ENGINE,
      ...(useAlgorithms ? [] : ['--disable-algorithms']),
    ],
    req
  );
}

function runPythonCommand(pythonArgs, req = null) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python3', [
      ...pythonArgs
    ], {
      cwd: projectRoot,
      env: {
        ...process.env,
        OBJC_DISABLE_INITIALIZE_FORK_SAFETY: 'YES',
        OMP_NUM_THREADS: process.env.OMP_NUM_THREADS || '1',
        MKL_NUM_THREADS: process.env.MKL_NUM_THREADS || '1',
        VECLIB_MAXIMUM_THREADS: process.env.VECLIB_MAXIMUM_THREADS || '1',
        TOKENIZERS_PARALLELISM: 'false',
        PYTORCH_ENABLE_MPS_FALLBACK: '1',
      },
    });

    let stdoutData = '';
    let stderrData = '';
    let isResolved = false;
    const MAX_OUTPUT_SIZE = 50 * 1024 * 1024; // 50MB limit
    const TIMEOUT_MS = 120000; // 2 minutes timeout

    // Set up timeout
    const timeout = setTimeout(() => {
      if (!isResolved) {
        console.error('[Python] Process timeout - killing process');
        pythonProcess.kill('SIGTERM');
        setTimeout(() => pythonProcess.kill('SIGKILL'), 5000); // Force kill after 5s
        cleanup();
        reject(new Error('Python script execution timed out after 2 minutes'));
      }
    }, TIMEOUT_MS);

    // Handle real client disconnects without treating normal request closure as an abort.
    const abortHandler = () => {
      if (!isResolved) {
        console.log('[Python] Request aborted - killing process');
        pythonProcess.kill('SIGTERM');
        setTimeout(() => pythonProcess.kill('SIGKILL'), 1000);
        cleanup();
        reject(new Error('Request aborted by client'));
      }
    };

    const responseCloseHandler = () => {
      if (!isResolved && req?.aborted) {
        abortHandler();
      }
    };

    if (req) {
      req.once('aborted', abortHandler);
      req.res?.once('close', responseCloseHandler);
    }

    const cleanup = () => {
      isResolved = true;
      clearTimeout(timeout);
      if (req) {
        req.removeListener('aborted', abortHandler);
        req.res?.removeListener('close', responseCloseHandler);
      }
    };

    pythonProcess.stdout.on('data', (data) => {
      stdoutData += data.toString();
      // Check buffer size limit
      if (stdoutData.length > MAX_OUTPUT_SIZE) {
        console.error('[Python] Output size limit exceeded - killing process');
        pythonProcess.kill('SIGTERM');
        cleanup();
        reject(new Error('Python script output exceeded size limit (50MB)'));
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      stderrData += data.toString();
      // Also limit stderr
      if (stderrData.length > MAX_OUTPUT_SIZE) {
        console.error('[Python] Error output size limit exceeded - killing process');
        pythonProcess.kill('SIGTERM');
        cleanup();
        reject(new Error('Python script error output exceeded size limit (50MB)'));
      }
    });

    pythonProcess.on('close', (code, signal) => {
      if (isResolved) return; // Already handled by timeout or abort
      cleanup();

      if (code !== 0) {
        console.error(`[Python] Error output:`, stderrData);
        const exitDetail = signal ? `signal ${signal}` : `code ${code}`;
        const summary = summarizePythonError(stderrData);
        return reject(new Error(`Python script failed with ${exitDetail}: ${summary}`));
      }

      try {
        // Try to parse JSON from stdout
        // The script might output some logs before JSON, so we need to extract it
        const jsonMatch = stdoutData.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const result = JSON.parse(jsonMatch[0]);
          resolve(result);
        } else {
          // If no JSON found, return the text output
          resolve({
            combined_text: stdoutData.trim(),
            raw_output: stdoutData
          });
        }
      } catch (error) {
        console.error(`[Python] Failed to parse output:`, error);
        reject(new Error(`Failed to parse Python script output: ${error.message}`));
      }
    });

    pythonProcess.on('error', (error) => {
      if (isResolved) return;
      cleanup();
      reject(new Error(`Failed to start Python script: ${error.message}`));
    });
  });
}

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('[API] Unhandled error:', error);
  res.status(500).json({
    success: false,
    error: error.message || 'Internal server error'
  });
});

if (hasBuiltFrontend) {
  app.use(express.static(distDir));

  app.get('*', (req, res, next) => {
    if (req.path.startsWith('/api/')) {
      return next();
    }
    res.sendFile(path.join(distDir, 'index.html'));
  });
}

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n🚀 Factify API Server running on http://localhost:${PORT}`);
  console.log(`📡 Health check: http://localhost:${PORT}/api/health`);
  console.log(`📝 Text analysis endpoint: http://localhost:${PORT}/api/analyze-text`);
  console.log(`📤 Image upload endpoint: http://localhost:${PORT}/api/analyze-image`);
  console.log(`🔗 URL scrape endpoint: http://localhost:${PORT}/api/analyze-url\n`);
  if (hasBuiltFrontend) {
    console.log(`🌐 Frontend served from: http://localhost:${PORT}\n`);
  }
}).on('error', (err) => {
  console.error('❌ Failed to start server:', err);
  process.exit(1);
});
