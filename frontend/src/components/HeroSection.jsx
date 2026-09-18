import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Rocket, ArrowRight, Compass, Clock } from 'lucide-react';

export default function HeroSection() {
    const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date().toLocaleTimeString());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="relative w-full h-[600px] rounded-3xl overflow-hidden border border-slate-800 shadow-2xl flex flex-col justify-between p-8 text-white">
            {/* Background Video Layer */}
            <video
                autoPlay
                loop
                muted
                playsInline
                className="absolute inset-0 w-full h-full object-cover z-0 filter brightness-75"
            >
                <source
                    src="https://assets.mixkit.co/videos/preview/mixkit-stars-in-space-background-1610-large.mp4"
                    type="video/mp4"
                />
            </video>

            {/* Dark Gradient Overlay for Readability */}
            <div className="absolute inset-0 bg-gradient-to-r from-slate-950/90 via-slate-950/40 to-transparent z-10" />

            {/* Top Header Navigation Overlay */}
            <div className="relative z-20 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-400/30 backdrop-blur-md flex items-center justify-center text-cyan-400">
                        <Rocket className="w-5 h-5 animate-pulse" />
                    </div>
                    <span className="font-bold text-lg tracking-wider text-white">ORBITX</span>
                </div>

                <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300 backdrop-blur-md bg-white/5 px-6 py-2 rounded-full border border-white/10">
                    <a href="#missions" className="hover:text-cyan-400 transition-colors">Missions</a>
                    <a href="#spacecraft" className="hover:text-cyan-400 transition-colors">Fleet</a>
                    <a href="#telemetry" className="hover:text-cyan-400 transition-colors">Telemetry</a>
                    <a href="#about" className="hover:text-cyan-400 transition-colors">About</a>
                </nav>

                <div className="flex items-center gap-3">
                    <div className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/60 border border-cyan-500/30 text-cyan-300 text-xs font-mono backdrop-blur-md">
                        <Clock className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                        <span>{currentTime}</span>
                    </div>

                    <button className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-5 py-2.5 rounded-full shadow-lg shadow-cyan-500/20 transition-all text-sm">
                        Launch Portal
                    </button>
                </div>
            </div>

            {/* Hero Content Overlay */}
            <div className="relative z-20 max-w-xl my-auto space-y-6">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="inline-flex items-center gap-2 text-xs font-semibold px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-400/30 text-cyan-300"
                >
                    <Compass className="w-4 h-4 animate-spin" /> Next Gen Autonomous Navigation
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight"
                >
                    Explore Deep Space <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Real-Time</span> Fleet
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                    className="text-slate-300 text-sm leading-relaxed"
                >
                    AI-driven space telemetry, live orbit tracking, and atmospheric intelligence integrated into one centralized command dashboard.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.6 }}
                    className="flex items-center gap-4 pt-2"
                >
                    <button className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold px-6 py-3 rounded-xl shadow-lg shadow-cyan-500/25 transition-all text-sm">
                        Live Stream <ArrowRight className="w-4 h-4" />
                    </button>
                    <button className="px-6 py-3 rounded-xl font-semibold text-sm border border-slate-700 bg-slate-900/60 hover:bg-slate-800 backdrop-blur-md transition-all text-slate-200">
                        View Analytics
                    </button>
                </motion.div>
            </div>

            {/* Bottom Telemetry Mini Cards */}
            <div className="relative z-20 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-xl">
                {[
                    { label: 'Mission Time', value: currentTime },
                    { label: 'Orbital Speed', value: '27,600 km/h' },
                    { label: 'AI Latency', value: '1.2 ms' },
                    { label: 'Active Probes', value: '104 Units' },
                ].map((item, idx) => (
                    <div key={idx} className="bg-slate-950/60 backdrop-blur-md border border-white/10 p-3 rounded-2xl">
                        <span className="text-[10px] text-slate-400 font-medium block">{item.label}</span>
                        <span className="text-xs font-bold text-cyan-300 font-mono">{item.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
