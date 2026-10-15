import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { issueService } from '../services/api';
import { AIAnalysisResult, ALL_15_CATEGORIES, IssueType, SeverityLevel } from '../types';
import { 
  Upload, MapPin, Cpu, AlertCircle, ArrowRight, CheckCircle2, 
  Image as ImageIcon, Crosshair, Map, ShieldAlert, Check, X, Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const fadeUp = { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } };

const DEPARTMENT_LOOKUP: Record<string, string> = {
  // Road
  'Pothole': 'Road & Public Works Department (DEPT_PWD)',
  'Longitudinal Crack': 'Road & Public Works Department (DEPT_PWD)',
  'Transverse Crack': 'Road & Public Works Department (DEPT_PWD)',
  'Alligator Crack': 'Road & Public Works Department (DEPT_PWD)',
  'Damaged Road Surface': 'Road & Public Works Department (DEPT_PWD)',
  'Road Damage': 'Road & Public Works Department (DEPT_PWD)',

  // Sanitation
  'Garbage Accumulation': 'Waste Management & Sanitation Dept (DEPT_SAN)',
  'Illegal Dumping': 'Waste Management & Sanitation Dept (DEPT_SAN)',
  'Overflowing Garbage Bins': 'Waste Management & Sanitation Dept (DEPT_SAN)',

  // Drainage
  'Blocked Drains': 'Stormwater Drainage Dept (DEPT_DRAIN)',
  'Overflowing Drains': 'Stormwater Drainage Dept (DEPT_DRAIN)',
  'Waterlogging': 'Stormwater Drainage Dept (DEPT_DRAIN)',
  'Damaged Drainage Covers': 'Stormwater Drainage Dept (DEPT_DRAIN)',

  // Utility
  'Open Manhole': 'Sewerage & Sanitation Board (DEPT_SEW)',
  'Broken Streetlight': 'Electrical Infrastructure Dept (DEPT_ELEC)',
};

const YOLO_SUPPORTED_CLASSES = new Set([
  'Pothole',
  'Longitudinal Crack',
  'Transverse Crack',
  'Alligator Crack'
]);

export const ReportIssuePage: React.FC = () => {
  const navigate = useNavigate();

  // 1. Citizen reporting inputs
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [manualSeverity, setManualSeverity] = useState<SeverityLevel>(SeverityLevel.MEDIUM);
  const [latitude, setLatitude] = useState<number>(28.6139);
  const [longitude, setLongitude] = useState<number>(77.2090);
  const [address, setAddress] = useState('Connaught Place Ring Road, Sector 4');

  // 2. AI state
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<AIAnalysisResult | null>(null);
  const [aiAccepted, setAiAccepted] = useState<boolean>(true); // Whether citizen accepts AI suggestion on disagreement
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (file: File | null) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file (JPG, PNG, WEBP)');
      return;
    }
    setSelectedFile(file);
    setImagePreview(URL.createObjectURL(file));
    setError('');
    setAiResult(null); // Reset AI result when image changes
  };

  const handleFetchLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(Number(pos.coords.latitude.toFixed(6)));
          setLongitude(Number(pos.coords.longitude.toFixed(6)));
          setAddress(`GPS Coordinates (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`);
        },
        () => {
          setError('Could not retrieve precise location. Please enter manually or allow permissions.');
        }
      );
    }
  };

  const handleRunAIAnalysis = async () => {
    if (!selectedFile) {
      setError('Please upload an infrastructure image first.');
      return;
    }
    setError('');
    setAnalyzing(true);

    try {
      const result = await issueService.analyzeImage(selectedFile);
      setAiResult(result);

      // Auto-suggest title if empty and AI detected a defect
      if (result.issue_type && !title) {
        setTitle(`Reported ${result.issue_type} near ${address.split(',')[0]}`);
      }

      // If user hadn't selected a category yet and AI detected something, set it
      if (!selectedCategory && result.issue_type) {
        setSelectedCategory(result.issue_type);
        setAiAccepted(true);
      } else if (result.issue_type && selectedCategory) {
        // If there's an AI result and a selection, default to accepting AI if it matches
        setAiAccepted(result.issue_type === selectedCategory);
      }
    } catch (err: any) {
      setAiResult({
        status: 'vision_unavailable',
        message: err.response?.data?.detail || 'Automated AI vision model is currently unavailable on this host.',
        original_image_url: imagePreview || '',
        issue_type: null,
        confidence: 0,
        severity: null,
        priority_score: 0,
        recommended_department: null,
        recommended_department_code: null,
        bounding_boxes: [],
        defect_area_ratio: 0
      });
    } finally {
      setAnalyzing(false);
    }
  };

  // Determine final effective category
  const hasAiDetection = Boolean(aiResult && aiResult.status === 'success' && aiResult.issue_type);
  const isCategoryMismatch = hasAiDetection && selectedCategory && aiResult?.issue_type !== selectedCategory;
  
  const effectiveCategory = hasAiDetection 
    ? (aiAccepted ? (aiResult?.issue_type || selectedCategory) : selectedCategory)
    : selectedCategory;

  const currentCategoryMeta = ALL_15_CATEGORIES.find(c => c.name === (selectedCategory || effectiveCategory));
  const isAiCapableCategory = selectedCategory ? YOLO_SUPPORTED_CLASSES.has(selectedCategory) : true;

  const handleSubmitReport = async () => {
    if (!selectedCategory && !effectiveCategory) {
      setError('Please select an issue category from the 15 supported categories.');
      return;
    }

    if (!selectedFile && !aiResult?.original_image_url) {
      setError('Please upload an infrastructure photo to accompany your report.');
      return;
    }

    const finalCategory = effectiveCategory || selectedCategory;
    if (!finalCategory) {
      setError('Please select a valid defect category before submitting.');
      return;
    }

    setSubmitting(true);
    setError('');

    // Determine AI analysis status string
    let analysisStatus = 'MANUAL';
    if (aiResult) {
      if (aiResult.status === 'success') {
        if (isCategoryMismatch) {
          analysisStatus = aiAccepted ? 'AI_SUGGESTION_ACCEPTED' : 'CITIZEN_OVERRODE_AI';
        } else {
          analysisStatus = 'SUCCESS';
        }
      } else if (aiResult.status === 'no_detection') {
        analysisStatus = 'NO_DETECTION';
      } else {
        analysisStatus = 'VISION_UNAVAILABLE';
      }
    }

    const useAiMetrics = hasAiDetection && aiAccepted;

    try {
      const createdIssue = await issueService.createIssue({
        title: title || `${finalCategory} Report`,
        description,
        issue_type: finalCategory as IssueType,
        latitude,
        longitude,
        address,
        original_image_url: aiResult?.original_image_url || imagePreview || '',
        annotated_image_url: useAiMetrics ? aiResult?.annotated_image_url : undefined,
        ai_confidence: useAiMetrics ? (aiResult?.confidence || 0) : 0,
        severity: useAiMetrics && aiResult?.severity ? aiResult.severity : manualSeverity,
        priority_score: useAiMetrics && aiResult?.priority_score ? aiResult.priority_score : 50.0,
        bounding_box_json: useAiMetrics ? JSON.stringify(aiResult?.bounding_boxes || []) : "[]",
        detected_defects_json: JSON.stringify(aiResult?.detected_defects || []),
        model_provenance_json: JSON.stringify(aiResult?.model_provenance || {}),
        ai_analysis_status: analysisStatus
      });

      navigate(`/issue/${createdIssue.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit issue report.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp}>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-mono tracking-wider mb-2">
          <Cpu className="w-3 h-3" /> CIVIC REPORTING WIZARD • 15 MUNICIPAL CATEGORIES
        </div>
        <h1 className="text-2xl font-bold text-white">Report Civic Infrastructure Defect</h1>
        <p className="text-sm text-slate-400 mt-0.5 max-w-2xl">
          Select the reporting category, upload a photo, and optionally run YOLOv8 computer vision detection. Municipal officers will triage and verify all reported issues.
        </p>
      </motion.div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
            className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Category, Upload, Location */}
        <div className="space-y-6">
          {/* Step 1: Upfront Category Selection (15 Categories) */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 text-xs flex items-center justify-center font-bold">1</span>
              Select Defect Category (15 Categories Supported)
            </h2>

            <div>
              <label className="text-[10px] font-mono text-slate-400 uppercase mb-1.5 block">Reporting Category *</label>
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setError('');
                }}
                className="w-full bg-civic-bg border border-civic-border rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
              >
                <option value="">-- Choose Reporting Category (15 Options) --</option>
                
                <optgroup label="Road Infrastructure Defects (6)">
                  <option value="Pothole">Pothole [YOLOv8 Object Detection Supported]</option>
                  <option value="Longitudinal Crack">Longitudinal Crack [YOLOv8 Object Detection Supported]</option>
                  <option value="Transverse Crack">Transverse Crack [YOLOv8 Object Detection Supported]</option>
                  <option value="Alligator Crack">Alligator Crack [YOLOv8 Object Detection Supported]</option>
                  <option value="Damaged Road Surface">Damaged Road Surface [Manual Citizen Reporting]</option>
                  <option value="Road Damage">Road Damage [Legacy Umbrella — Manual Reporting]</option>
                </optgroup>

                <optgroup label="Sanitation & Waste Defects (3)">
                  <option value="Garbage Accumulation">Garbage Accumulation [Manual Citizen Reporting]</option>
                  <option value="Illegal Dumping">Illegal Dumping [Manual Citizen Reporting]</option>
                  <option value="Overflowing Garbage Bins">Overflowing Garbage Bins [Manual Citizen Reporting]</option>
                </optgroup>

                <optgroup label="Drainage & Water Defects (4)">
                  <option value="Blocked Drains">Blocked Drains [Manual Citizen Reporting]</option>
                  <option value="Overflowing Drains">Overflowing Drains [Manual Citizen Reporting]</option>
                  <option value="Waterlogging">Waterlogging [Manual Citizen Reporting]</option>
                  <option value="Damaged Drainage Covers">Damaged Drainage Covers [Manual Citizen Reporting]</option>
                </optgroup>

                <optgroup label="Public Utilities & Safety (2)">
                  <option value="Open Manhole">Open Manhole [Manual Citizen Reporting — Sewerage Board]</option>
                  <option value="Broken Streetlight">Broken Streetlight [Manual Citizen Reporting — Electrical Dept]</option>
                </optgroup>
              </select>
            </div>

            {/* Dynamic Capability & Department Guidance */}
            {selectedCategory && (
              <div className="p-3 rounded-xl bg-slate-900/80 border border-civic-border text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase text-slate-400">Target Department:</span>
                  <span className="text-[11px] font-semibold text-purple-400 font-mono">
                    {DEPARTMENT_LOOKUP[selectedCategory] || 'Municipal Dispatch'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase text-slate-400">AI Detection Status:</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                    isAiCapableCategory 
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}>
                    {isAiCapableCategory ? 'YOLOv8 Detection Supported' : 'Manual Citizen Reporting'}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 leading-relaxed pt-1">
                  {currentCategoryMeta?.description || 'Municipal infrastructure issue reported by citizen.'}
                </p>
                {!isAiCapableCategory && (
                  <p className="text-[10px] text-amber-400/90 italic flex items-center gap-1 pt-0.5">
                    <Info className="w-3 h-3 shrink-0" />
                    Automated YOLO vision only detects road cracks & potholes. This category uses direct citizen manual dispatch.
                  </p>
                )}
              </div>
            )}
          </motion.div>

          {/* Step 2: Upload Image */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 text-xs flex items-center justify-center font-bold">2</span>
              Upload Infrastructure Photo
            </h2>

            <div
              className={`border-2 border-dashed rounded-2xl p-2 text-center cursor-pointer transition-all ${
                imagePreview ? 'border-cyan-500/30 bg-civic-bg' : 'border-civic-border hover:border-cyan-500/30 bg-civic-bg/50 hover:bg-civic-bg'
              }`}
              onClick={() => document.getElementById('imageInput')?.click()}
            >
              <input id="imageInput" type="file" accept="image/*" className="hidden" onChange={(e) => handleFileChange(e.target.files?.[0] || null)} />

              {imagePreview ? (
                <div className="relative group rounded-xl overflow-hidden bg-slate-900">
                  <img src={imagePreview} alt="Preview" className="w-full h-56 object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="px-4 py-2 rounded-lg bg-civic-card border border-civic-border text-sm font-medium text-white">Click to change photo</div>
                  </div>
                </div>
              ) : (
                <div className="py-12 flex flex-col items-center justify-center">
                  <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-3">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-semibold text-slate-200">Click or drag defect image here</div>
                  <div className="text-[11px] text-slate-500 mt-1">High-resolution JPG/PNG/WEBP (up to 10MB)</div>
                </div>
              )}
            </div>

            <button
              onClick={handleRunAIAnalysis}
              disabled={!selectedFile || analyzing || (!!aiResult && aiResult.status === 'success')}
              className={`w-full py-3 rounded-xl font-semibold text-sm shadow-lg flex items-center justify-center gap-2 transition-all ${
                aiResult && aiResult.status === 'success'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-not-allowed'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-600/20 disabled:opacity-40 disabled:cursor-not-allowed'
              }`}
            >
              {analyzing ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Running YOLOv8 Road Pipeline...</>
              ) : aiResult && aiResult.status === 'success' ? (
                <><CheckCircle2 className="w-4 h-4" /> AI Analysis Completed</>
              ) : (
                <><Cpu className="w-4 h-4" /> Run AI Defect Analysis (Optional)</>
              )}
            </button>
          </motion.div>

          {/* Step 3: Location Metadata */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 text-xs flex items-center justify-center font-bold">3</span>
                Location Metadata
              </h2>
              <button onClick={handleFetchLocation} type="button" className="text-[10px] font-mono font-medium text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors flex items-center gap-1.5">
                <Crosshair className="w-3 h-3" /> Auto-Locate GPS
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Street Address / Landmark</label>
                <div className="relative">
                  <Map className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input type="text" value={address} onChange={(e) => setAddress(e.target.value)}
                    className="w-full bg-civic-bg border border-civic-border rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-colors" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Latitude</label>
                  <input type="number" step="0.0001" value={latitude} onChange={(e) => setLatitude(parseFloat(e.target.value))}
                    className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-cyan-500/50 transition-colors" />
                </div>
                <div>
                  <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Longitude</label>
                  <input type="number" step="0.0001" value={longitude} onChange={(e) => setLongitude(parseFloat(e.target.value))}
                    className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-cyan-500/50 transition-colors" />
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Column: AI Results & Final Submit */}
        <div className="space-y-6">
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-5 h-full flex flex-col">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-400 text-xs flex items-center justify-center font-bold">4</span>
              Verification & Dispatch Preview
            </h2>

            {/* AI Result Card */}
            {aiResult && (
              <div className="space-y-4">
                {aiResult.status === 'success' && aiResult.issue_type ? (
                  <div className="bg-civic-bg border border-civic-border rounded-xl p-4 space-y-3">
                    <div className="text-[10px] font-mono text-slate-500 flex items-center justify-between">
                      <span>AI_VISION_INFERENCE</span>
                      <span className="text-emerald-400 flex items-center gap-1 font-mono font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5" /> DETECTED: {aiResult.issue_type}
                      </span>
                    </div>

                    {aiResult.annotated_image_url && (
                      <div className="relative rounded-lg overflow-hidden border border-civic-border">
                        <img src={aiResult.annotated_image_url} alt="AI Annotated Overlay" className="w-full h-40 object-cover" />
                        <div className="absolute bottom-2 left-2 bg-civic-bg/90 backdrop-blur-sm px-2 py-0.5 rounded text-[9px] font-mono text-emerald-400 border border-emerald-500/20">
                          {aiResult.bounding_boxes && aiResult.bounding_boxes.length > 0
                            ? `YOLO BBox Overlay (${aiResult.bounding_boxes.length} detected)`
                            : 'Scene Classification'}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 rounded-lg bg-slate-900/60 border border-civic-border">
                        <div className="text-[9px] font-mono text-slate-500 uppercase">Model Prediction</div>
                        <div className="font-bold text-cyan-300 mt-0.5">{aiResult.issue_type}</div>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-900/60 border border-civic-border">
                        <div className="text-[9px] font-mono text-slate-500 uppercase">Detection Confidence</div>
                        <div className="font-bold text-emerald-400 font-mono mt-0.5">
                          {((aiResult.confidence || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {/* Category Disagreement Notice */}
                    {isCategoryMismatch && (
                      <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2">
                        <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs">
                          <ShieldAlert className="w-4 h-4 shrink-0" />
                          <span>Category Disagreement Detected</span>
                        </div>
                        <p className="text-[11px] text-slate-300">
                          You selected <strong className="text-white">"{selectedCategory}"</strong>, but YOLOv8 detected <strong className="text-cyan-300">"{aiResult.issue_type}"</strong>.
                        </p>
                        <div className="flex gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => setAiAccepted(false)}
                            className={`flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                              !aiAccepted
                                ? 'bg-amber-500 text-black shadow-lg shadow-amber-500/20'
                                : 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700'
                            }`}
                          >
                            <Check className="w-3.5 h-3.5" /> Keep "{selectedCategory}"
                          </button>
                          <button
                            type="button"
                            onClick={() => setAiAccepted(true)}
                            className={`flex-1 py-1.5 px-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                              aiAccepted
                                ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/20'
                                : 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700'
                            }`}
                          >
                            <Check className="w-3.5 h-3.5" /> Accept AI: "{aiResult.issue_type}"
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : aiResult.status === 'no_detection' ? (
                  <div className="p-4 rounded-xl border border-cyan-500/20 bg-cyan-500/5 space-y-1.5">
                    <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold">
                      <Info className="w-4 h-4 shrink-0" />
                      <span>No Road Defect Detected by Computer Vision</span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      YOLOv8 evaluated this image and found no standard road cracks or potholes exceeding the confidence threshold. Your report will proceed with your selected category: <strong className="text-white">"{selectedCategory || 'Manual Report'}"</strong> for officer triage.
                    </p>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl border border-slate-700 bg-slate-900/60 space-y-1">
                    <div className="flex items-center gap-2 text-slate-300 text-xs font-semibold">
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>Computer Vision Offline</span>
                    </div>
                    <p className="text-[11px] text-slate-400">
                      Automated vision model is unavailable. Your report will be handled directly as a manual citizen dispatch.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Submission Summary Card */}
            <div className="bg-civic-bg border border-civic-border rounded-xl p-4 space-y-3">
              <div className="text-[10px] font-mono text-slate-500 uppercase">Dispatch Summary</div>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-[9px] font-mono text-slate-500 uppercase">Effective Category</div>
                  <div className="font-bold text-white mt-0.5 truncate">
                    {effectiveCategory || <span className="text-amber-400 italic">Select in Step 1</span>}
                  </div>
                </div>
                <div>
                  <div className="text-[9px] font-mono text-slate-500 uppercase">Assigned Department</div>
                  <div className="font-bold text-purple-400 mt-0.5 truncate">
                    {DEPARTMENT_LOOKUP[effectiveCategory] || 'Municipal Dispatch'}
                  </div>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Observed Severity</label>
                <select
                  value={manualSeverity}
                  onChange={(e) => setManualSeverity(e.target.value as SeverityLevel)}
                  className="w-full bg-civic-card border border-civic-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500/50 transition-colors"
                >
                  <option value={SeverityLevel.LOW}>LOW — Superficial defect</option>
                  <option value={SeverityLevel.MEDIUM}>MEDIUM — Standard road hazard</option>
                  <option value={SeverityLevel.HIGH}>HIGH — Substantial danger to traffic/pedestrians</option>
                  <option value={SeverityLevel.CRITICAL}>CRITICAL — Immediate structural or safety hazard</option>
                </select>
              </div>

              <div className="text-[10px] font-mono text-slate-500 flex items-center justify-between pt-1">
                <span>VERIFICATION_STATUS:</span>
                <span className="text-amber-400 font-bold">UNVERIFIED (Officer Review Required)</span>
              </div>
            </div>

            {/* Final Form Inputs */}
            <div className="space-y-4 mt-auto">
              <div>
                <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Issue Title (Optional)</label>
                <input 
                  type="text" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)} 
                  placeholder={effectiveCategory ? `E.g. ${effectiveCategory} near main junction` : 'E.g. Deep road hazard'}
                  className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-colors" 
                />
              </div>
              <div>
                <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Additional Description / Context</label>
                <textarea 
                  rows={2} 
                  value={description} 
                  onChange={(e) => setDescription(e.target.value)} 
                  placeholder="Provide landmarks, lane direction, or danger context for municipal crews..."
                  className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-sm text-white resize-none focus:outline-none focus:border-cyan-500/50 transition-colors" 
                />
              </div>

              <button 
                onClick={handleSubmitReport} 
                disabled={submitting}
                className="w-full py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {submitting ? (
                  <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Submitting Report to Municipal Queue...</>
                ) : (
                  <>Submit Civic Defect Report <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};
