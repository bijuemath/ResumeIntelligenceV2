import React from 'react';
import { Linkedin, History, AlertCircle, User, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

const Dashboard = () => {
    const [stats, setStats] = React.useState<any>(null);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        const fetchStats = async () => {
            try {
                // In a real app, use an Axios instance with interceptors for auth headers
                const token = localStorage.getItem('token') || 'mock-token-123';
                const response = await fetch('http://localhost:8000/api/dashboard/stats', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setStats(data);
                }
            } catch (error) {
                console.error("Failed to fetch dashboard stats", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            {/* Hero Section */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
                <div className="relative z-10">
                    <h2 className="text-3xl font-bold mb-2">Elevate Your Profile.</h2>
                    <p className="opacity-90 max-w-md">Our AI engine has analyzed {stats?.total_resumes || 0} documents in your private corpus.</p>
                    <div className="mt-6 flex gap-3">
                        <button className="bg-white text-blue-700 px-6 py-2 rounded-lg font-semibold flex items-center gap-2 hover:bg-slate-100 transition-all shadow-lg active:scale-95">
                            <Linkedin size={18} /> Sync LinkedIn
                        </button>
                        <button className="bg-blue-800/30 text-white border border-white/20 px-6 py-2 rounded-lg font-semibold flex items-center gap-2 hover:bg-blue-800/50 transition-all active:scale-95">
                            View Analysis <ArrowRight size={18} />
                        </button>
                    </div>
                </div>
                <div className="absolute right-[-20px] top-[-20px] opacity-10">
                    <User size={240} />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Recent Applications / Activity */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <History size={20} className="text-blue-600" /> Recent Activity
                    </h3>
                    <div className="space-y-4">
                        {loading ? (
                            <p className="text-sm text-slate-400">Loading activity...</p>
                        ) : stats?.recent_activity?.length > 0 ? (
                            stats.recent_activity.map((activity: any, i: number) => (
                                <div key={i} className="flex justify-between items-center p-3 hover:bg-slate-50 rounded-lg border border-transparent hover:border-slate-200 transition-all cursor-pointer group">
                                    <div>
                                        <p className="text-sm font-bold group-hover:text-blue-600 transition-colors uppercase text-xs tracking-wider">{activity.type}</p>
                                        <p className="text-xs text-slate-500 truncate max-w-[200px]">{activity.filename}</p>
                                    </div>
                                    <span className="bg-blue-100 text-blue-700 text-[10px] px-2 py-1 rounded-full font-bold uppercase">
                                        {new Date(activity.timestamp).toLocaleDateString()}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-slate-400 italic">No recent activity found. Upload a resume to get started.</p>
                        )}
                    </div>
                </div>

                {/* Optimization Alerts */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <AlertCircle size={20} className="text-amber-500" /> Optimization Alerts
                    </h3>
                    <div className="p-4 bg-amber-50 rounded-lg border-l-4 border-amber-400 text-sm text-amber-800">
                        "Consider adding <strong>GraphQL</strong> to your skills list. It appears in 40% of the roles you're targeting."
                    </div>
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-400 text-sm text-blue-800">
                        <strong>Resume Tip:</strong> Your summary could be more impactful. Try our <span className="underline font-bold cursor-pointer">AI Refiner</span>.
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
