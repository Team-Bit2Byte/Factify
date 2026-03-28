import express from 'express';
import multer from 'multer';
import cors from 'cors';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '..', '..');

const app = express();
const PORT = process.env.PORT || 3001;
const DEFAULT_OCR_ENGINE = process.env.OCR_ENGINE || (process.platform === 'darwin' ? 'tesseract' : 'auto');
const DEFAULT_OCR_MODE = process.env.OCR_MODE || 'ocr';

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
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
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
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Factify API server is running' });
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
    const result = await runPythonScript(pythonScript, imagePath);
    
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
function runPythonScript(scriptPath, imagePath) {
  return new Promise((resolve, reject) => {
    const pythonArgs = [
      scriptPath,
      '--image', imagePath,
      '--format', 'json',
      '--mode', DEFAULT_OCR_MODE,
      '--engine', DEFAULT_OCR_ENGINE,
    ];

    const pythonProcess = spawn('python3', [
      ...pythonArgs
    ], {
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

    pythonProcess.stdout.on('data', (data) => {
      stdoutData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderrData += data.toString();
    });

    pythonProcess.on('close', (code, signal) => {
      if (code !== 0) {
        console.error(`[Python] Error output:`, stderrData);
        const exitDetail = signal ? `signal ${signal}` : `code ${code}`;
        return reject(new Error(`Python script failed with ${exitDetail}: ${stderrData}`));
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

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n🚀 Factify API Server running on http://localhost:${PORT}`);
  console.log(`📡 Health check: http://localhost:${PORT}/api/health`);
  console.log(`📤 Upload endpoint: http://localhost:${PORT}/api/analyze-image\n`);
});
