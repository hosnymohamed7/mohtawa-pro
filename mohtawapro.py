import streamlit as st
import google.generativeai as genai
from newspaper import Article
from duckduckgo_search import DDGS
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

st.title("✨ محتوى برو: مخطط المقال الشامل")
st.write("أدخل كلمتك المفتاحية، ودع الذكاء الاصطناعي يحلل أفضل المنافسين ويبني لك مخطط مقال يتفوق عليهم جميعاً.")

# --- إعدادات واجهة برمجة التطبيقات (API) ---
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    GEMINI_API_KEY = "AIzaSyAD2Rc1lOxzgj61DeVT5lV9qPJ4RVJ7V_s"  # <--- ضع مفتاحك هنا للتجربة المحلية

genai.configure(api_key=GEMINI_API_KEY)


# --- الدوال الأساسية ---

def get_competitor_links(keyword, num_results=5):
    """
    تبحث عن الكلمة المفتاحية باستخدام DDGS مع حيل لتحسين النتائج العربية.
    """
    links = []
    # الحيلة 1: إضافة بصمة متصفح (User-Agent) حقيقي
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    try:
        with DDGS(headers=headers, timeout=20) as ddgs:
            # الحيلة 2: تحديد منطقة عربية بشكل صريح (eg-ar لمصر)
            results = list(ddgs.text(keywords=keyword, region='eg-ar', safesearch='off', max_results=num_results))
            if results:
                links = [r['href'] for r in results]
    except Exception as e:
        st.error(f"حدث خطأ أثناء البحث: {e}")
    return links


def scrape_and_summarize_article(url):
    """تستخلص النص من رابط المقال."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:2000]  # زدنا عدد الحروف قليلاً لملخص أفضل
    except Exception:
        return None


def generate_ultimate_outline(keyword, competitor_contents):
    """تنشئ مخطط المقال الشامل باستخدام Gemini."""
    content_prompt_part = ""
    for i, content in enumerate(competitor_contents):
        content_prompt_part += f"**ملخص المقال المنافس {i + 1}:**\n{content}\n\n---\n\n"

    prompt = f"""
    أنت خبير في تحسين محركات البحث (SEO) واستراتيجي محتوى بخبرة 20 عاماً. 
    مهمتك هي إنشاء مخطط مقال (Article Outline) شامل ونهائي يتفوق على المنافسين.
    الكلمة المفتاحية المستهدفة هي: "{keyword}"
    لقد قمت بتحليل محتوى أفضل المنافسين، وهذه هي ملخصاتهم:
    {content_prompt_part}
    مهمتك الآن هي القيام بما يلي:
    1.  **تحليل النقاط المشتركة:** حدد 3-4 مواضيع رئيسية اتفق عليها معظم المنافسين.
    2.  **تحديد الفجوة المعرفية:** ابحث عن سؤال مهم أو زاوية لم يغطها أي من المنافسين بشكل جيد.
    3.  **بناء المخطط الشامل (The Ultimate Outline):** بناءً على تحليلك، قم بإنشاء مخطط مقال نهائي (H2s و H3s) بتنسيق Markdown. يجب أن يتضمن المخطط كل النقاط المشتركة وقسماً خاصاً يغطي الفجوة المعرفية.
    القواعد:
    - استخدم `##` لـ H2 و `###` لـ H3.
    - لا تضف أي نصوص أو شروحات خارج المخطط. ابدأ مباشرة بأول H2.
    - اجعل المخطط شاملاً ومفصلاً.
    الهدف هو إنشاء مخطط لمقال يكون **أشمل وأفضل من أي من المقالات المنافسة**. ابدأ الآن.
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

    # تقسيم المخطط إلى أجزاء بناءً على H2
    # التعبير النمطي (regex) يبحث عن "## " في بداية السطر
    parts = re.split(r'(?=^##\s)', outline, flags=re.MULTILINE)

    for part in parts:
        if not part.strip():
            continue

        lines = part.strip().split('\n')
        h2_title = lines[0].strip('# ').strip()

        with st.expander(f"**{h2_title}**"):
            # طباعة H2 مرة أخرى داخل الـ expander بلون مميز
            st.markdown(f'<h2 style="color: #0068c9; font-size: 1.5em;">{h2_title}</h2>', unsafe_allow_html=True)

            # طباعة باقي الأسطر (H3s)
            for line in lines[1:]:
                if line.strip().startswith('###'):
                    h3_title = line.strip('# ').strip()
                    st.markdown(f'<h3 style="color: #555555; font-size: 1.1em; margin-left: 20px;">- {h3_title}</h3>',
                                unsafe_allow_html=True)
                elif line.strip():
                    st.markdown(f'<p style="margin-left: 20px;">{line.strip()}</p>', unsafe_allow_html=True)


# --- واجهة المستخدم الرئيسية ---
keyword = st.text_input("أدخل الكلمة المفتاحية الأساسية هنا:", placeholder="مثال: أفضل طرق التسويق الرقمي")

if st.button("🚀 حلل المنافسين وابنِ المخطط الشامل", type="primary"):
    if not keyword:
        st.warning("يرجى إدخال كلمة مفتاحية أولاً.")
    elif not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY":
        st.error("يرجى وضع مفتاح Google AI API الصحيح في الكود أولاً.")
    else:
        with st.spinner("الخطوة 1/3: البحث عن أفضل المنافسين..."):
            links = get_competitor_links(keyword, num_results=5)

        if not links:
            st.error("لم يتم العثور على منافسين. حاول استخدام كلمة مفتاحية مختلفة أو تحقق من الاتصال.")
        else:
            st.info(f"تم العثور على {len(links)} منافسين. جاري تحليل محتواهم...")

            competitor_contents = []
            with st.spinner("الخطوة 2/3: استخلاص وتحليل محتوى المنافسين... (قد تستغرق هذه الخطوة دقيقة)"):
                for link in links[:3]:
                    content = scrape_and_summarize_article(link)
                    if content:
                        competitor_contents.append(content)

            if not competitor_contents:
                st.error("فشل استخلاص المحتوى من روابط المنافسين. قد تكون صفحات معقدة أو محمية.")
            else:
                with st.spinner("الخطوة 3/3: العقل المدبر (Gemini) يقوم ببناء المخطط الشامل..."):
                    ultimate_outline = generate_ultimate_outline(keyword, competitor_contents)

                st.success("🎉 تم إنشاء مخطط المقال الشامل بنجاح!")
                st.markdown("---")

                if ultimate_outline:
                    display_expandable_outline(ultimate_outline)
                else:
                    st.error("فشل إنشاء المخطط.")
