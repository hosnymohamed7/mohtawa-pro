import streamlit as st
import google.generativeai as genai
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

st.title("✨ محتوى برو: محلل الروابط الاستراتيجي")
st.write(
    "اذهب إلى جوجل، ابحث عن كلمتك المفتاحية، ثم الصق هنا روابط أفضل 3-5 مقالات منافسة لبناء مخطط مقال يتفوق عليهم.")

# --- إعدادات واجهة برمجة التطبيقات (API) ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    GEMINI_API_KEY = "AIzaSyAD2Rc1lOxzgj61DeVT5lV9qPJ4RVJ7V_s"  # <--- ضع مفتاحك هنا للتجربة المحلية

genai.configure(api_key=GEMINI_API_KEY)


# --- الدوال الأساسية ---

@st.cache_data(ttl=3600)
def scrape_headings_only(url):
    """
    يستخلص عناوين H2 و H3 فقط من رابط المقال باستخدام BeautifulSoup.
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        headings = []
        for heading in soup.find_all(['h2', 'h3']):
            prefix = "##" if heading.name == 'h2' else "###"
            headings.append(f"{prefix} {heading.get_text(strip=True)}")

        return "\n".join(headings)
    except Exception as e:
        st.warning(f"فشل تحليل الرابط: {url} - السبب: {e}")
        return None


def generate_ultimate_outline_from_headings(competitor_headings):
    """
    ينشئ مخطط المقال الشامل بناءً على هياكل المنافسين.
    """
    content_prompt_part = ""
    for i, heading_list in enumerate(competitor_headings):
        content_prompt_part += f"**هيكل المقال المنافس {i + 1}:**\n{heading_list}\n\n---\n\n"

    prompt = f"""
    أنت خبير استراتيجي في تحسين محركات البحث (SEO) متخصص في تحليل المحتوى.
    لقد قمت بتحليل **هياكل المقالات (قوائم العناوين H2 و H3)** التي قدمها المستخدم، وهذه هي:
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
                    # --- هذا هو السطر الذي تم تعديله ---
                    st.markdown(f'<h3 style="color: #FFFFFF; font-size: 1.1em; margin-left: 20px;">- {h3_title}</h3>',
                                unsafe_allow_html=True)
                elif line.strip():
                    st.markdown(f'<p style="margin-left: 20px;">{line.strip()}</p>', unsafe_allow_html=True)


# --- واجهة المستخدم الرئيسية ---
links_input = st.text_area(
    "الصق هنا روابط المقالات المنافسة (كل رابط في سطر منفصل)",
    height=150,
    placeholder="مثال:\nhttps://www.example.com/article-1\nhttps://www.another.com/blog-post-2\n..."
)

if st.button("🚀 حلل الروابط وابنِ المخطط", type="primary"):
    links = [link.strip() for link in links_input.split('\n') if link.strip()]

    if not links:
        st.warning("يرجى لصق رابط واحد على الأقل.")
    elif not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY":
        st.error("يرجى وضع مفتاح Google AI API الصحيح في الكود أولاً.")
    else:
        st.info(f"تم العثور على {len(links)} روابط. جاري تحليل هياكلها...")

        competitor_headings = []
        with st.spinner("الخطوة 1/2: استخلاص هياكل العناوين (H2, H3)..."):
            for link in links:
                headings = scrape_headings_only(link)
                if headings:
                    competitor_headings.append(headings)

        if not competitor_headings:
            st.error("فشل استخلاص هياكل العناوين من الروابط المقدمة. تأكد من أن الروابط صحيحة وقابلة للتحليل.")
        else:
            with st.spinner("الخطوة 2/2: العقل الاستراتيجي (Gemini) يبني الهيكل الشامل..."):
                ultimate_outline = generate_ultimate_outline_from_headings(competitor_headings)

            st.success("🎉 تم بناء الهيكل الشامل بنجاح!")
            st.markdown("---")

            if ultimate_outline:
                display_expandable_outline(ultimate_outline)
            else:
                st.error("فشل إنشاء الهيكل.")
