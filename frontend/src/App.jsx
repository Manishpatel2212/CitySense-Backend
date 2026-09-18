import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Bus,
  MapPin,
  AlertTriangle,
  BarChart3,
  Bell,
  FileText,
  Settings,
  Cpu,
  CheckCircle2,
  Users,
  Filter,
  Download,
  Sun,
  Moon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ProfessionalMapView from './components/ProfessionalMapView';

export default function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [sidebarTheme, setSidebarTheme] = useState('light');
  const [potholes, setPotholes] = useState([]);
  const [potholesLoading, setPotholesLoading] = useState(true);
  const [potholesError, setPotholesError] = useState('');

  useEffect(() => {
    const controller = new AbortController();

    fetch('http://localhost:5000/api/confirmed-potholes', { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        setPotholes(data.confirmedPotholes || []);
        setPotholesError('');
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setPotholesError('Unable to load confirmed potholes.');
        }
      })
      .finally(() => setPotholesLoading(false));

    return () => controller.abort();
  }, []);

  const formatPercentage = (value) => `${(Number(value || 0) * 100).toFixed(1)}%`;
  const firstPothole = potholes[0];

  // Dynamic View Renderer Based on Active Navigation Tab
  const renderMainContent = () => {
    switch (activeTab) {
      case 'Dashboard':
        return (
          <div className="space-y-6">
            {/* Top 4 Metric Cards */}
            <div className="grid grid-cols-4 gap-5">
              {[
                { title: 'Active Buses', count: '48', sub: '↑ 6% from yesterday', color: 'bg-[#00A3FF]', icon: Bus },
                { title: 'Road Defects Detected', count: potholesLoading ? '...' : potholes.length, sub: 'Confirmed potholes', color: 'bg-purple-600', icon: AlertTriangle },
                { title: 'Traffic Congestion Zones', count: '5', sub: '↑ 2 new today', color: 'bg-orange-500', icon: Bus },
                { title: 'Pedestrian Risk Areas', count: '3', sub: '↑ 1 new today', color: 'bg-emerald-500', icon: Users }
              ].map((card, i) => {
                const Icon = card.icon;
                return (
                  <motion.div
                    key={i}
                    whileHover={{ y: -3 }}
                    className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-4"
                  >
                    <div className={`w-12 h-12 rounded-2xl ${card.color} text-white flex items-center justify-center shrink-0 shadow-md`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <span className="text-xs font-medium text-gray-400 block">{card.title}</span>
                      <span className="text-2xl font-bold text-gray-900 leading-tight block">{card.count}</span>
                      <span className="text-[11px] text-gray-400 font-medium">{card.sub}</span>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Central Main Workspace Layout */}
            <div className="grid grid-cols-3 gap-6">
              {/* Central Map Section */}
              <div className="col-span-2">
                <ProfessionalMapView potholes={potholes} loading={potholesLoading} error={potholesError} />
              </div>

              {/* Right Panel AI Alerts & System Status */}
              <div className="space-y-6">
                {/* Priority AI Alerts Box */}
                <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bell className="w-4 h-4 text-[#00A3FF]" />
                      <h2 className="font-bold text-gray-900 text-sm">Priority AI Alerts</h2>
                    </div>
                    <button onClick={() => setActiveTab('AI Alerts')} className="text-[11px] text-[#00A3FF] font-semibold hover:underline">
                      View All &gt;
                    </button>
                  </div>

                  <div className="space-y-3">
                    {[
                      ...(firstPothole ? [{ type: 'Road Defect Detected', desc: `${firstPothole.severity} pothole at ${firstPothole.location.latitude.toFixed(4)}, ${firstPothole.location.longitude.toFixed(4)}`, time: 'Live', level: firstPothole.severity, badge: 'bg-red-50 text-red-600 border-red-200' }] : []),
                      { type: 'Heavy Traffic Congestion', desc: 'Vijay Nagar Square to Palasia Junction', time: '11:15 AM', level: 'High', badge: 'bg-red-50 text-red-600 border-red-200' },
                      { type: 'Pedestrian Risk', desc: 'School crossing zone - Near Green Park', time: '10:52 AM', level: 'Medium', badge: 'bg-amber-50 text-amber-600 border-amber-200' },
                    ].map((alert, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-gray-50 border border-gray-100 flex items-start justify-between gap-3">
                        <div>
                          <p className="text-xs font-bold text-gray-900">{alert.type}</p>
                          <p className="text-[11px] text-gray-500">{alert.desc}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-[10px] text-gray-400 block mb-1">{alert.time}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${alert.badge}`}>
                            {alert.level}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Live System Operational Status Box */}
                <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-gray-100 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                      <h3 className="font-bold text-gray-900 text-xs">Live System Status</h3>
                    </div>
                    <span className="text-[10px] text-emerald-600 font-medium">All Systems Operational</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div className="p-2.5 rounded-xl bg-gray-50 border border-gray-100">
                      <span className="text-[10px] text-gray-400 block">Fleet Tracking</span>
                      <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Online
                      </span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-gray-50 border border-gray-100">
                      <span className="text-[10px] text-gray-400 block">AI Analysis</span>
                      <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                        <Cpu className="w-3 h-3" /> Online
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'City Intelligence Map':
      case 'Live Fleet':
        return (
          <div className="h-[calc(100vh-140px)] w-full">
            <ProfessionalMapView potholes={potholes} loading={potholesLoading} error={potholesError} />
          </div>
        );

      case 'Traffic Analytics':
        return (
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm space-y-6">
            <h2 className="text-lg font-bold text-gray-900">Traffic Analytics & Route Optimization</h2>
            <div className="grid grid-cols-3 gap-5">
              <div className="p-5 bg-sky-50 rounded-2xl border border-sky-100">
                <span className="text-xs text-sky-700 font-semibold">Average Fleet Speed</span>
                <p className="text-3xl font-extrabold text-sky-900 mt-2">34.2 km/h</p>
                <span className="text-[11px] text-sky-600">Optimal traffic flow speed</span>
              </div>
              <div className="p-5 bg-purple-50 rounded-2xl border border-purple-100">
                <span className="text-xs text-purple-700 font-semibold">Peak Delay Period</span>
                <p className="text-3xl font-extrabold text-purple-900 mt-2">09:15 AM</p>
                <span className="text-[11px] text-purple-600">Palasia to Vijay Nagar</span>
              </div>
              <div className="p-5 bg-emerald-50 rounded-2xl border border-emerald-100">
                <span className="text-xs text-emerald-700 font-semibold">Fleet On-Time Rate</span>
                <p className="text-3xl font-extrabold text-emerald-900 mt-2">94.8%</p>
                <span className="text-[11px] text-emerald-600">↑ 2.1% improvement</span>
              </div>
            </div>
          </div>
        );

      case 'Road Defects':
      case 'AI Alerts':
        return (
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm space-y-5">
            <div className="flex justify-between items-center border-b border-gray-100 pb-4">
              <h2 className="text-lg font-bold text-gray-900">Detected Road Defects & AI Incidents Log</h2>
              <button className="flex items-center gap-2 px-3 py-1.5 border border-gray-200 rounded-xl text-xs font-semibold text-gray-600 hover:bg-gray-50">
                <Filter className="w-3.5 h-3.5" /> Filter Incidents
              </button>
            </div>
            <div className="space-y-3">
              {potholesLoading ? <p className="text-sm text-gray-500">Loading confirmed potholes...</p> : potholesError ? <p className="text-sm text-red-600">{potholesError}</p> : potholes.length === 0 ? <p className="text-sm text-gray-500">No confirmed potholes found.</p> : potholes.map((pothole) => {
                const item = {
                  id: pothole.potholeId,
                  title: `${pothole.severity} Pothole`,
                  loc: `${pothole.location.latitude.toFixed(5)}, ${pothole.location.longitude.toFixed(5)}`,
                  conf: formatPercentage(pothole.averageConfidence),
                  severity: pothole.severity,
                  status: pothole.status,
                  buses: pothole.uniqueBusCount,
                  confirmation: `${pothole.confirmationPercentage}%`
                };
                return (
                <div key={item.id} className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-[#00A3FF]">{item.id}</span>
                    <h3 className="text-sm font-bold text-gray-900">{item.title}</h3>
                    <p className="text-xs text-gray-500">{item.loc} • AI Confidence: {item.conf} • Buses: {item.buses} • Confirmation: {item.confirmation}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-3 py-1 rounded-full font-bold bg-red-100 text-red-700 border border-red-200">
                      {item.severity}
                    </span>
                    <span className="text-xs font-semibold text-gray-600 bg-white px-3 py-1 rounded-lg border border-gray-200">
                      {item.status}
                    </span>
                  </div>
                </div>
                );
              })}
            </div>
          </div>
        );

      case 'Reports':
        return (
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Generated Audits & Automated Reports</h2>
            <div className="space-y-3">
              {[
                'Daily Municipal Road Infrastructure Damage Report - Sep 18',
                'Smart Public Transport Route Delay & Congestion Audit',
                'Edge AI Camera Detection Accuracy & Sensor Log'
              ].map((report, idx) => (
                <div key={idx} className="p-4 border border-gray-100 rounded-xl flex justify-between items-center hover:bg-gray-50 cursor-pointer">
                  <span className="text-xs font-bold text-gray-800">{report}</span>
                  <button className="flex items-center gap-1.5 text-xs text-[#00A3FF] font-semibold hover:underline">
                    <Download className="w-3.5 h-3.5" /> Export PDF
                  </button>
                </div>
              ))}
            </div>
          </div>
        );

      case 'Settings':
        return (
          <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm space-y-5 max-w-2xl">
            <h2 className="text-lg font-bold text-gray-900">System Preferences & Notification Thresholds</h2>
            <div className="space-y-4 text-xs font-semibold text-gray-700">
              <label className="flex items-center justify-between p-4 border rounded-xl bg-gray-50">
                <div>
                  <p className="text-sm font-bold text-gray-900">Real-Time Audio Alerts</p>
                  <p className="text-gray-500 text-[11px] font-normal">Play notification sound when High-Priority defect is detected</p>
                </div>
                <input type="checkbox" className="w-4 h-4 accent-[#00A3FF]" defaultChecked />
              </label>
              <label className="flex items-center justify-between p-4 border rounded-xl bg-gray-50">
                <div>
                  <p className="text-sm font-bold text-gray-900">Automated Dispatch System</p>
                  <p className="text-gray-500 text-[11px] font-normal">Send high-confidence alerts directly to Municipal Command</p>
                </div>
                <input type="checkbox" className="w-4 h-4 accent-[#00A3FF]" defaultChecked />
              </label>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#F4F6FA] text-gray-800 font-sans overflow-hidden">
      {/* Navigation Sidebar */}
      <aside className="w-64 bg-[#0B132B] text-gray-300 flex flex-col justify-between p-4 shrink-0">
        <div>
          {/* Brand Logo Header */}
          <div className="flex items-center gap-3 px-2 py-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#00A3FF] to-sky-400 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-[#00A3FF]/30">
              C
            </div>
            <div>
              <h1 className={`font-bold text-lg leading-tight ${sidebarTheme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                CitySense
              </h1>
              <p className="text-[11px] text-gray-400">Smarter Cities, Safer Journeys</p>
            </div>
          </div>

          <div className="px-3 mb-2 text-[10px] font-bold uppercase tracking-wider text-gray-400">
            Navigation
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {[
              { name: 'Dashboard', icon: LayoutDashboard },
              { name: 'City Intelligence Map', icon: MapPin },
              { name: 'Traffic Analytics', icon: BarChart3 },
              { name: 'AI Alerts', icon: Bell },
              { name: 'Reports', icon: FileText },
              { name: 'Settings', icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.name;
              return (
                <button
                  key={item.name}
                  onClick={() => setActiveTab(item.name)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${isActive
                    ? 'bg-[#00A3FF] text-white shadow-lg shadow-[#00A3FF]/30 font-semibold'
                    : sidebarTheme === 'light'
                      ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/70'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-slate-800/80'
                    }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer: Fleet Status & Theme Switcher */}
        <div className={`space-y-3 pt-4 border-t ${sidebarTheme === 'light' ? 'border-gray-100' : 'border-slate-800'}`}>
          <div className={`p-3 rounded-xl border ${sidebarTheme === 'light'
            ? 'bg-gray-50 border-gray-100'
            : 'bg-slate-800/50 border-slate-700/60'
            } flex items-center gap-3`}>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <span className={`text-xs font-bold block ${sidebarTheme === 'light' ? 'text-gray-800' : 'text-slate-200'}`}>
                Fleet Active
              </span>
              <span className="text-[10px] text-gray-400">48 / 50 Connected</span>
            </div>
          </div>

          <button
            onClick={() => setSidebarTheme(sidebarTheme === 'light' ? 'dark' : 'light')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium border transition-colors ${sidebarTheme === 'light'
              ? 'bg-gray-50 border-gray-200/80 text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              : 'bg-slate-800/80 border-slate-700 text-gray-300 hover:text-white hover:bg-slate-700'
              }`}
          >
            <span className="flex items-center gap-2">
              {sidebarTheme === 'light' ? <Moon className="w-3.5 h-3.5 text-gray-500" /> : <Sun className="w-3.5 h-3.5 text-amber-400" />}
              {sidebarTheme === 'light' ? 'Dark Sidebar' : 'Light Sidebar'}
            </span>
            <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${sidebarTheme === 'light' ? 'bg-sky-100 text-sky-700' : 'bg-slate-700 text-cyan-300'
              }`}>
              {sidebarTheme}
            </span>
          </button>
        </div>
      </aside>

      {/* Main Right Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 bg-white border-b border-gray-200/80 px-8 flex items-center justify-between shrink-0 shadow-sm">
          <div className="text-sm font-medium text-gray-500">
            UrbanSense <span className="mx-2 text-gray-300">/</span> <span className="text-gray-900 font-semibold">{activeTab}</span>
          </div>

          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="text-gray-500">Fri, 18 Sep 2026</span>
            <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-full border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              System Online
            </div>
          </div>
        </header>

        {/* Dynamic Body Panel */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {renderMainContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}