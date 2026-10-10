import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { issueService } from '../services/api';
import { AIAnalysisResult } from '../types';
import { Upload, MapPin, Cpu, AlertCircle, ArrowRight, CheckCircle2, Image as ImageIcon, Crosshair, Map } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const fadeUp = { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } };

export const ReportIssuePage: React.FC = () => {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [latitude, setLatitude] = useState<number>(28.6139);
  const [longitude, setLongitude] = useState<number>(77.2090);
  const [address, setAddress] = useState('Connaught Place Ring Road, Sector 4');
  
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<AIAnalysisResult | null>(null);
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
    setAiResult(null); // Reset AI result if image changes
  };

  const handleFetchLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(Number(pos.coords.latitude.toFixed(6)));
          setLongitude(Number(pos.coords.longitude.toFixed(6)));
          setAddress(`GPS Coordinates (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`);
        },
        (err) => {
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
      if (!title) {
        setTitle(`Reported ${result.issue_type} near ${address.split(',')[0]}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze image with AI model.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmitReport = async () => {
    if (!aiResult) {
      setError('Please run AI analysis first before submitting.');
      return;
    }
    if (aiResult.status === 'no_detection' || !aiResult.issue_type) {
      setError('Cannot submit report. No supported defect was detected in the image.');
      return;
    }
    setSubmitting(true);
    setError('');

    try {
      const createdIssue = await issueService.createIssue({
        title: title || `${aiResult.issue_type} Defect Report`,
        description,
        issue_type: aiResult.issue_type,
        latitude,
        longitude,
        address,
        original_image_url: aiResult.original_image_url,
        annotated_image_url: aiResult.annotated_image_url,
        ai_confidence: aiResult.confidence || 0,
        severity: aiResult.severity || 'MEDIUM',
        priority_score: aiResult.priority_score || 0,
        bounding_box_json: JSON.stringify(aiResult.bounding_boxes)
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
          <Cpu className="w-3 h-3" /> AI REPORTING WIZARD
        </div>
        <h1 className="text-2xl font-bold text-white">Report Civic Defect</h1>
        <p className="text-sm text-slate-400 mt-0.5 max-w-2xl">
          Upload an image of the infrastructure issue. Our computer vision models will automatically detect the defect type, classify severity, and route it to the correct department.
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
        {/* Left Column */}
        <div className="space-y-6">
          {/* Step 1: Upload */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-cyan-400" /> 1. Upload Defect Image
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
                  <img src={imagePreview} alt="Preview" className="w-full h-64 object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="px-4 py-2 rounded-lg bg-civic-card border border-civic-border text-sm font-medium text-white">Click to change</div>
                  </div>
                </div>
              ) : (
                <div className="py-16 flex flex-col items-center justify-center">
                  <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-3">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-semibold text-slate-200">Click or drag image here</div>
                  <div className="text-[11px] text-slate-500 mt-1">High-resolution JPG/PNG for best AI results</div>
                </div>
              )}
            </div>

            <button
              onClick={handleRunAIAnalysis}
              disabled={!selectedFile || analyzing || !!aiResult}
              className={`w-full py-3 rounded-xl font-semibold text-sm shadow-lg flex items-center justify-center gap-2 transition-all ${
                aiResult 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-not-allowed'
                  : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-600/20 disabled:opacity-40 disabled:cursor-not-allowed'
              }`}
            >
              {analyzing ? (
                <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Running YOLOv8 Pipeline...</>
              ) : aiResult ? (
                <><CheckCircle2 className="w-4 h-4" /> Analysis Complete</>
              ) : (
                <><Cpu className="w-4 h-4" /> Run AI Vision Analysis</>
              )}
            </button>
          </motion.div>

          {/* Step 2: Location */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-400" /> 2. Location Metadata
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

        {/* Right Column */}
        <div className="space-y-6">
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
            className="bg-civic-card border border-civic-border rounded-2xl p-6 space-y-5 h-full flex flex-col">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-cyan-400" /> 3. Verification & Submit
            </h2>

            {!aiResult ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-12 border-2 border-dashed border-civic-border rounded-xl">
                <div className="w-12 h-12 rounded-full bg-slate-800/50 flex items-center justify-center mb-3">
                  <Cpu className="w-5 h-5 text-slate-600" />
                </div>
                <p className="text-sm font-semibold text-slate-400">Waiting for AI Output</p>
                <p className="text-[11px] text-slate-500 mt-1 max-w-[220px]">Upload an image and run analysis to populate verification data.</p>
              </div>
            ) : aiResult.status === 'no_detection' ? (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-5 flex-1 flex flex-col">
                 <div className="flex-1 flex flex-col items-center justify-center text-center py-12 border-2 border-dashed border-rose-500/30 rounded-xl bg-rose-500/5">
                    <AlertCircle className="w-8 h-8 text-rose-400 mb-3" />
                    <p className="text-sm font-semibold text-rose-400">No Supported Issue Detected</p>
                    <p className="text-[11px] text-slate-400 mt-2 max-w-[220px]">The AI model could not confidently identify a supported civic defect (e.g. pothole, road damage) in this image. Please upload a clearer image.</p>
                 </div>
              </motion.div>
            ) : (
              <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-5 flex-1 flex flex-col">
                {/* AI Vision Payload Box */}
                <div className="bg-civic-bg border border-civic-border rounded-xl p-4">
                  <div className="text-[10px] font-mono text-slate-500 mb-3 flex items-center justify-between">
                    <span>AI_VISION_PAYLOAD</span>
                    <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> VERIFIED</span>
                  </div>
                  
                  {aiResult.annotated_image_url && (
                    <div className="mb-4 relative rounded-lg overflow-hidden border border-civic-border">
                      <img src={aiResult.annotated_image_url} alt="AI Annotated" className="w-full h-40 object-cover" />
                      <div className="absolute bottom-2 left-2 bg-civic-bg/90 backdrop-blur-sm px-2 py-0.5 rounded text-[9px] font-mono text-emerald-400 border border-emerald-500/20">
                        BBox Overlay Rendered
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div>
                      <div className="text-[10px] font-mono text-slate-500 uppercase">Detected Class</div>
                      <div className="text-sm font-bold text-cyan-400 mt-0.5">{aiResult.issue_type}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-slate-500 uppercase">AI Confidence</div>
                      <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">{(aiResult.confidence! * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-slate-500 uppercase">Severity Level</div>
                      <div className="text-sm font-bold text-rose-400 mt-0.5">{aiResult.severity}</div>
                    </div>
                    <div>
                      <div className="text-[10px] font-mono text-slate-500 uppercase">Priority Score</div>
                      <div className="text-sm font-bold text-amber-400 font-mono mt-0.5">{aiResult.priority_score}/100</div>
                    </div>
                  </div>
                  <div className="pt-3 border-t border-civic-border">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">Auto-Routing Destination</div>
                    <div className="text-xs font-semibold text-purple-400 mt-1 flex items-center gap-1.5">
                      <ArrowRight className="w-3 h-3" /> {aiResult.recommended_department}
                    </div>
                  </div>
                </div>

                {/* Final Form */}
                <div className="space-y-4 mt-auto">
                  <div>
                    <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Issue Title</label>
                    <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="E.g. Deep pothole on main road"
                      className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 transition-colors" />
                  </div>
                  <div>
                    <label className="text-[10px] font-mono text-slate-500 uppercase mb-1 block">Additional Context (Optional)</label>
                    <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Add any details helpful for repair crews..."
                      className="w-full bg-civic-bg border border-civic-border rounded-lg px-3 py-2 text-sm text-white resize-none focus:outline-none focus:border-cyan-500/50 transition-colors" />
                  </div>
                  <button onClick={handleSubmitReport} disabled={submitting || aiResult.status === 'no_detection'}
                    className="w-full py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50 mt-4">
                    {submitting ? (
                      <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Submitting Report...</>
                    ) : (
                      <>Commit to Database <ArrowRight className="w-4 h-4" /></>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
};
