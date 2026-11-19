import json
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

from config import WEB_DASHBOARD_PORT, DEFAULT_PASSWORD, DEFAULT_EMAIL_PREFIX
from database.db import Database
from core.morelogin import MoreLoginCreator, live_tracker

db = Database()
creator = MoreLoginCreator()

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoreLogin – Live Browser Automation & Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --card-bg: #111827;
            --card-border: #1f2937;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --browser-bar: #1e293b;
            --browser-bg: #0f172a;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text-main); padding: 18px; min-height: 100vh; }
        .container { max-width: 1440px; margin: 0 auto; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid var(--card-border); flex-wrap: wrap; gap: 12px; }
        .logo-area { display: flex; align-items: center; gap: 12px; }
        .logo-badge { background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 8px 14px; border-radius: 8px; font-weight: 700; font-size: 16px; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        .header-actions { display: flex; align-items: center; gap: 12px; }
        .status-pill { display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.12); color: var(--success); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500; border: 1px solid rgba(16, 185, 129, 0.25); }
        .pulse-dot { width: 8px; height: 8px; background-color: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }

        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-bottom: 22px; }
        .stat-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 16px; }
        .stat-label { color: var(--text-muted); font-size: 12px; font-weight: 500; margin-bottom: 4px; }
        .stat-val { font-size: 24px; font-weight: 700; color: var(--text-main); }
        .stat-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

        /* Main 2-Column Layout */
        .grid-layout { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; }
        @media (max-width: 1100px) { .grid-layout { grid-template-columns: 1fr; } }

        /* Browser Window Mockup */
        .browser-window {
            background: var(--browser-bg);
            border: 1px solid #334155;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            margin-bottom: 16px;
        }
        .window-titlebar {
            background: #0f172a;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #1e293b;
        }
        .window-controls { display: flex; gap: 8px; }
        .win-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .dot-close { background: #ef4444; }
        .dot-min { background: #f59e0b; }
        .dot-max { background: #10b981; }

        .browser-tabs { display: flex; gap: 6px; margin-left: 12px; flex: 1; }
        .tab-item {
            padding: 6px 14px;
            font-size: 12px;
            border-radius: 6px 6px 0 0;
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .tab-item.active { background: #1e293b; color: #fff; font-weight: 600; }

        .browser-nav-bar {
            background: #1e293b;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #334155;
        }
        .nav-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 14px; }
        .url-bar {
            flex: 1;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #93c5fd;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .ssl-lock { color: #10b981; font-size: 11px; }

        /* Browser Viewport */
        .browser-viewport {
            min-height: 380px;
            background: #0b1120;
            padding: 24px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* MoreLogin Form Mockup */
        .morelogin-card {
            width: 100%;
            max-width: 440px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }
        .ml-header { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
        .ml-logo { background: #3b82f6; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff; }
        .input-group { margin-bottom: 14px; text-align: left; }
        .input-label { display: block; font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; }
        .sim-input {
            width: 100%;
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 9px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: #fff;
            position: relative;
            min-height: 38px;
            display: flex;
            align-items: center;
        }
        .sim-input.focused { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .cursor-blink { display: inline-block; width: 2px; height: 16px; background: #3b82f6; animation: blink 1s infinite; margin-left: 2px; }
        @keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }

        .btn-register-sim {
            width: 100%;
            background: #3b82f6;
            color: #fff;
            border: none;
            padding: 10px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            margin-top: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-register-sim.clicked { background: #1d4ed8; transform: scale(0.98); }

        /* Müllfach Inbox Mockup */
        .muellfach-view {
            width: 100%;
            height: 100%;
            background: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
            padding: 18px;
            text-align: left;
        }
        .inbox-item {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 12px;
            margin-top: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .activate-btn-highlight {
            display: inline-block;
            background: #3b82f6;
            color: #fff;
            font-weight: 600;
            font-size: 12px;
            padding: 6px 14px;
            border-radius: 4px;
            text-decoration: none;
            animation: pulse-border 1.5s infinite;
        }
        @keyframes pulse-border {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
            70% { box-shadow: 0 0 0 8px rgba(59, 130, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        }

        /* Success Card */
        .success-overlay {
            width: 100%;
            max-width: 440px;
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid var(--success);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
        }
        .check-circle { width: 50px; height: 50px; background: var(--success); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 12px auto; }

        /* Terminal Console */
        .terminal-box {
            background: #050811;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 12px 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #94a3b8;
            max-height: 140px;
            overflow-y: auto;
            line-height: 1.6;
            margin-bottom: 14px;
        }
        .terminal-box span { color: #38bdf8; }

        /* Cards and Tables */
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 18px; margin-bottom: 20px; overflow: hidden; }
        .section-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }
        
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 12px; }
        th { padding: 10px 12px; color: var(--text-muted); border-bottom: 1px solid var(--card-border); font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; }
        td { padding: 10px 12px; border-bottom: 1px solid var(--card-border); vertical-align: middle; }
        tr:hover { background-color: rgba(255, 255, 255, 0.02); }

        .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
        .badge-click { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
        .badge-create { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .code-box { font-family: 'JetBrains Mono', monospace; background: rgba(0,0,0,0.3); padding: 3px 6px; border-radius: 4px; font-size: 11px; }

        .btn { background: var(--primary); color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 12px; cursor: pointer; transition: background 0.2s; display: inline-flex; align-items: center; gap: 6px; }
        .btn:hover { background: var(--primary-hover); }
        .btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-main); }
        .btn-outline:hover { background: rgba(255,255,255,0.05); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-area">
                <div class="logo-badge">⚡ MoreLogin</div>
                <div>
                    <h2>Realtime Automation & Control Center</h2>
                    <p style="color: var(--text-muted); font-size: 12px;">Live Browser Automation Preview & Telegram Bot Activity</p>
                </div>
            </div>
            <div class="header-actions">
                <div class="status-pill">
                    <span class="pulse-dot"></span>
                    <span>Live Tracking Active</span>
                </div>
                <button class="btn" id="btn_run_test" onclick="triggerWebAccountCreation()">▶️ Run Live Automation Demo</button>
            </div>
        </header>

        <!-- Stats Bar -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">👥 Total Bot Users</div>
                <div class="stat-val" id="total_users">-</div>
                <div class="stat-sub">Active Telegram users</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">⚡ Total MoreLogin Accounts</div>
                <div class="stat-val" id="total_accounts">-</div>
                <div class="stat-sub">Fully activated & verified</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">📅 Created Today</div>
                <div class="stat-val" id="today_accounts">-</div>
                <div class="stat-sub" id="today_clicks_sub">- button clicks</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">📡 Current Automation Step</div>
                <div class="stat-val" id="step_indicator" style="font-size: 18px; color: #60a5fa;">Ready</div>
                <div class="stat-sub" id="step_sub">Waiting for 1-click trigger</div>
            </div>
        </div>

        <!-- 2-Column Split: Browser on Left, Tables on Right -->
        <div class="grid-layout">
            <!-- Left: Windows Live Browser Window Tab -->
            <div>
                <div class="section-title">
                    <span>🖥️ Live Automation Browser Window</span>
                    <span id="live_status_tag" class="badge badge-click">● IDLE / READY</span>
                </div>

                <!-- Realistic Windows/Chrome Browser Window -->
                <div class="browser-window">
                    <div class="window-titlebar">
                        <div class="window-controls">
                            <span class="win-dot dot-close"></span>
                            <span class="win-dot dot-min"></span>
                            <span class="win-dot dot-max"></span>
                        </div>
                        <div class="browser-tabs">
                            <div class="tab-item" id="tab_morelogin">
                                <span>⚡</span> MoreLogin | Register
                            </div>
                            <div class="tab-item" id="tab_muellfach">
                                <span>📬</span> Müllfach.de | Postfach
                            </div>
                        </div>
                    </div>

                    <div class="browser-nav-bar">
                        <button class="nav-btn">◀</button>
                        <button class="nav-btn">▶</button>
                        <button class="nav-btn">🔄</button>
                        <div class="url-bar">
                            <span class="ssl-lock">🔒</span>
                            <span id="browser_url">https://www.morelogin.com/register</span>
                        </div>
                    </div>

                    <!-- Live Dynamic Viewport -->
                    <div class="browser-viewport" id="viewport">
                        <!-- Default Idle View: MoreLogin Form -->
                        <div class="morelogin-card" id="view_form">
                            <div class="ml-header">
                                <div class="ml-logo">M</div>
                                <div>
                                    <h4 style="font-size: 15px;">Create MoreLogin Account</h4>
                                    <p style="font-size: 11px; color: var(--text-muted);">The leading antidetect browser</p>
                                </div>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Email Address (muellfach.de)</label>
                                <div class="sim-input" id="sim_email">
                                    <span id="text_email" style="color: #94a3b8;">priyaahmed210208@muellfach.de</span>
                                    <span class="cursor-blink"></span>
                                </div>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Password</label>
                                <div class="sim-input" id="sim_pwd">
                                    <span id="text_pwd" style="color: #94a3b8;">••••••••••••</span>
                                </div>
                            </div>
                            <button class="btn-register-sim" id="btn_sim">Sign Up (1-Click Automation)</button>
                        </div>
                    </div>
                </div>

                <!-- Live Logs Box -->
                <div class="terminal-box" id="terminal_logs">
                    <div><span>[LOG]</span> Waiting for account creation trigger...</div>
                </div>
            </div>

            <!-- Right: Activity Feed & Accounts Created Table -->
            <div>
                <!-- Created Accounts Table -->
                <div class="card">
                    <div class="section-title">
                        <span>📋 Recent Created Accounts</span>
                        <span style="font-size: 11px; color: var(--text-muted);" id="acc_count_tag"></span>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Created</th>
                                <th>Email</th>
                                <th>Password</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="accounts_tbody">
                            <tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Loading accounts...</td></tr>
                        </tbody>
                    </table>
                </div>

                <!-- Realtime User Click Tracker -->
                <div class="card">
                    <div class="section-title">
                        <span>📡 Telegram Realtime Click Tracker</span>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>User</th>
                                <th>Button Clicked</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody id="activity_tbody">
                            <tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Loading events...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function fetchDashboardData() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                
                // Update stats
                document.getElementById('total_users').textContent = data.stats.total_users;
                document.getElementById('total_accounts').textContent = data.stats.total_accounts;
                document.getElementById('today_accounts').textContent = data.stats.today_accounts;
                document.getElementById('today_clicks_sub').textContent = `${data.stats.today_clicks} bot clicks today`;

                // Update Live Tracker state
                const trk = data.live_tracker;
                updateBrowserWindow(trk);

                // Update Accounts
                const accTbody = document.getElementById('accounts_tbody');
                if (data.accounts && data.accounts.length) {
                    document.getElementById('acc_count_tag').textContent = `Total: ${data.accounts.length}`;
                    accTbody.innerHTML = data.accounts.map(acc => `
                        <tr>
                            <td style="color: var(--text-muted); font-size: 11px;">${acc.created_at.split(' ')[1] || acc.created_at}</td>
                            <td><strong style="color: #60a5fa;">${acc.email}</strong></td>
                            <td><span class="code-box">${acc.password}</span></td>
                            <td><span class="badge badge-create">✅ Activated</span></td>
                        </tr>
                    `).join('');
                }

                // Update Activities
                const actTbody = document.getElementById('activity_tbody');
                if (data.activities && data.activities.length) {
                    actTbody.innerHTML = data.activities.slice(0, 10).map(a => {
                        const uname = a.username ? `@${a.username}` : (a.full_name || a.user_id);
                        return `
                            <tr>
                                <td style="color: var(--text-muted); font-size: 11px;">${a.timestamp.split(' ')[1] || a.timestamp}</td>
                                <td><strong>${uname}</strong></td>
                                <td><span class="badge badge-click">${a.button_name}</span></td>
                                <td style="color: var(--text-muted); font-size: 11px;">${a.details || '-'}</td>
                            </tr>
                        `;
                    }).join('');
                }
            } catch (err) {
                console.error("Dashboard refresh error:", err);
            }
        }

        function updateBrowserWindow(trk) {
            if (!trk) return;

            document.getElementById('browser_url').textContent = trk.url || 'https://www.morelogin.com/register';
            document.getElementById('step_indicator').textContent = trk.step_title || 'Ready';
            document.getElementById('step_sub').textContent = `Step ${trk.step || 0}/5`;

            // Active Tab Indicator
            const tabML = document.getElementById('tab_morelogin');
            const tabMF = document.getElementById('tab_muellfach');
            if (trk.active_tab === 'muellfach') {
                tabML.classList.remove('active');
                tabMF.classList.add('active');
            } else {
                tabML.classList.add('active');
                tabMF.classList.remove('active');
            }

            // Terminal Logs
            const logBox = document.getElementById('terminal_logs');
            if (trk.logs && trk.logs.length) {
                logBox.innerHTML = trk.logs.map(l => `<div>${l}</div>`).join('');
                logBox.scrollTop = logBox.scrollHeight;
            }

            // Status Tag
            const tag = document.getElementById('live_status_tag');
            const viewport = document.getElementById('viewport');

            if (trk.status === 'running') {
                tag.className = 'badge badge-create';
                tag.textContent = '⚡ RUNNING AUTOMATION...';

                if (trk.step === 1 || trk.step === 2 || trk.step === 3) {
                    // Show MoreLogin form with typed inputs
                    viewport.innerHTML = `
                        <div class="morelogin-card">
                            <div class="ml-header">
                                <div class="ml-logo">M</div>
                                <div>
                                    <h4 style="font-size: 15px;">Create MoreLogin Account</h4>
                                    <p style="font-size: 11px; color: var(--text-muted);">Step ${trk.step}: ${trk.step_title}</p>
                                </div>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Email Address (muellfach.de)</label>
                                <div class="sim-input focused">
                                    <span style="color: #60a5fa; font-weight: 600;">${trk.email || 'Generating...'}</span>
                                    <span class="cursor-blink"></span>
                                </div>
                            </div>
                            <div class="input-group">
                                <label class="input-label">Password</label>
                                <div class="sim-input focused">
                                    <span>${trk.password ? '••••••••••••' : 'Generating...'}</span>
                                </div>
                            </div>
                            <button class="btn-register-sim ${trk.step === 3 ? 'clicked' : ''}">
                                ${trk.step === 3 ? '⏳ Submitting to Gateway...' : 'Sign Up'}
                            </button>
                        </div>
                    `;
                } else if (trk.step === 4 || trk.step === 5) {
                    // Show Müllfach Inbox View
                    viewport.innerHTML = `
                        <div class="muellfach-view">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 8px;">
                                <div>
                                    <strong style="color: #38bdf8;">📬 Müllfach.de Inbox</strong>
                                    <div style="font-size: 11px; color: var(--text-muted); font-family: monospace;">${trk.email}</div>
                                </div>
                                <span class="badge badge-click">Auto-Syncing</span>
                            </div>
                            <div class="inbox-item">
                                <div>
                                    <div style="font-weight: 600; font-size: 13px;">【MoreLogin】Activate account</div>
                                    <div style="font-size: 11px; color: var(--text-muted);">from: morelogin@service.morelogin.com</div>
                                </div>
                                <a href="javascript:void(0)" class="activate-btn-highlight">👉 Activate Account (Clicking...)</a>
                            </div>
                        </div>
                    `;
                }
            } else if (trk.status === 'success') {
                tag.className = 'badge badge-create';
                tag.textContent = '✅ AUTOMATION COMPLETED';
                viewport.innerHTML = `
                    <div class="success-overlay">
                        <div class="check-circle">✓</div>
                        <h3 style="font-size: 18px; color: #10b981; margin-bottom: 6px;">MoreLogin Account Ready!</h3>
                        <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 14px;">100% Verified & Activated Automatically</p>
                        <div style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 12px; text-align: left; font-family: monospace; font-size: 12px; margin-bottom: 12px;">
                            <div>📧 <strong>Email:</strong> ${trk.email}</div>
                            <div style="margin-top: 4px;">🔑 <strong>Password:</strong> ${trk.password}</div>
                        </div>
                        <button class="btn" style="width: 100%; justify-content: center;" onclick="triggerWebAccountCreation()">⚡ Create Another Account</button>
                    </div>
                `;
            } else {
                tag.className = 'badge badge-click';
                tag.textContent = '● IDLE / READY';
            }
        }

        async function triggerWebAccountCreation() {
            const btn = document.getElementById('btn_run_test');
            btn.disabled = true;
            btn.textContent = '⚡ Running...';
            try {
                const res = await fetch('/api/create-account', { method: 'POST' });
                const data = await res.json();
                console.log("Triggered:", data);
            } catch (e) {
                alert('Could not start automation: ' + e);
            } finally {
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = '▶️ Run Live Automation Demo';
                }, 4000);
            }
        }

        // Live polling loop (fast 1 second poll for smooth visual updates!)
        fetchDashboardData();
        setInterval(fetchDashboardData, 1000);
    </script>
</body>
</html>
"""

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/dashboard", "/admin"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))

        elif parsed.path == "/api/data":
            stats = db.get_system_stats()
            activities = db.get_recent_activities(limit=15)
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM accounts ORDER BY id DESC LIMIT 15")
                accounts = [dict(r) for r in cursor.fetchall()]

            data = {
                "stats": stats,
                "activities": activities,
                "accounts": accounts,
                "live_tracker": live_tracker.get_state()
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/create-account":
            # Run creation in background thread
            def run_create():
                async def _task():
                    pwd = DEFAULT_PASSWORD
                    res = await creator.create_account_full_flow(
                        email_prefix=DEFAULT_EMAIL_PREFIX,
                        password=pwd
                    )
                    if res.get("success"):
                        db.save_account(
                            user_id=1,  # Web Admin user
                            email=res["email"],
                            password=res["password"],
                            is_activated=True,
                            activation_link=res.get("activation_link", "")
                        )
                        db.log_activity(
                            user_id=1,
                            username="WebAdmin",
                            full_name="Web Dashboard",
                            button_name="Web Live Automation",
                            action_type="create_account",
                            details=f"Created {res['email']}"
                        )
                asyncio.run(_task())

            threading.Thread(target=run_create, daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Automation started"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def start_web_dashboard(port: int = WEB_DASHBOARD_PORT):
    """Runs lightweight local web dashboard in background thread"""
    try:
        server = HTTPServer(("0.0.0.0", port), DashboardHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"🌐 Web Admin Live Dashboard running at http://localhost:{port}/")
    except Exception as e:
        print(f"⚠️ Could not start web dashboard on port {port}: {e}")
