import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Users,
    FileCheck,
    AlertCircle,
    CheckCircle2,
    ArrowUpRight,
    Loader2
} from 'lucide-react';
import api from '../api';

const StatCard = ({ title, value, icon: Icon, color, trend }: any) => (
    <div className="glass-card p-6 p-relative group hover:border-primary-200 transition-all hover:shadow-md">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-xl bg-${color}-50 border border-${color}-100`}>
                <Icon className={`text-${color}-600 w-6 h-6`} />
            </div>
            <button className="text-slate-300 hover:text-primary-500 transition-colors">
                <ArrowUpRight className="w-5 h-5" />
            </button>
        </div>
        <div>
            <h3 className="text-slate-500 text-sm font-semibold mb-1 uppercase tracking-tight">{title}</h3>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900">{value}</span>
                {trend && <span className="text-emerald-600 text-xs font-bold bg-emerald-50 px-1.5 py-0.5 rounded">{trend}</span>}
            </div>
        </div>
    </div>
);

const Dashboard = () => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await api.get('/dashboard/stats');
                setStats(response.data);
            } catch (err) {
                console.error("Failed to fetch dashboard stats", err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <header>
                <h1 className="text-3xl font-bold mb-2 text-slate-900 tracking-tight">Welcome back, {user.name?.split(' ')[0] || 'User'}</h1>
                <p className="text-slate-500 font-medium">Here's what's happening with your recruitment pipeline today.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Resumes" value={stats?.total_resumes || 0} icon={Users} color="primary" trend="+12% this week" />
                <StatCard title="Auto Screened" value={stats?.auto_screened || 0} icon={FileCheck} color="emerald" trend="+5%" />
                <StatCard title="High Match" value={stats?.high_matches || 0} icon={CheckCircle2} color="blue" />
                <StatCard title="Skill Gaps" value={stats?.skill_gaps || 0} icon={AlertCircle} color="amber" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 glass-card p-8">
                    <h2 className="text-xl font-bold mb-6 text-slate-800">Recent Activity</h2>
                    <div className="space-y-6">
                        {stats?.recent_activity?.length > 0 ? (
                            stats.recent_activity.map((activity: any, i: number) => (
                                <div key={i} className="flex gap-4 items-start pb-6 border-b border-slate-100 last:border-0 last:pb-0">
                                    <div className="w-10 h-10 rounded-full bg-slate-100 flex-shrink-0 border border-slate-200 flex items-center justify-center text-slate-400 font-bold">
                                        {activity.filename[0]}
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-semibold text-slate-700">
                                            {activity.type === 'screen' ? 'Candidate' : 'Analysis for'} <span className="text-primary-600">{activity.filename}</span> was {activity.type === 'screen' ? 'auto-screened' : activity.type}
                                        </p>
                                        <p className="text-xs text-slate-500 mt-1 font-medium">
                                            {new Date(activity.timestamp).toLocaleTimeString()} • Overall Score: {activity.score}%
                                        </p>
                                    </div>
                                    {activity.type === 'screen' && (
                                        <div className={`${activity.decision === 'SELECTED' ? 'text-emerald-600 bg-emerald-50 border-emerald-100' : 'text-red-600 bg-red-50 border-red-100'} text-[10px] font-black tracking-widest px-2 py-1 border rounded underline decoration-2 underline-offset-2`}>
                                            {activity.decision}
                                        </div>
                                    )}
                                </div>
                            ))
                        ) : (
                            <p className="text-slate-400 text-center py-12">No recent activity found.</p>
                        )}
                    </div>
                </div>

                <div className="glass-card p-8">
                    <h2 className="text-xl font-bold mb-6 text-slate-800">Upcoming Actions</h2>
                    <div className="space-y-4">
                        <div className="p-4 bg-white rounded-lg border border-slate-200 border-l-primary-500 border-l-4 shadow-sm">
                            <p className="text-sm font-bold text-slate-800">Review Skill Analysis</p>
                            <p className="text-xs text-slate-500 mt-1 font-medium">Java Developer position</p>
                        </div>
                        <div className="p-4 bg-white rounded-lg border border-slate-200 border-l-amber-500 border-l-4 shadow-sm">
                            <p className="text-sm font-bold text-slate-800">Generate New Batch</p>
                            <p className="text-xs text-slate-500 mt-1 font-medium">Product Design roles</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
