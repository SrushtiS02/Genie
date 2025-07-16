import streamlit as st
from PIL import Image
import os
from gemini_api import (
    generate_creative_ideas,
    analyze_caption,
    suggest_captions_from_image,
    localize_caption,
)
from utils import (
    run_ab_test_simulation,
    get_supported_languages,
    format_score,
)
from dotenv import load_dotenv

load_dotenv()

# --------- Aesthetic Almond-Pink Styling ---------
st.markdown("""
    <style>
    body, .main, [data-testid="stAppViewContainer"] {
        background-color: #FAF3EB !important;  /* almond white */
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #FAF3EB 0%, #FCE4EC 100%) !important;
    }
    h1, h4, .stMarkdown {
        font-family: 'Quicksand', 'Segoe UI', sans-serif !important;
        color: #6B2956 !important;
    }
    .genie-header {
        background: #FCE4EC;
        border-radius: 24px;
        box-shadow: 0 8px 36px rgba(107,41,86,0.07);
        padding: 1.5rem 1.2rem 1.2rem 1.2rem;
        margin-bottom: 30px;
        border-left: 9px solid #B4889F;
    }
    .genie-header h1 {
        color: #6B2956 !important;
        font-size: 2.5em;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .genie-header h4 {
        color: #B4889F !important;
        margin-top: 0.2em;
        font-size: 1.17em;
        font-weight: 500;
    }
    .genie-header span {
        color: #B4889F !important;
        font-size: 1.07em;
        font-weight: 600;
    }
    .option-box {
        background: #FFF8F7;
        border-radius: 13px;
        border: 1.5px solid #FCE4EC;
        padding: 1em 1.1em;
        margin-bottom: 12px;
        color: #5C5050;
        font-size: 1.09em;
    }
    .stButton>button {
        background-color: #A3B18A !important;
        color: #fff !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
        font-size: 1em !important;
        border: none !important;
        box-shadow: 0 2px 8px #b9d6df24 !important;
        transition: 0.18s;
    }
    .stButton>button:hover {
        background-color: #B4889F !important;
        color: #fff !important;
    }
    .stTabs [role="tab"] {
        background: #FFF8F7 !important;
        color: #B4889F !important;
        border-radius: 10px 10px 0 0 !important;
        font-weight: 600;
        font-size: 1.07em;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: #FAF3EB !important;
        color: #6B2956 !important;
    }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# --------- Header ---------
def show_header():
    st.markdown("""
        <div class='genie-header'>
            <h1>Genie</h1>
            <h4>Generative Ideation & Evaluation Assistant</h4>
            <span>by Srushti Surpur</span>
        </div>
    """, unsafe_allow_html=True)

show_header()

tabs = st.tabs(["💡 Creative Assistant", "🖼️ Image/Poster Analysis", "ℹ️ About Genie"])

# ------------- Creative Assistant -------------
with tabs[0]:
    st.markdown("#### Generate campaign slogans, event names, or creative ideas.")
    st.write("Enter your prompt below. _(e.g., Give me 3 taglines for an online game night)_")
    user_prompt = st.text_area("Describe the idea to brainstorm:", height=80, key="creative_prompt")
    style = st.selectbox(
        "Choose a style (optional)",
        ["Default", "Witty", "Exciting", "Responsible", "Luxury", "Fun"],
        index=0,
        key="creative_style"
    )
    if st.button("Generate Ideas", key="generate_ideas_btn"):
        if user_prompt.strip() == "":
            st.warning("Please enter your idea prompt to get started.")
        else:
            with st.spinner("Genie is generating ideas..."):
                try:
                    ideas, variations = generate_creative_ideas(user_prompt, style)
                    if len(variations) > 1:
                        ab_results = run_ab_test_simulation(variations)
                        st.markdown("#### Top Suggestions")
                        for idx, result in enumerate(ab_results):
                            st.markdown(
                                f"<div class='option-box'><b>Option {chr(65+idx)}:</b> "
                                f"<span style='color:#A3B18A;'>{result['caption']}</span><br>"
                                f"<b>Engagement:</b> <span style='color:#B9D6DF;'>{format_score(result['score'])}</span><br>"
                                f"<span style='color:#968E7E;'>{result['why']}</span>"
                                + ("<br>🌟 <b style='color:#A3B18A;'>Recommended</b>" if result['recommended'] else "")
                                + "</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.success(f"“{ideas[0]}”")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# ------------- Image/Poster Analysis -------------
with tabs[1]:
    st.markdown("#### Upload a poster or banner to analyze and optimize your caption, then translate for global markets.")
    img_file = st.file_uploader("Upload an image (JPG or PNG):", type=['jpg', 'png'], key="image_upload")
    input_caption = st.text_area(
        "Enter your caption/tagline (or leave blank for suggestions):",
        height=80,
        key="caption_input"
    )
    lang_options = get_supported_languages()
    selected_lang = st.selectbox("Translate to (localization):", lang_options, index=0, key="localize_lang")

    if st.button("Analyze Content", key="analyze_btn"):
        if not img_file:
            st.warning("Please upload an image before analyzing.")
        else:
            try:
                image = Image.open(img_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                with st.spinner("Genie is analyzing your content..."):
                    # If caption provided, analyze it
                    if input_caption.strip():
                        analysis = analyze_caption(image, input_caption)
                        st.markdown(f"**Original Caption:** “{input_caption}”")
                        st.markdown(f"**Engagement Score:** {format_score(analysis['engagement_score'])}")
                        st.markdown(f"**Brand Voice:** {analysis['brand_voice']}")
                        st.markdown(f"**Compliance Check:** {analysis['compliance']}")
                        st.markdown("**Suggestions:**")
                        ab_results = run_ab_test_simulation(analysis["caption_variations"])
                        for idx, result in enumerate(ab_results):
                            st.markdown(
                                f"<div class='option-box'><b>Option {chr(65+idx)}:</b> "
                                f"<span style='color:#A3B18A;'>{result['caption']}</span> "
                                f"(Score: <span style='color:#B9D6DF;'>{format_score(result['score'])}</span>)"
                                + (" 🌟 <b style='color:#A3B18A;'>Recommended</b>" if result['recommended'] else "")
                                + "</div>",
                                unsafe_allow_html=True
                            )
                        st.divider()
                        # Localization
                        if selected_lang != "English":
                            st.markdown("**Localized Caption:**")
                            localized = localize_caption(analysis['caption_variations'][0]["caption"], selected_lang)
                            st.markdown(f"{selected_lang}: “{localized['localized_caption']}”")
                            if localized.get("notes"):
                                st.info(f"Note: {localized['notes']}")
                    else:
                        suggestion = suggest_captions_from_image(image)
                        st.markdown(f"**Suggested Caption:** “{suggestion['caption']}”")
                        st.markdown(f"**Engagement Score:** {format_score(suggestion['engagement_score'])}")
                        st.markdown(f"**Brand Voice:** {suggestion['brand_voice']}")
                        st.markdown(f"**Compliance Check:** {suggestion['compliance']}")
                        if suggestion.get('caption_variations'):
                            st.markdown("**Alternate Captions:**")
                            ab_results = run_ab_test_simulation(suggestion["caption_variations"])
                            for idx, result in enumerate(ab_results):
                                st.markdown(
                                    f"<div class='option-box'><b>Option {chr(65+idx)}:</b> "
                                    f"<span style='color:#A3B18A;'>{result['caption']}</span> "
                                    f"(Score: <span style='color:#B9D6DF;'>{format_score(result['score'])}</span>)"
                                    + (" 🌟 <b style='color:#A3B18A;'>Recommended</b>" if result['recommended'] else "")
                                    + "</div>",
                                    unsafe_allow_html=True
                                )
                        # Localization
                        if selected_lang != "English":
                            st.markdown("**Localized Caption:**")
                            localized = localize_caption(suggestion['caption'], selected_lang)
                            st.markdown(f"{selected_lang}: “{localized['localized_caption']}”")
                            if localized.get("notes"):
                                st.info(f"Note: {localized['notes']}")
            except Exception as e:
                st.error(f"Error analyzing image: {e}")

# ------------- About / Help -------------
with tabs[2]:
    st.markdown("### About Genie")
    st.markdown(
        """
        Genie is a generative ideation and evaluation assistant for creative teams and content marketers.

        - **Creative Brainstorming:** Campaign ideas, event names, and slogans
        - **Image-to-Text:** Caption generation and analysis for visuals
        - **Brand Voice & Compliance:** Automated checks for engagement, clarity, and responsibility
        - **A/B Testing Simulation:** Highlights the best creative options
        - **Localization:** European languages and Hindi

        <br><br>
        <sub>Developed by Srushti Surpur.  
        [LinkedIn](https://www.linkedin.com/in/srushtisurpur/) | [Email](mailto:surpurs@tcd.ie)</sub>
        """, unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("For support or collaboration, please get in touch.")
