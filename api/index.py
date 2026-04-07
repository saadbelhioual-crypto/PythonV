from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import sys
import os
import uuid
import tempfile
import shutil
from pathlib import Path

app = FastAPI()

# إعداد المسارات
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# التأكد من وجود مجلد static
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/execute")
async def execute_code(code: str = Form(...)):
    temp_file = None
    try:
        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            # إضافة مكتبات مساعدة تلقائياً
            enhanced_code = f"""
# المكتبات المتاحة تلقائياً
import sys
import json
import math
import random
from datetime import datetime

try:
    import numpy as np
except ImportError:
    pass
try:
    import pandas as pd
except ImportError:
    pass
try:
    import requests
except ImportError:
    pass

# كود المستخدم
{code}
"""
            f.write(enhanced_code)
            temp_file = f.name
        
        # تنفيذ الكود
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=tempfile.gettempdir()
        )
        
        output = result.stdout
        error = result.stderr
        
        return JSONResponse({
            "success": True,
            "output": output if output else "✅ تم التنفيذ بنجاح (لا يوجد مخرجات)",
            "error": error if error else None
        })
        
    except subprocess.TimeoutExpired:
        return JSONResponse({
            "success": False,
            "output": "",
            "error": "⏰ انتهى وقت التنفيذ (أكثر من 10 ثوانٍ)"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "output": "",
            "error": f"❌ خطأ: {str(e)}"
        })
    finally:
        # تنظيف الملف المؤقت
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    temp_dir = None
    try:
        # إنشاء مجلد مؤقت
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        
        # حفظ الملف
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # إذا كان ملف Python، نحاول تنفيذه
        if file.filename.endswith('.py'):
            result = subprocess.run(
                [sys.executable, file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return JSONResponse({
                "success": True,
                "message": f"✅ تم رفع وتنفيذ {file.filename}",
                "output": result.stdout if result.stdout else "تم التنفيذ بنجاح",
                "error": result.stderr if result.stderr else None
            })
        
        # للملفات الأخرى
        return JSONResponse({
            "success": True,
            "message": f"✅ تم رفع {file.filename} بنجاح",
            "size": f"{len(content)} بايت",
            "type": file.content_type
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": f"❌ خطأ في رفع الملف: {str(e)}"
        })
    finally:
        # تنظيف
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

@app.get("/libraries")
async def get_libraries():
    """إرجاع قائمة المكتبات المتاحة"""
    libraries = {
        "standard": ["math", "random", "datetime", "json", "re", "os", "sys"],
        "installed": ["numpy", "pandas", "requests", "beautifulsoup4", "scipy", "matplotlib", "sympy", "sklearn"]
    }
    return JSONResponse(libraries)
