import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { Lock, User, Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await api.post('/auth/login', { username, password });
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
            navigate('/');
        } catch (err) {
            setError('Invalid credentials. Hint: recruit / admin123');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#f8fafc] px-4 relative overflow-hidden">
            {/* Abstract Background Elements */}
            <div className="absolute top-0 -left-1/4 w-full h-full bg-primary-500/5 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-0 -right-1/4 w-1/2 h-1/2 bg-blue-500/5 blur-[120px] rounded-full pointer-events-none" />

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="glass-card max-w-md w-full p-10 relative z-10 border-slate-100 bg-white/80 shadow-2xl shadow-slate-200/50"
            >
                <div className="flex justify-center mb-8">
                    <div className="w-20 h-20 bg-primary-50 rounded-3xl flex items-center justify-center border border-primary-100 shadow-sm relative group overflow-hidden">
                        <div className="absolute inset-0 bg-primary-500/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                        <Terminal className="text-primary-600 w-10 h-10 relative z-10" />
                    </div>
                </div>

                <div className="text-center mb-10">
                    <h1 className="text-3xl font-black text-slate-900 tracking-tighter mb-2">Resume Intelligence</h1>
                    <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">Strategic Talent Acquisition Hub</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="space-y-2">
                        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Username</label>
                        <div className="relative group">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-primary-500 transition-colors" />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-white border border-slate-200 rounded-xl py-3.5 pl-12 pr-4 focus:border-primary-500 outline-none transition-all shadow-sm focus:ring-4 focus:ring-primary-500/5 text-slate-800 placeholder:text-slate-300 font-medium"
                                placeholder="recruit"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Password</label>
                        <div className="relative group">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-primary-500 transition-colors" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-white border border-slate-200 rounded-xl py-3.5 pl-12 pr-4 focus:border-primary-500 outline-none transition-all shadow-sm focus:ring-4 focus:ring-primary-500/5 text-slate-800 placeholder:text-slate-300 font-medium"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    {error && (
                        <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-2 text-red-500 text-xs font-bold bg-red-50 p-3 rounded-lg border border-red-100">
                            <Lock className="w-3.5" /> {error}
                        </motion.div>
                    )}

                    <button
                        type="submit"
                        className="w-full bg-slate-900 hover:bg-slate-800 text-white font-black uppercase tracking-widest text-sm py-4 rounded-xl mt-6 shadow-xl shadow-slate-200 transition-all transform active:scale-[0.97]"
                    >
                        Authenticate Access
                    </button>
                </form>

                <div className="mt-10 pt-8 border-t border-slate-100 text-center">
                    <p className="text-slate-400 text-xs font-medium">Restricted system for authorized recruiters only.</p>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
