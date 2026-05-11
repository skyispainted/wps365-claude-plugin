# -*- coding: utf-8 -*-
"""OAuth 授权成功页面 HTML"""

LOGIN_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAuth 授权成功</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    fontFamily: { sans: ['Outfit', 'sans-serif'] },
                    colors: {
                        brand: { 50: '#f0f9ff', 100: '#e0f2fe', 500: '#0ea5e9', 600: '#0284c7', 900: '#0c4a6e' },
                        success: '#10b981',
                    },
                    animation: { 'blob': 'blob 7s infinite', 'check': 'check 0.5s cubic-bezier(0.65, 0, 0.45, 1) forwards', 'fade-in-up': 'fadeInUp 0.8s ease-out forwards' },
                    keyframes: {
                        blob: { '0%': { transform: 'translate(0px, 0px) scale(1)' }, '33%': { transform: 'translate(30px, -50px) scale(1.1)' }, '66%': { transform: 'translate(-20px, 20px) scale(0.9)' }, '100%': { transform: 'translate(0px, 0px) scale(1)' } },
                        fadeInUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } }
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #f8fafc; }
        .checkmark__circle { stroke-dasharray: 166; stroke-dashoffset: 166; stroke-width: 2; stroke-miterlimit: 10; stroke: #10b981; fill: none; animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards; }
        .checkmark { width: 80px; height: 80px; border-radius: 50%; display: block; stroke-width: 2; stroke: #fff; stroke-miterlimit: 10; margin: 0 auto; box-shadow: inset 0px 0px 0px #10b981; animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both; }
        .checkmark__check { transform-origin: 50% 50%; stroke-dasharray: 48; stroke-dashoffset: 48; animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards; }
        @keyframes stroke { 100% { stroke-dashoffset: 0; } }
        @keyframes scale { 0%, 100% { transform: none; } 50% { transform: scale3d(1.1, 1.1, 1); } }
        @keyframes fill { 100% { box-shadow: inset 0px 0px 0px 50px #10b981; } }
        .glass-card { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.6); }
        .progress-bar { transition: width 0.1s linear; }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center relative overflow-hidden text-slate-800 selection:bg-brand-500 selection:text-white">
    <div class="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
    <div class="absolute top-0 -right-4 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
    <div class="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
    <div class="absolute bottom-0 right-0 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>
    <div class="glass-card w-full max-w-md p-8 rounded-3xl shadow-2xl relative z-10 transform transition-all duration-500 hover:shadow-brand-500/20 animate-fade-in-up mx-4">
        <div class="absolute top-4 right-4">
            <div class="flex items-center gap-1.5 bg-green-50 border border-green-100 text-green-700 px-2.5 py-1 rounded-full text-xs font-medium shadow-sm">
                <i class="fa-solid fa-shield-halved"></i><span>Secure</span>
            </div>
        </div>
        <div class="text-center mt-4">
            <div class="mb-6 relative h-24 flex items-center justify-center">
                <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
                    <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
            </div>
            <h1 class="text-3xl font-bold text-slate-900 mb-2 tracking-tight">授权成功</h1>
            <p class="text-slate-500 text-base mb-8 leading-relaxed">恭喜您已成功登录。请返回继续完成后续的配置工作。</p>
            <div class="w-full bg-slate-100 rounded-full h-1.5 mb-3 overflow-hidden">
                <div id="progress" class="progress-bar bg-gradient-to-r from-brand-500 to-purple-600 h-1.5 rounded-full w-0"></div>
            </div>
            <p id="close-hint" class="text-sm text-slate-400 mb-6"><span id="countdown" class="font-mono font-bold text-slate-600">3</span> 秒后自动关闭...</p>
            <button onclick="manualRedirect()" class="w-full py-3 px-4 bg-white border border-slate-200 hover:border-brand-300 hover:bg-brand-50 text-slate-400 font-medium rounded-xl transition-all duration-200 shadow-sm hover:shadow-md flex items-center justify-center gap-2 group">
                <span>点击关闭</span><i class="fa-solid fa-power-off text-slate-400 group-hover:scale-110 transition-transform"></i>
            </button>
        </div>
        <div class="mt-8 pt-6 border-t border-slate-100 text-center">
            <p class="text-xs text-slate-400"><i class="fa-solid fa-lock mr-1"></i> WPS365开放平台 数字员工开发平台</p>
        </div>
    </div>
    <script>
        const totalSeconds = 3;
        const progressEl = document.getElementById('progress');
        const countdownEl = document.getElementById('countdown');
        let timeLeft = totalSeconds;
        const intervalStep = 50;
        const totalSteps = (totalSeconds * 1000) / intervalStep;
        let currentStep = 0;
        const timer = setInterval(() => {
            currentStep++;
            const percentage = Math.min((currentStep / totalSteps) * 100, 100);
            progressEl.style.width = percentage + '%';
            if (currentStep % (1000 / intervalStep) === 0) { timeLeft--; if (timeLeft >= 0) countdownEl.textContent = timeLeft; }
            if (currentStep >= totalSteps) { clearInterval(timer); countdownEl.textContent = "0"; setTimeout(() => { try { window.close(); } catch(e) {} }, 300); }
        }, intervalStep);
        function manualRedirect() { try { window.close(); } catch(e) {} }
    </script>
</body>
</html>
"""
