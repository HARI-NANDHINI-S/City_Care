import React from 'react';
import { Brain, Target, Zap, Layers, Shield } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeUp = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

const statItems = [
  { label: 'Detection Architecture', value: 'YOLOv8', color: 'text-cyan-400' },
  { label: 'Image Processing', value: 'OpenCV', color: 'text-emerald-400' },
  { label: 'Confidence Threshold', value: '85%', color: 'text-amber-400' },
  { label: 'Defect Classes', value: '6 types', color: 'text-purple-400' },
  { label: 'Duplicate Detection', value: 'Haversine 50m', color: 'text-indigo-400' },
  { label: 'Priority Weights', value: '5 factors', color: 'text-rose-400' },
];

const detectionClasses = [
  { name: 'Pothole', code: 'PH', desc: 'Road surface depression with high pedestrian risk', severity: 'CRITICAL' },
  { name: 'Garbage Accumulation', code: 'GA', desc: 'Unsanitary waste buildup in public areas', severity: 'HIGH' },
  { name: 'Waterlogging', code: 'WL', desc: 'Standing water on road or walkway surfaces', severity: 'HIGH' },
  { name: 'Broken Streetlight', code: 'BS', desc: 'Non-functional public lighting infrastructure', severity: 'MEDIUM' },
  { name: 'Open Manhole', code: 'OM', desc: 'Uncovered sewer access posing fall hazard', severity: 'CRITICAL' },
  { name: 'Road Damage', code: 'RD', desc: 'Structural surface damage to carriageway', severity: 'HIGH' },
];

const priorityFactors = [
  { factor: 'AI Confidence Score', weight: '40%', desc: 'YOLO detection confidence from bounding box classification' },
  { factor: 'Defect Severity', weight: '25%', desc: 'Pre-assigned severity weight by defect category class' },
  { factor: 'Bounding Box Area', weight: '20%', desc: 'Relative defect size to image area (larger = more urgent)' },
  { factor: 'Duplicate Reports', weight: '10%', desc: 'Haversine-clustered co-reported tickets boost score' },
  { factor: 'Time Since Reported', weight: '5%', desc: 'Aging factor accumulates urgency over elapsed hours' },
];

const severityColors: Record<string, string> = {
  CRITICAL: 'text-red-400 bg-red-500/10 border-red-500/20',
  HIGH: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  MEDIUM: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
};

export const ModelIntelligencePage: React.FC = () => {
  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-mono tracking-wider mb-2">
          <Brain className="w-3 h-3" /> ML MODEL DOCUMENTATION
        </div>
        <h1 className="text-2xl font-bold text-white">Model Intelligence</h1>
        <p className="text-sm text-slate-400 mt-0.5">Computer vision pipeline, defect classification, and priority scoring engine</p>
      </motion.div>

      {/* Stat Row */}
      <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {statItems.map((s, i) => (
          <motion.div key={i} variants={fadeUp} className="bg-civic-card border border-civic-border rounded-xl p-4 text-center">
            <div className={`text-base font-bold font-mono ${s.color}`}>{s.value}</div>
            <div className="text-[10px] text-slate-500 mt-1">{s.label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Detection Classes */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Target className="w-4 h-4 text-cyan-400" /> Detection Target Classes
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {detectionClasses.map((cls, i) => (
            <motion.div key={cls.code}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 + i * 0.06 }}
              className="bg-civic-card border border-civic-border rounded-xl p-4 hover:border-slate-600 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-bold bg-civic-bg border border-civic-border px-2 py-0.5 rounded text-slate-400">{cls.code}</span>
                  <span className="text-sm font-medium text-white">{cls.name}</span>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${severityColors[cls.severity] || ''}`}>{cls.severity}</span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">{cls.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Priority Scoring */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" /> Priority Scoring Formula
        </h2>
        <div className="bg-civic-card border border-civic-border rounded-2xl overflow-hidden">
          <div className="bg-civic-bg border-b border-civic-border px-5 py-3">
            <code className="text-xs font-mono text-cyan-300">
              score = (confidence × 0.40) + (severity_weight × 0.25) + (bbox_area × 0.20) + (duplicate_factor × 0.10) + (aging_hours × 0.05)
            </code>
          </div>
          <div className="divide-y divide-civic-border">
            {priorityFactors.map((pf, i) => (
              <div key={i} className="px-5 py-4 flex items-center gap-4">
                <div className="w-12 text-center">
                  <span className="text-sm font-bold font-mono text-amber-400">{pf.weight}</span>
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{pf.factor}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{pf.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Duplicate Detection */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.42 }}>
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" /> Spatial Duplicate Detection
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { label: 'Algorithm', value: 'Haversine Formula', desc: 'Great-circle distance calculation between GPS coordinates' },
            { label: 'Spatial Radius', value: '50 meters', desc: 'Issues within 50m of each other are classified as spatial duplicates' },
            { label: 'Temporal Window', value: '72 hours', desc: 'Reports within 72h for the same location are linked and score-boosted' },
          ].map((item, i) => (
            <div key={i} className="bg-civic-card border border-civic-border rounded-xl p-5">
              <div className="text-[10px] font-mono text-slate-500 uppercase mb-1">{item.label}</div>
              <div className="text-base font-bold text-purple-400 font-mono mb-2">{item.value}</div>
              <div className="text-xs text-slate-400 leading-relaxed">{item.desc}</div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Pipeline Flow */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
        <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400" /> AI Processing Pipeline
        </h2>
        <div className="bg-civic-card border border-civic-border rounded-2xl p-6">
          <div className="flex items-center overflow-x-auto gap-2 pb-2">
            {[
              { step: '1', label: 'Image Upload', desc: 'Citizen uploads photo', color: 'bg-cyan-500' },
              { step: '2', label: 'OpenCV Pre-process', desc: 'Resize & normalize', color: 'bg-blue-500' },
              { step: '3', label: 'YOLO Inference', desc: 'Detect & classify', color: 'bg-purple-500' },
              { step: '4', label: 'BBox Annotation', desc: 'Draw labeled boxes', color: 'bg-indigo-500' },
              { step: '5', label: 'Priority Score', desc: 'Multi-factor formula', color: 'bg-amber-500' },
              { step: '6', label: 'Dup. Detection', desc: 'Haversine cluster', color: 'bg-orange-500' },
              { step: '7', label: 'Dept. Routing', desc: 'Auto-assign dept.', color: 'bg-emerald-500' },
            ].map((s, i, arr) => (
              <React.Fragment key={s.step}>
                <div className="shrink-0 text-center">
                  <div className={`w-10 h-10 rounded-full ${s.color} flex items-center justify-center text-white font-bold text-sm mx-auto mb-2`}>{s.step}</div>
                  <div className="text-[11px] font-medium text-slate-200 w-20">{s.label}</div>
                  <div className="text-[10px] text-slate-500">{s.desc}</div>
                </div>
                {i < arr.length - 1 && <div className="h-0.5 w-8 bg-civic-border shrink-0 mt-5" />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  );
};
