#!/bin/bash
echo "🛑 กำลังปิด NovaAgent + Cloudflared..."
pkill -f "python app.py"
pkill -f "cloudflared tunnel"
echo "🎯 ปิดระบบเรียบร้อย!"
