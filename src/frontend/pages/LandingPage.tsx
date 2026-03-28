import React, { useState, useCallback, useRef, useEffect } from "react";
import {
  FileText,
  Image,
  Link as LinkIcon,
  Sparkles,
  Network,
  BarChart3,
  UploadCloud,
  Loader2,
  AlertCircle,
} from "lucide-react";
import AnalysisReport from "../components/dashboard/AnalysisReport";
import {
  analyzeImage,
  analyzeText,
  analyzeUrl,
  type AnalysisResult,
} from "../services/api";

export default function LandingPage() {
  const [activeTab, setActiveTab] = useState<"text" | "image" | "url">("text");
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    null,
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [urlInput, setUrlInput] = useState("");
  const [textInput, setTextInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleFileSelect = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (file) {
        setSelectedFile(file);
        setUploadError(null);
      }
    },
    [],
  );

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();

    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      setSelectedFile(file);
      setUploadError(null);
    } else {
      setUploadError("Please drop an image file (JPEG, PNG, WEBP, AVIF)");
    }
  }, []);

  const handleDragOver = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();
    },
    [],
  );

  const handleUploadClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleAnalyze = useCallback(async () => {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    if (activeTab === "text") {
      const trimmedText = textInput.trim();
      if (!trimmedText) {
        setUploadError("Please enter text to analyze.");
        return;
      }

      setIsUploading(true);
      setUploadError(null);

      try {
        const response = await analyzeText(trimmedText, signal);

        if (response.success) {
          setAnalysisResult(response.result);
          setShowAnalysis(true);
        } else {
          throw new Error(response.error || "Text analysis failed");
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          console.log("Request was aborted");
          return;
        }
        console.error("Text analysis error:", error);
        setUploadError(
          error instanceof Error
            ? error.message
            : "Failed to analyze text. Please make sure the backend server is running.",
        );
      } finally {
        setIsUploading(false);
      }
    } else if (activeTab === "image" && selectedFile) {
      setIsUploading(true);
      setUploadError(null);

      try {
        console.log("Uploading image:", selectedFile.name);
        const response = await analyzeImage(selectedFile, signal);

        if (response.success) {
          setAnalysisResult(response.result);
          setShowAnalysis(true);
          console.log("Analysis complete:", response.result);
        } else {
          throw new Error(response.error || "Analysis failed");
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          console.log("Request was aborted");
          return;
        }
        console.error("Upload error:", error);
        setUploadError(
          error instanceof Error
            ? error.message
            : "Failed to analyze image. Please make sure the backend server is running.",
        );
      } finally {
        setIsUploading(false);
      }
    } else if (activeTab === "url") {
      const trimmedUrl = urlInput.trim();
      if (!trimmedUrl) {
        setUploadError("Please enter a URL to analyze.");
        return;
      }

      setIsUploading(true);
      setUploadError(null);

      try {
        const response = await analyzeUrl(trimmedUrl, signal);

        if (response.success) {
          setAnalysisResult(response.result);
          setShowAnalysis(true);
        } else {
          throw new Error(response.error || "URL analysis failed");
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          console.log("Request was aborted");
          return;
        }
        console.error("URL analysis error:", error);
        setUploadError(
          error instanceof Error
            ? error.message
            : "Failed to analyze URL. Please make sure the backend server is running.",
        );
      } finally {
        setIsUploading(false);
      }
    }
  }, [activeTab, selectedFile, textInput, urlInput]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-surface via-surface-container-low to-slate-100">
      <main
        className={`pt-20 pb-10 mx-auto grid grid-cols-1 gap-6 px-4 sm:px-6 md:pt-24 md:pb-12 lg:grid-cols-12 lg:gap-10 xl:gap-12 transition-all duration-700 ${showAnalysis ? "max-w-[1700px] w-full" : "max-w-4xl"}`}
      >
        {/* Left Content: Hero & Input */}
        <div
          className={`space-y-8 md:space-y-10 lg:space-y-12 transition-all duration-700 ${showAnalysis ? "lg:col-span-5 xl:col-span-4" : "lg:col-span-12"}`}
        >
          {/* Hero Section */}
          <section className="space-y-4">
            <h1 className="text-4xl font-black tracking-tight text-on-surface leading-[1.05] sm:text-5xl md:text-6xl">
              Think Before You{" "}
              <span className="text-primary italic">Believe</span>
            </h1>
            <p className="max-w-2xl text-base leading-relaxed text-secondary sm:text-lg md:text-xl">
              In an era of synthetic misinformation, Factify provides the
              technical rigor of investigative journalism to every citizen.
              Verify text, images, and links in real-time.
            </p>
          </section>

          {/* Core Interaction Card */}
          <div className="bg-surface-container-lowest rounded-2xl shadow-[0_20px_40px_-12px_rgba(11,28,48,0.06)] border border-outline-variant/15 overflow-hidden">
            {/* Tabs */}
            <div className="grid grid-cols-3 border-b border-outline-variant/10">
              <button
                type="button"
                onClick={() => setActiveTab("text")}
                className={`min-w-0 px-3 py-4 flex items-center justify-center gap-2 text-xs sm:text-sm md:text-base transition-colors ${activeTab === "text" ? "border-b-2 border-primary text-primary font-semibold" : "text-secondary hover:bg-surface-container-low"}`}
              >
                <FileText className="h-4 w-4 shrink-0 sm:h-5 sm:w-5" />
                <span className="truncate">Text Input</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("image")}
                className={`min-w-0 px-3 py-4 flex items-center justify-center gap-2 text-xs sm:text-sm md:text-base transition-colors ${activeTab === "image" ? "border-b-2 border-primary text-primary font-semibold" : "text-secondary hover:bg-surface-container-low"}`}
              >
                <Image className="h-4 w-4 shrink-0 sm:h-5 sm:w-5" />
                <span className="truncate">Image Upload</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("url")}
                className={`min-w-0 px-3 py-4 flex items-center justify-center gap-2 text-xs sm:text-sm md:text-base transition-colors ${activeTab === "url" ? "border-b-2 border-primary text-primary font-semibold" : "text-secondary hover:bg-surface-container-low"}`}
              >
                <LinkIcon className="h-4 w-4 shrink-0 sm:h-5 sm:w-5" />
                <span className="truncate">URL Input</span>
              </button>
            </div>
            <div className="space-y-6 p-5 sm:p-6 md:p-8">
              {/* Input Section */}
              <div className="space-y-4">
                <label className="block text-xs font-bold tracking-widest text-secondary uppercase">
                  Analysis Content
                </label>

                {activeTab === "text" && (
                  <textarea
                    value={textInput}
                    onChange={(event) => {
                      setTextInput(event.target.value);
                      setUploadError(null);
                    }}
                    className="w-full bg-surface-container-low border border-outline-variant/15 rounded-xl p-4 sm:p-5 md:p-6 text-on-surface placeholder:text-secondary/50 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none text-base sm:text-lg leading-relaxed"
                    placeholder="Paste the suspicious article, social media post, or claim here for a deep forensic audit..."
                    rows={7}
                  />
                )}

                {activeTab === "image" && (
                  <div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/webp,image/avif"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <div
                      onClick={handleUploadClick}
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      className="flex min-h-56 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed border-outline-variant/30 bg-surface-container-low p-5 text-center transition-colors cursor-pointer group hover:bg-surface-container-high sm:min-h-64 sm:p-6"
                    >
                      {selectedFile ? (
                        <>
                          <div className="w-16 h-16 rounded-full bg-tertiary/10 flex items-center justify-center text-tertiary mb-4">
                            <Image className="w-8 h-8" />
                          </div>
                          <p className="mb-1 break-words text-base font-bold text-on-surface sm:text-lg">
                            {selectedFile.name}
                          </p>
                          <p className="text-secondary text-sm">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedFile(null);
                            }}
                            className="mt-4 text-sm text-error hover:underline"
                          >
                            Remove file
                          </button>
                        </>
                      ) : (
                        <>
                          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                            <UploadCloud className="w-8 h-8" />
                          </div>
                          <p className="mb-1 text-base font-bold text-on-surface sm:text-lg">
                            Drag and drop an image, or click to browse
                          </p>
                          <p className="text-sm leading-6 text-secondary">
                            Supports JPG, PNG, WEBP, and AVIF for advanced
                            metadata forensics.
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === "url" && (
                  <div className="flex items-start gap-3 rounded-xl border border-outline-variant/15 bg-surface-container-low p-4 transition-all focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 sm:items-center">
                    <LinkIcon className="mt-1 h-5 w-5 shrink-0 text-secondary sm:mt-0 sm:h-6 sm:w-6" />
                    <input
                      type="url"
                      value={urlInput}
                      onChange={(event) => {
                        setUrlInput(event.target.value);
                        setUploadError(null);
                      }}
                      className="w-full bg-transparent border-none p-0 text-base text-on-surface placeholder:text-secondary/50 outline-none focus:ring-0 sm:text-lg"
                      placeholder="https://example.com/suspicious-article"
                    />
                  </div>
                )}

                {uploadError && (
                  <div className="mt-4 p-4 bg-error-container/20 border border-error/30 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-error shrink-0 mt-0.5" />
                    <div>
                      <p className="text-error font-semibold text-sm">
                        {activeTab === "url" ? "URL Error" : "Upload Error"}
                      </p>
                      <p className="text-error/80 text-sm mt-1">
                        {uploadError}
                      </p>
                    </div>
                  </div>
                )}
              </div>
              {/* Action Bar */}
              <div className="flex flex-col gap-4 pt-4 sm:gap-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-4">
                  <button
                    type="button"
                    onClick={() => alert("Language auto-detected: English")}
                    className="flex items-center gap-2 text-left text-sm font-medium text-secondary hover:text-primary transition-colors"
                  >
                    <Sparkles className="w-4 h-4" />
                    Auto-detect Language
                  </button>
                  <button
                    type="button"
                    onClick={() => alert("Context Tuning options open")}
                    className="flex items-center gap-2 text-left text-sm font-medium text-secondary hover:text-primary transition-colors"
                  >
                    <Network className="w-4 h-4" />
                    Context Tuning
                  </button>
                </div>
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={
                    isUploading ||
                    (activeTab === "text" && !textInput.trim()) ||
                    (activeTab === "image" && !selectedFile) ||
                    (activeTab === "url" && !urlInput.trim())
                  }
                  className="flex w-full items-center justify-center gap-3 rounded-xl bg-gradient-to-br from-primary to-primary-container px-6 py-4 text-base font-bold text-white shadow-lg shadow-primary/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100 sm:text-lg lg:w-auto"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <span>Analyze Content</span>
                      <BarChart3 className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Content: Analysis Report */}
        {showAnalysis && (
          <div className="min-w-0 lg:col-span-7 xl:col-span-8">
            <AnalysisReport analysisData={analysisResult} />
          </div>
        )}
      </main>
    </div>
  );
}
