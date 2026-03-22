"""
msata_component.py — Full MSATA Agreement Component
=====================================================
English + Hindi bilingual
4 mandatory checkboxes
Forensic execution log
IT Act 2000 compliant
"""

import streamlit as st
import datetime
import uuid
import hashlib
import json

MSATA_ENGLISH = """
MASTER SERVICE & ASSET TRANSFER AGREEMENT
Technical Consultancy, Copyright Assignment, and Professional Indemnity
Platform: PaperForge AI | Version: MSATA-2026-DIGITAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I. SCOPE OF SERVICES & TERM

This Agreement governs the technical consultancy services provided by the Licensor (PaperForge AI / Yogesh Wagh), specifically the development of computational prototypes, mathematical models, and statistical simulations. This Agreement applies to all deliverables provided on or after the date of digital execution. The Client acknowledges receiving prior deliverables (if any) and explicitly agrees that continued use of such work constitutes acceptance of these terms regarding liability, confidentiality, and academic integrity.

II. COPYRIGHT ASSIGNMENT (SECTION 17)

Pursuant to Section 17(b) of the Copyright Act, 1957, the Licensor agrees that all rights in the final deliverables shall transfer to the Client as a "Work-for-Hire" only upon receipt of full and final payment of applicable credits. Until payment is perfected, the Licensor remains the sole owner of the intellectual property. Any use of deliverables prior to final payment is granted under a limited, revocable license.

III. PAYMENT MILESTONES & TIMELINES

Services shall be delivered upon deduction of applicable credits from the Client's account. The Licensor shall deliver work within the session in which credits are deducted. Client Acceptance: The Client shall have 7 days from delivery to report non-conformity with specifications. Silence beyond this period constitutes final acceptance of the deliverable. No further revisions shall be entertained post-acceptance without additional credit expenditure.

IV. CLIENT RESPONSIBILITIES & MUTUAL NDA

The Client shall provide clear project specifications. Both parties agree to maintain strict confidentiality of proprietary information shared during this engagement for a period of 3 years following the completion of services. Neither party shall disclose the nature of the consultancy to third parties without written consent. The platform's proprietary algorithms, prompt structures, and data generation methods are protected trade secrets.

V. ACADEMIC INTEGRITY WARRANTY

THE CLIENT WARRANTS THAT THE DELIVERABLES ARE "TECHNICAL PROTOTYPES" AND SHALL NOT BE SUBMITTED AS ORIGINAL RESEARCH FOR DEGREE REQUIREMENTS (UGC 2018 GUIDELINES). The Client agrees to indemnify the Licensor against any and all claims of academic misconduct, fraud, plagiarism, or misrepresentation resulting from the misuse or misattribution of these technical simulations. The Client acknowledges that all statistical outputs are illustrative computational models and not empirically collected field data. The Client takes full and sole responsibility for any academic, legal, or professional consequences arising from the use of these deliverables.

VI. LIABILITY CAP & DISPUTE RESOLUTION

The total liability of the Licensor for any claims arising from this Agreement is strictly limited to the total credits paid by the Client for the specific deliverable, valued at face credit rate. Any disputes shall be resolved via binding arbitration in Pune, Maharashtra, under the Arbitration and Conciliation Act, 1996. The parties shall mutually appoint a sole arbitrator; failing agreement within 15 days, the arbitrator shall be appointed by the Pune Bar Association. This Agreement is governed by the laws of Maharashtra and the Republic of India.

VII. TERMINATION & REFUND POLICY

Termination: Either party may terminate with 7 days' written notice. Credits consumed for completed work are non-refundable. Refunds: Credits represent completed performance of technical services and are non-refundable once generation is confirmed. Non-delivery means failure to provide deliverables within the active session; in such cases, credit refund is automatic and immediate.

VIII. FORCE MAJEURE

Neither party shall be liable for delays caused by circumstances beyond reasonable control, including acts of God, government restrictions, API provider outages, or critical technology failures. The affected party shall use reasonable efforts to minimise delays and resume performance. Written notice must be provided within 48 hours of the event.

IX. WATERMARKING & ASSET PROTECTION

The Licensor reserves the right to apply visible or invisible watermarks, metadata tags, or identification markers to any deliverable. All downloadable files contain embedded metadata identifying the generation session, user details, and timestamp. Removal or alteration of such markings constitutes a material breach of this Agreement.

X. DATA PRIVACY

The platform collects and stores: full name, email address, IP address, browser user agent, generation parameters, and MSATA execution timestamp. This data is stored securely and used solely for legal compliance, abuse prevention, and service improvement. No data is sold to third parties. Data retention period: 7 years for legal compliance.

XI. GOVERNING LAW & LANGUAGE HIERARCHY

This Agreement is governed by the laws of Maharashtra and the Republic of India. In case of any conflict between the English and Hindi versions, the English text shall prevail in all legal interpretations.

XII. SEVERABILITY

If any provision of this Agreement is held invalid or unenforceable by a court or tribunal, the remaining provisions shall continue in full force and effect.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Executed under Section 3A and 5 of the Information Technology Act, 2000
Digital execution constitutes a legally binding signature under Indian law.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

MSATA_HINDI = """
मास्टर सेवा एवं संपत्ति हस्तांतरण अनुबंध
तकनीकी परामर्श, कॉपीराइट असाइनमेंट और व्यावसायिक क्षतिपूर्ति
प्लेटफॉर्म: PaperForge AI | संस्करण: MSATA-2026-डिजिटल

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I. सेवाओं का दायरा एवं अवधि

यह अनुबंध लाइसेंसकर्ता (PaperForge AI / योगेश वाघ) द्वारा प्रदान की जाने वाली तकनीकी परामर्श सेवाओं को नियंत्रित करता है, विशेष रूप से कम्प्यूटेशनल प्रोटोटाइप, गणितीय मॉडल और सांख्यिकीय सिमुलेशन का विकास। यह अनुबंध डिजिटल निष्पादन की तारीख को या उसके बाद प्रदान किए गए सभी डिलिवरेबल्स पर लागू होता है।

II. कॉपीराइट असाइनमेंट (धारा 17)

कॉपीराइट अधिनियम, 1957 की धारा 17(ब) के अनुसार, लाइसेंसकर्ता सहमत है कि अंतिम डिलिवरेबल्स में सभी अधिकार क्लाइंट को "कार्य-के-लिए-किराया" के रूप में केवल लागू क्रेडिट के पूर्ण और अंतिम भुगतान की प्राप्ति पर हस्तांतरित होंगे।

III. भुगतान मील के पत्थर एवं समयसीमा

सेवाएं क्लाइंट के खाते से लागू क्रेडिट की कटौती पर प्रदान की जाएंगी। लाइसेंसकर्ता उस सत्र के भीतर कार्य प्रदान करेगा जिसमें क्रेडिट काटे जाते हैं।

IV. क्लाइंट की जिम्मेदारियां और पारस्परिक एनडीए

क्लाइंट स्पष्ट परियोजना विनिर्देश प्रदान करेगा। दोनों पक्ष सेवाओं की समाप्ति के बाद 3 वर्षों की अवधि के लिए इस सहयोग के दौरान साझा की गई स्वामित्व जानकारी की सख्त गोपनीयता बनाए रखने के लिए सहमत हैं।

V. शैक्षणिक अखंडता वारंटी

क्लाइंट गारंटी देता है कि डिलिवरेबल्स "तकनीकी प्रोटोटाइप" हैं और उन्हें डिग्री आवश्यकताओं (UGC 2018 दिशानिर्देश) के लिए मूल शोध के रूप में प्रस्तुत नहीं किया जाएगा। क्लाइंट इन तकनीकी सिमुलेशन के दुरुपयोग या गलत आरोपण से उत्पन्न शैक्षणिक कदाचार, धोखाधड़ी, साहित्यिक चोरी या गलत बयानी के किसी भी और सभी दावों के खिलाफ लाइसेंसकर्ता को क्षतिपूर्ति देने के लिए सहमत है। क्लाइंट स्वीकार करता है कि सभी सांख्यिकीय आउटपुट दृष्टांत कम्प्यूटेशनल मॉडल हैं न कि अनुभवजन्य रूप से एकत्रित फील्ड डेटा।

VI. देयता सीमा एवं विवाद समाधान

इस अनुबंध से उत्पन्न किसी भी दावे के लिए लाइसेंसकर्ता की कुल देयता विशिष्ट डिलिवरेबल के लिए क्लाइंट द्वारा भुगतान किए गए कुल क्रेडिट तक सख्ती से सीमित है। किसी भी विवाद को मध्यस्थता और सुलह अधिनियम, 1996 के तहत पुणे, महाराष्ट्र में बाध्यकारी मध्यस्थता के माध्यम से हल किया जाएगा।

VII. समाप्ति एवं धनवापसी नीति

पूर्ण किए गए कार्य के लिए उपभोग किए गए क्रेडिट वापस नहीं किए जा सकते। क्रेडिट तकनीकी सेवाओं के पूर्ण प्रदर्शन का प्रतिनिधित्व करते हैं और एक बार पीढ़ी की पुष्टि होने के बाद वापस नहीं किए जा सकते।

VIII. अप्रत्याशित घटना

न तो पक्ष उचित नियंत्रण से परे परिस्थितियों के कारण देरी के लिए उत्तरदायी होगा।

IX. वॉटरमार्किंग एवं संपत्ति संरक्षण

लाइसेंसकर्ता किसी भी डिलिवरेबल पर दृश्यमान या अदृश्य वॉटरमार्क, मेटाडेटा टैग या पहचान मार्कर लगाने का अधिकार सुरक्षित रखता है।

X. डेटा गोपनीयता

प्लेटफॉर्म संग्रहीत करता है: पूरा नाम, ईमेल पता, आईपी पता, ब्राउज़र उपयोगकर्ता एजेंट, पीढ़ी पैरामीटर और MSATA निष्पादन टाइमस्टैम्प। यह डेटा सुरक्षित रूप से संग्रहीत किया जाता है।

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
सूचना प्रौद्योगिकी अधिनियम, 2000 की धारा 3A और 5 के तहत निष्पादित
डिजिटल निष्पादन भारतीय कानून के तहत कानूनी रूप से बाध्यकारी हस्ताक्षर का गठन करता है।
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

CHECKBOXES = [
    {
        "id": "cb1",
        "en": "I confirm that the deliverables are Technical Prototypes and will NOT be submitted as original research for any degree, diploma, or academic requirement under UGC 2018 guidelines.",
        "hi": "मैं पुष्टि करता/करती हूं कि डिलिवरेबल्स तकनीकी प्रोटोटाइप हैं और UGC 2018 दिशानिर्देशों के तहत किसी भी डिग्री, डिप्लोमा या शैक्षणिक आवश्यकता के लिए मूल शोध के रूप में प्रस्तुत नहीं किए जाएंगे।",
    },
    {
        "id": "cb2",
        "en": "I understand that all statistical data, datasets, and findings generated are illustrative computational models. I take full legal responsibility for any consequences arising from their use.",
        "hi": "मैं समझता/समझती हूं कि उत्पन्न सभी सांख्यिकीय डेटा, डेटासेट और निष्कर्ष दृष्टांत कम्प्यूटेशनल मॉडल हैं। मैं उनके उपयोग से उत्पन्न किसी भी परिणाम के लिए पूरी कानूनी जिम्मेदारी लेता/लेती हूं।",
    },
    {
        "id": "cb3",
        "en": "I agree to indemnify PaperForge AI and Yogesh Wagh against any claims of academic misconduct, plagiarism, fraud, or misrepresentation arising from my use of these deliverables.",
        "hi": "मैं इन डिलिवरेबल्स के मेरे उपयोग से उत्पन्न शैक्षणिक कदाचार, साहित्यिक चोरी, धोखाधड़ी या गलत बयानी के किसी भी दावे के खिलाफ PaperForge AI और योगेश वाघ को क्षतिपूर्ति देने के लिए सहमत हूं।",
    },
    {
        "id": "cb4",
        "en": "I have read, understood, and accept all terms of this Master Service & Asset Transfer Agreement in full. I confirm this digital execution is legally binding under the Information Technology Act, 2000.",
        "hi": "मैंने इस मास्टर सेवा एवं संपत्ति हस्तांतरण अनुबंध की सभी शर्तों को पूरी तरह से पढ़ा, समझा और स्वीकार किया है। मैं पुष्टि करता/करती हूं कि यह डिजिटल निष्पादन सूचना प्रौद्योगिकी अधिनियम, 2000 के तहत कानूनी रूप से बाध्यकारी है।",
    },
]


def generate_contract_id(user_name: str, email: str, paper_title: str) -> str:
    raw = f"{user_name}|{email}|{paper_title}|{datetime.datetime.utcnow().isoformat()}"
    return "MSATA-" + hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def render_msata_step(paper_title: str = "") -> bool:
    """
    Render the full MSATA step.
    Returns True if signed successfully.
    """
    st.markdown("## Step 12 — Master Service & Asset Transfer Agreement")
    st.markdown("*Read carefully. All four checkboxes must be ticked before download unlocks.*")

    # Language toggle
    lang = st.radio("Agreement Language", ["English", "Hindi (हिंदी)", "Both"], horizontal=True, index=2)

    # Display agreement
    if lang in ("English", "Both"):
        with st.expander("📄 MSATA — English Version (Click to read)", expanded=False):
            st.markdown(f"**Paper Title:** {paper_title}")
            st.text(MSATA_ENGLISH)

    if lang in ("Hindi (हिंदी)", "Both"):
        with st.expander("📄 MSATA — हिंदी संस्करण (पढ़ने के लिए क्लिक करें)", expanded=False):
            st.markdown(f"**पेपर शीर्षक:** {paper_title}")
            st.text(MSATA_HINDI)

    st.markdown("---")
    st.markdown("### ✍️ Client Details / क्लाइंट विवरण")

    col1, col2 = st.columns(2)
    with col1:
        user_name  = st.text_input("Full Name / पूरा नाम *", key="msata_name")
        user_email = st.text_input("Email Address / ईमेल पता *", key="msata_email")
    with col2:
        user_phone = st.text_input("Phone (optional) / फोन (वैकल्पिक)", key="msata_phone")
        user_org   = st.text_input("Institution/Organisation / संस्था", key="msata_org")

    st.markdown("---")
    st.markdown("### ☑️ Mandatory Declarations / अनिवार्य घोषणाएं")
    st.markdown("*All four must be checked to proceed / आगे बढ़ने के लिए चारों को चेक करना आवश्यक है*")

    checks = []
    for cb in CHECKBOXES:
        checked = st.checkbox(
            f"**{cb['en']}**\n\n*{cb['hi']}*",
            key=f"msata_{cb['id']}"
        )
        checks.append(checked)

    all_checked = all(checks)
    fields_filled = bool(user_name.strip() and user_email.strip() and "@" in user_email)

    st.markdown("---")

    if not fields_filled:
        st.markdown('<div class="warn-box">⚠️ Please fill in your Full Name and Email to proceed.</div>',
                    unsafe_allow_html=True)

    if not all_checked:
        st.markdown('<div class="warn-box">⚠️ All four declarations must be accepted to unlock download.</div>',
                    unsafe_allow_html=True)

    can_sign = all_checked and fields_filled

    if st.button("✅ I Accept & Execute Agreement — Unlock Download",
                 use_container_width=True, disabled=not can_sign):

        # Generate forensic data
        now_utc = datetime.datetime.utcnow()
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        contract_id = generate_contract_id(user_name, user_email, paper_title)
        session_id  = str(uuid.uuid4())

        forensic_log = {
            "contract_id":      contract_id,
            "contract_version": "MSATA-2026-DIGITAL-SIG",
            "client_name":      user_name,
            "client_email":     user_email,
            "client_phone":     user_phone or "Not provided",
            "client_org":       user_org or "Not provided",
            "paper_title":      paper_title,
            "accepted_at_ist":  now_ist.strftime("%A, %d %B %Y at %I:%M:%S %p IST"),
            "accepted_at_iso":  now_utc.isoformat() + "Z",
            "session_id":       session_id,
            "checkboxes_ticked": [cb["id"] for cb in CHECKBOXES],
            "platform":         "PaperForge AI",
            "licensor":         "Yogesh Wagh",
            "governing_law":    "Maharashtra, Republic of India",
            "it_act":           "Section 3A and 5, IT Act 2000",
            "ip_address":       "Captured server-side",
            "legal_note":       "This digital execution constitutes a legally binding signature under Indian law.",
        }

        st.session_state["msata_forensic"] = forensic_log
        st.session_state["msata_signed"]   = True
        st.session_state["msata_user_name"] = user_name
        st.session_state["msata_user_email"] = user_email

        # Display forensic execution receipt
        st.markdown("---")
        st.markdown("### 🔏 Forensic Execution Receipt / फोरेंसिक निष्पादन रसीद")
        st.markdown('<div class="ok-box">', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Contract ID:** `{contract_id}`")
            st.markdown(f"**Client:** {user_name}")
            st.markdown(f"**Email:** {user_email}")
            st.markdown(f"**Organisation:** {user_org or 'Not provided'}")
        with col2:
            st.markdown(f"**Accepted At (IST):** {forensic_log['accepted_at_ist']}")
            st.markdown(f"**Session ID:** `{session_id[:16]}...`")
            st.markdown(f"**Platform:** PaperForge AI")
            st.markdown(f"**Governing Law:** Maharashtra, India")

        st.markdown(f"**Declarations Accepted:** {' ✅ '.join([cb['id'].upper() for cb in CHECKBOXES])} ✅")
        st.markdown(f"*Executed under Section 3A and 5 of the Information Technology Act, 2000*")
        st.markdown('</div>', unsafe_allow_html=True)

        # Offer forensic receipt download
        receipt_text = f"""PAPERFORGE AI — MSATA EXECUTION RECEIPT
{'='*60}
Contract ID:      {contract_id}
Version:          MSATA-2026-DIGITAL-SIG
{'='*60}
CLIENT DETAILS
Name:             {user_name}
Email:            {user_email}
Phone:            {user_phone or 'Not provided'}
Organisation:     {user_org or 'Not provided'}
{'='*60}
EXECUTION DETAILS
Paper Title:      {paper_title}
Accepted At IST:  {forensic_log['accepted_at_ist']}
Accepted At ISO:  {forensic_log['accepted_at_iso']}
Session ID:       {session_id}
{'='*60}
DECLARATIONS ACCEPTED
CB1: Technical Prototype warranty
CB2: Statistical data acknowledgment  
CB3: Indemnity agreement
CB4: Full terms acceptance
{'='*60}
LEGAL
Platform:         PaperForge AI
Licensor:         Yogesh Wagh
Governing Law:    Maharashtra, Republic of India
IT Act:           Section 3A and 5, Information Technology Act 2000
{'='*60}
This digital execution constitutes a legally binding signature
under Indian law. Disputes resolved via arbitration in Pune.
{'='*60}
"""
        st.download_button(
            "📥 Download Execution Receipt (PDF/TXT)",
            data=receipt_text.encode("utf-8"),
            file_name=f"MSATA_Receipt_{contract_id}.txt",
            mime="text/plain",
            use_container_width=True
        )

        return True

    return False
