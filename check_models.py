import google.generativeai as genai
import os

# --- ضع مفتاحك هنا ---
# استبدل "YOUR_API_KEY" بمفتاحك الحقيقي
API_KEY = "AIzaSyAD2Rc1lOxzgj61DeVT5lV9qPJ4RVJ7V_s"

try:
    genai.configure(api_key=API_KEY)

    print("--- قائمة الموديلات المتاحة لحسابك ---")
    for m in genai.list_models():
        # نحن نهتم فقط بالموديلات التي تدعم إنشاء المحتوى
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    print("------------------------------------")

except Exception as e:
    print(f"حدث خطأ: {e}")

