#!/bin/bash
echo "🚀 กำลังเปิด NovaAgent + Cloudflared..."
cd ~/NovaAgent-Clean
nohup python app.py > ~/nova.log 2>&1 &
echo "✅ NovaAgent เริ่มทำงาน (PID: $!)"
sleep 5
nohup cloudflared tunnel --url http://127.0.0.1:17009 > ~/cloudflared.log 2>&1 &
echo "✅ Cloudflared Tunnel เริ่มทำงาน (PID: $!)"
sleep 5
echo ""
echo "🌐 URL ของคุณ:"
grep -o 'https://[^ ]*trycloudflare.com' ~/cloudflared.log | head -1
echo ""
echo "🎯 พร้อมใช้งาน!"
