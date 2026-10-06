import React from 'react';
import { Link } from 'react-router-dom';
import { Cpu, MapPin, ShieldCheck, ArrowRight, Zap, Layers, Eye, BarChart3 } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } };

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-civic-bg text-slate-100 flex flex-col">
      {/* Hero */}
      <section className="relative pt-24 pb-32 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-20%,rgba(6,182,212,0.12),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_80%_80%,rgba(16,185,129,0.06),transparent)]" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial="hidden" animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.12 } } }}
            className="text-center max-w-3xl mx-auto space-y-6"
          >
            <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono tracking-wide">
              <Zap className="w-3.5 h-3.5" /> INTELLIGENT CIVIC INFRASTRUCTURE
            </motion.div>

            <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]">
              <span className="bg-gradient-to-r from-white via-slate-100 to-cyan-400 bg-clip-text text-transparent">
                AI-Powered Civic Issue Detection & Resolution
              </span>
            </motion.h1>

            <motion.p variants={fadeUp} className="text-lg text-slate-400 leading-relaxed max-w-2xl mx-auto">
              CivicVision AI uses computer vision to detect potholes, open manholes, waterlogging, and urban defects. Automated priority scoring, spatial duplicate detection, and intelligent department dispatching.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-4 pt-4">
              <Link to="/report" className="group px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 shadow-lg shadow-cyan-500/25 flex items-center gap-2 transition-all">
                Report an Issue <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link to="/map" className="px-6 py-3 rounded-xl font-semibold bg-civic-card hover:bg-slate-800 text-slate-200 border border-civic-border flex items-center gap-2 transition-all">
                <MapPin className="w-4 h-4 text-cyan-400" /> Explore Map
              </Link>
            </motion.div>
          </motion.div>

          {/* Feature Grid */}
          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }}
            variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
            className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            {[
              { icon: Cpu, title: 'AI Vision Detection', desc: 'YOLO & OpenCV automatically detect 6 infrastructure defect classes with bounding box localization and confidence scoring.', color: 'cyan' },
              { icon: ShieldCheck, title: 'Priority Scoring Engine', desc: 'Multi-factor 0-100 scoring algorithm incorporating defect risk, AI confidence, area ratio, duplicate clustering, and aging hours.', color: 'emerald' },
              { icon: Layers, title: 'Haversine Duplicate Detection', desc: '50m radius spatial matching with 72h temporal window eliminates ticket clutter while escalating duplicate urgency.', color: 'purple' },
            ].map((feat, idx) => (
              <motion.div key={idx} variants={fadeUp}
                className="group bg-civic-card/60 backdrop-blur-sm p-7 rounded-2xl border border-civic-border hover:border-cyan-500/20 transition-all duration-300"
              >
                <div className={`w-11 h-11 rounded-xl bg-${feat.color}-500/10 flex items-center justify-center text-${feat.color}-400 mb-5 group-hover:scale-110 transition-transform`}>
                  <feat.icon className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feat.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{feat.desc}</p>
              </motion.div>
            ))}
          </motion.div>

          {/* Detection Classes */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-16 bg-civic-card/40 backdrop-blur-sm p-8 rounded-2xl border border-civic-border"
          >
            <h3 className="text-center text-sm font-mono text-slate-400 mb-6 uppercase tracking-wider">
              Detection Target Classes
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {['Pothole', 'Garbage Accumulation', 'Waterlogging', 'Broken Streetlight', 'Open Manhole', 'Road Damage'].map((cls, idx) => (
                <motion.div
                  key={idx}
                  whileHover={{ scale: 1.03 }}
                  className="bg-civic-bg px-3 py-3 rounded-xl border border-civic-border text-center text-xs font-medium text-cyan-300/80 hover:border-cyan-500/30 transition-all"
                >
                  {cls}
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Stats row */}
          <motion.div
            initial="hidden" whileInView="visible" viewport={{ once: true }}
            variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {[
              { label: 'Detection Classes', value: '6', suffix: 'types' },
              { label: 'Confidence Threshold', value: '85', suffix: '%+' },
              { label: 'Duplicate Radius', value: '50', suffix: 'm' },
              { label: 'Priority Factors', value: '5', suffix: 'weights' },
            ].map((stat, idx) => (
              <motion.div key={idx} variants={fadeUp}
                className="bg-civic-card/40 backdrop-blur-sm p-5 rounded-xl border border-civic-border text-center"
              >
                <div className="text-2xl font-bold text-white font-mono">{stat.value}<span className="text-xs text-cyan-400 ml-1">{stat.suffix}</span></div>
                <div className="text-[11px] text-slate-500 mt-1">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    </div>
  );
};
