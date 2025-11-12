import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import re

# --- إعدادات الصفحة والواجهة ---
st.set_page_config(page_title="محتوى برو", page_icon="🚀", layout="wide")

# --- إخفاء القائمة الافتراضية ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("✨ محتوى برو: مخطط المقال فائق السرعة")
st.write("أدخل كلمتك المفتاحية، ودع الذكاء الاصطناعي يحلل **هياكل** أفضل المنافسين ويبني لك مخطط مقال يتفوق عليهم.")

# --- إعدادات واجهة برمجة التطبيقات (API) ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    GEMINI_API_KEY = "AIzaSyAD2Rc1lOxzgj61DeVT5lV9qPJ4RVJ7V_s"  # <--- ضع مفتاحك هنا للتجربة المحلية

genai.configure(api_key=GEMINI_API_KEY)


# --- الدوال الأساسية ---

@st.cache_data(ttl=3600)  # تخزين النتائج لمدة ساعة لتسريع التجارب المتكررة
def get_competitor_links(keyword, num_results=5):
    """
    تبحث عن الكلمة المفتاحية باستخدام DDGS مع حيل لتحسين النتائج العربية.
    """
    links = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    try:
        with DDGS(headers=headers, timeout=20) as ddgs:
            results = list(ddgs.text(keywords=keyword, region='eg-ar', safesearch='off', max_results=num_results))
            if results:
                links = [r['href'] for r in results]
    except Exception as e:
        st.error(f"حدث خطأ أثناء البحث: {e}")
    return links


@st.cache_data(ttl=3600)
def scrape_headings_only(url):
    """
    (القلب الجديد للأداة)
    يستخلص عناوين H2 و H3 فقط من رابط المقال باستخدام BeautifulSoup.
    """
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        headings = []
        # البحث عن كل وسوم h2 و h3
        for heading in soup.find_all(['h2', 'h3']):
            # إضافة ## أو ### بناءً على نوع الوسم
            prefix = "##" if heading.name == 'h2' else "###"
            headings.append(f"{prefix} {heading.get_text(strip=True)}")

        return "\n".join(headings)
    except Exception:
        return None


def generate_ultimate_outline_from_headings(keyword, competitor_headings):
    """
    (البرومبت الجديد)
    ينشئ مخطط المقال الشامل بناءً على هياكل المنافسين.
    """
    content_prompt_part = ""
    for i, heading_list in enumerate(competitor_headings):
        content_prompt_part += f"**هيكل المقال المنافس {i + 1}:**\n{heading_list}\n\n---\n\n"

    prompt = f"""
    أنت خبير استراتيجي في تحسين محركات البحث (SEO) متخصص في تحليل المحتوى.
    الكلمة المفتاحية المستهدفة هي: "{keyword}"
    لقد قمت بتحليل **هياكل المقالات (قوائم العناوين H2 و H3)** لأفضل المنافسين، وهذه هي:
    {content_prompt_part}
    مهمتك الآن هي القيام بما يلي:
    1.  **تحليل الهياكل:** حدد الأنماط والنقاط المشتركة التي يغطيها كل المنافسين في عناوينهم الرئيسية (H2s).
    2.  **تحديد الفجوة الهيكلية:** ابحث عن زاوية مهمة أو قسم منطقي (H2) لم يركز عليه أي من المنافسين في هيكل مقالهم.
    3.  **بناء الهيكل الشامل (The Ultimate Outline):** قم بإنشاء مخطط مقال نهائي (H2s و H3s) بتنسيق Markdown. يجب أن يدمج المخطط أفضل ما في هياكل المنافسين ويضيف قسماً فريداً يغطي الفجوة التي وجدتها.
    القواعد:
    - استخدم `##` لـ H2 و `###` لـ H3.
    - لا تضف أي نصوص أو شروحات خارج المخطط. ابدأ مباشرة بأول H2.
    - كن استراتيجياً. الهدف هو بناء هيكل مقال يتفوق منطقياً على هياكل المنافسين.
    ابدأ الآن.
    """
    try:
        model = genai.GenerativeModel('models/gemini-pro-latest')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال بـ Google AI: {e}")
        return None


def display_expandable_outline(outline):
    """
    تعرض المخطط بشكل قابل للطي (Expanders) مع تلوين العناوين.
    """
    st.subheader("📝 مخطط المقال المقترح:")
    parts = re.split(r'(?=^##\s)', outline, flags=re.MULTILINE)
    for part in parts:
        if not part.strip():
            continue
        lines = part.strip().split('\n')
        h2_title = lines[0].strip('# ').strip()
        with st.expander(f"**{h2_title}**"):
            st.markdown(f'<h2 style="color: #0068c9; font-size: 1.5em;">{h2_title}</h2>', unsafe_allow_html=True)
            for line in lines[1:]:
                if line.strip().startswith('###'):
                    h3_title = line.strip('# ').strip()
                    st.markdown(f'<h3 style="color: #555555; font-size: 1.1em; margin-left: 20px;">- {h3_title}</h3>',
                                unsafe_allow_html=True)
                elif line.strip():
                    st.markdown(f'<p style="margin-left: 20px;">{line.strip()}</p>', unsafe_allow_html=True)


# --- واجهة المستخدم الرئيسية ---
keyword = st.text_input("أدخل الكلمة المفتاحية الأساسية هنا:", placeholder="مثال: أفضل طرق التسويق الرقمي")

if st.button("🚀 حلل هياكل المنافسين وابنِ المخطط", type="primary"):
    if not keyword:
        st.warning("يرجى إدخال كلمة مفتاحية أولاً.")
    elif not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY":
        st.error("يرجى وضع مفتاح Google AI API الصحيح في الكود أولاً.")
    else:
        with st.spinner("الخطوة 1/3: البحث عن أفضل المنافسين..."):
            links = get_competitor_links(keyword, num_results=5)

        if not links:
            st.error("لم يتم العثور على منافسين. حاول استخدام كلمة مفتاحية مختلفة.")
        else:
            st.info(f"تم العثور على {len(links)} منافسين. جاري تحليل هياكلهم...")

            competitor_headings = []
            with st.spinner("الخطوة 2/3: استخلاص هياكل العناوين (H2, H3)... (فائق السرعة!)"):
                for link in links[:3]:
                    headings = scrape_headings_only(link)
                    if headings:
                        competitor_headings.append(headings)

            if not competitor_headings:
                st.error("فشل استخلاص هياكل العناوين من المنافسين.")
            else:
                with st.spinner("الخطوة 3/3: العقل الاستراتيجي (Gemini) يبني الهيكل الشامل..."):
                    ultimate_outline = generate_ultimate_outline_from_headings(keyword, competitor_headings)

                st.success("🎉 تم بناء الهيكل الشامل بنجاح!")
                st.markdown("---")

                if ultimate_outline:
                    display_expandable_outline(ultimate_outline)
                else:
                    st.error("فشل إنشاء الهيكل.")
