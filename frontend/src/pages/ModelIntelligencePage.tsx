import React, { useState, useEffect } from 'react';
import { Brain, Target, Database, GitMerge, AlertCircle, CheckCircle, XCircle, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { mlService } from '../services/api';

export const ModelIntelligencePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'datasets' | 'pipeline'>('overview');
  const [datasets, setDatasets] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [dsData, modData] = await Promise.all([
          mlService.getLabDatasets(),
          mlService.getLabModels()
        ]);
        
        setDatasets(dsData);
        setModels(modData);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || "Failed to fetch lab data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);


  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-mono tracking-wider mb-2">
          <Brain className="w-3 h-3" /> ML MODEL LAB
        </div>
        <h1 className="text-2xl font-bold text-white">Model Intelligence & Integration Lab</h1>
        <p className="text-sm text-slate-400 mt-0.5">Manage datasets, track dependencies, and prepare tabular models for manual training.</p>
      </motion.div>

      {/* Tabs */}
      <div className="flex border-b border-civic-border overflow-x-auto">
        <button onClick={() => setActiveTab('overview')} className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === 'overview' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
          <Target className="w-4 h-4 inline-block mr-2" /> Model Overview
        </button>
        <button onClick={() => setActiveTab('datasets')} className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === 'datasets' ? 'border-cyan-500 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
          <Database className="w-4 h-4 inline-block mr-2" /> Dataset Explorer
        </button>
        <button onClick={() => setActiveTab('pipeline')} className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === 'pipeline' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
          <GitMerge className="w-4 h-4 inline-block mr-2" /> Dependency Pipeline
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400">Loading lab data...</div>
      ) : error ? (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" /> {error}
        </div>
      ) : (
        <div className="mt-6">
          
          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {models.map((m) => (
                <div key={m.id} className="bg-civic-card border border-civic-border rounded-xl p-5 hover:border-slate-600 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-bold text-white">{m.name}</h3>
                    <span className={`px-2 py-1 rounded text-[10px] font-mono uppercase border ${
                      m.readiness === 'TRAINED_AND_AVAILABLE' || m.training_status === 'TRAINED'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : 'bg-red-500/10 text-red-400 border-red-500/20'
                    }`}>
                      {m.readiness}
                    </span>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Task</span>
                      <span className="text-slate-300 text-right">{m.task}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Target</span>
                      <span className="text-slate-300 font-mono text-xs">{m.target_variable}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Dataset</span>
                      <span className="text-amber-400 text-xs font-mono">{m.compatible_dataset}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Status</span>
                      <span className={`text-xs font-mono font-semibold ${m.training_status === 'TRAINED' ? 'text-emerald-400' : 'text-slate-400'}`}>{m.training_status}</span>
                    </div>

                    {/* Verified Metrics Display if available */}
                    {m.metrics && (
                      <div className="pt-2 border-t border-civic-border">
                        <span className="text-xs text-slate-400 font-medium block mb-1.5">Verified Evaluation Metrics:</span>
                        <div className="grid grid-cols-3 gap-2">
                          <div className="bg-civic-bg p-2 rounded border border-civic-border text-center">
                            <span className="text-[10px] text-slate-500 uppercase block">MAE</span>
                            <span className="text-xs font-mono text-emerald-400 font-bold">{typeof m.metrics.MAE === 'number' ? m.metrics.MAE.toFixed(4) : m.metrics.MAE}</span>
                          </div>
                          <div className="bg-civic-bg p-2 rounded border border-civic-border text-center">
                            <span className="text-[10px] text-slate-500 uppercase block">RMSE</span>
                            <span className="text-xs font-mono text-emerald-400 font-bold">{typeof m.metrics.RMSE === 'number' ? m.metrics.RMSE.toFixed(4) : m.metrics.RMSE}</span>
                          </div>
                          <div className="bg-civic-bg p-2 rounded border border-civic-border text-center">
                            <span className="text-[10px] text-slate-500 uppercase block">R² Score</span>
                            <span className="text-xs font-mono text-emerald-400 font-bold">{typeof m.metrics.R2 === 'number' ? m.metrics.R2.toFixed(4) : m.metrics.R2}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 pt-4 border-t border-civic-border">
                    <p className="text-xs text-slate-400 font-medium mb-2">Required Features:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {m.features.map((f: string) => <span key={f} className="px-2 py-0.5 bg-civic-bg border border-civic-border rounded text-[10px] text-slate-300">{f}</span>)}
                    </div>
                  </div>
                  <div className={`mt-4 p-3 rounded-lg border ${
                    m.training_status === 'TRAINED'
                      ? 'bg-emerald-500/5 border-emerald-500/20'
                      : 'bg-red-500/5 border-red-500/20'
                  }`}>
                    <div className={`text-[10px] uppercase font-bold mb-1 flex items-center gap-1 ${
                      m.training_status === 'TRAINED' ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {m.training_status === 'TRAINED' ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                      {m.training_status === 'TRAINED' ? 'Verified Status' : 'Action Required'}
                    </div>
                    <p className="text-xs text-slate-300">{m.next_action}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* DATASETS TAB */}
          {activeTab === 'datasets' && (
            <div className="space-y-6">
              {datasets.map((d) => (
                <div key={d.id} className="bg-civic-card border border-civic-border rounded-xl p-5">
                  <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-bold text-white">{d.name}</h3>
                        {d.is_synthetic && <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded text-[10px] font-mono">SYNTHETIC</span>}
                      </div>
                      <p className="text-xs text-slate-400">{d.source} • {d.coverage}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-[10px] font-mono uppercase ${d.compatibility === 'INCOMPATIBLE' || d.compatibility === 'BLOCKED' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                        {d.compatibility}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="p-3 bg-civic-bg rounded-lg border border-civic-border">
                      <div className="text-[10px] text-slate-500 uppercase mb-1">Rows</div>
                      <div className="text-sm font-mono text-white">{d.row_count.toLocaleString()}</div>
                    </div>
                    <div className="p-3 bg-civic-bg rounded-lg border border-civic-border">
                      <div className="text-[10px] text-slate-500 uppercase mb-1">Target</div>
                      <div className="text-sm font-mono text-white">{d.target}</div>
                    </div>
                    <div className="p-3 bg-civic-bg rounded-lg border border-civic-border">
                      <div className="text-[10px] text-slate-500 uppercase mb-1">Status</div>
                      <div className="text-sm font-mono text-white">{d.status}</div>
                    </div>
                    <div className="p-3 bg-civic-bg rounded-lg border border-civic-border">
                      <div className="text-[10px] text-slate-500 uppercase mb-1">License</div>
                      <div className="text-sm font-mono text-white truncate" title={d.license}>{d.license}</div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <span className="text-xs text-slate-500 block mb-1">Columns:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {d.columns.length > 0 ? d.columns.map((c: string) => <span key={c} className="px-2 py-0.5 bg-slate-800 rounded text-[10px] text-slate-300">{c}</span>) : <span className="text-xs text-slate-600">No columns defined</span>}
                      </div>
                    </div>
                    <div className="p-3 bg-red-500/5 border border-red-500/10 rounded-lg">
                      <span className="text-[10px] text-red-400 uppercase font-bold block mb-1">Limitations / Blockers</span>
                      <p className="text-xs text-slate-300 leading-relaxed">{d.limitations}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* PIPELINE TAB */}
          {activeTab === 'pipeline' && (
            <div className="bg-civic-card border border-civic-border rounded-xl p-8 text-center space-y-6">
               <div className="max-w-2xl mx-auto space-y-8">
                  <div className="p-4 border border-emerald-500/20 bg-emerald-500/5 rounded-xl">
                    <h4 className="text-emerald-400 font-bold mb-1 flex justify-center items-center gap-2"><CheckCircle className="w-4 h-4"/> YOLOv8 (Image Inference)</h4>
                    <p className="text-xs text-slate-400">Status: TRAINED. Detects damage severity and bounding boxes natively.</p>
                  </div>
                  
                  <div className="w-0.5 h-8 bg-slate-700 mx-auto"></div>

                  <div className="p-4 border border-red-500/20 bg-red-500/5 rounded-xl">
                    <h4 className="text-red-400 font-bold mb-1 flex justify-center items-center gap-2"><XCircle className="w-4 h-4"/> Tabular Models (RF, DT, LR, GB)</h4>
                    <p className="text-xs text-slate-400">Status: BLOCKED. Awaiting genuine Indian road condition dataset (PCI/AADT) procurement.</p>
                  </div>

                  <div className="w-0.5 h-8 bg-slate-700 mx-auto"></div>

                  <div className="p-4 border border-amber-500/20 bg-amber-500/5 rounded-xl">
                    <h4 className="text-amber-400 font-bold mb-1 flex justify-center items-center gap-2"><AlertCircle className="w-4 h-4"/> Downstream Prioritization</h4>
                    <p className="text-xs text-slate-400">Status: BLOCKED. Cannot generate synthetic priority outputs without valid upstream tabular inputs. Wait for dataset procurement.</p>
                  </div>
               </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
};

