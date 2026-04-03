"""
generate_ppt.py
Generates a rich, professional PowerPoint presentation for:
  Resume Analyzer AI - RAG Platform for HR & Recruitment
"""
# coding: utf-8
import io
import os
import requests as _requests

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
import copy
from lxml import etree

# ─── Colour Palette ────────────────────────────────────────────────────────────
C_NAVY   = RGBColor(0x0D, 0x1B, 0x2A)   # deep navy bg
C_DARK   = RGBColor(0x11, 0x2A, 0x46)   # dark blue panel
C_ACCENT = RGBColor(0x00, 0xB4, 0xD8)   # vivid cyan accent
C_TEAL   = RGBColor(0x0A, 0xF5, 0xCB)   # teal highlight
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
C_LTGREY = RGBColor(0xCC, 0xE5, 0xFF)   # light blue-grey text
C_GOLD   = RGBColor(0xFF, 0xD1, 0x66)   # warm gold bullets
C_GREEN  = RGBColor(0x06, 0xD6, 0xA0)

# Slide dimensions – 16:9 widescreen
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# ─── Helpers ────────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> RGBColor:
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def add_solid_fill(shape, color: RGBColor):
    """Fill a shape with a solid colour."""
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_gradient_fill(shape, c1: RGBColor, c2: RGBColor, angle_deg: int = 135):
    """Add a two-stop linear gradient to a shape via raw XML."""
    spPr = shape.fill._element
    # remove existing fill
    for child in list(spPr):
        if child.tag.endswith('}solidFill') or child.tag.endswith('}gradFill') or child.tag.endswith('}noFill'):
            spPr.remove(child)
    nsmap = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    grad = etree.SubElement(spPr, f'{{{nsmap}}}gradFill')
    gsLst = etree.SubElement(grad, f'{{{nsmap}}}gsLst')
    for pos, col in [(0, c1), (100000, c2)]:
        gs = etree.SubElement(gsLst, f'{{{nsmap}}}gs', pos=str(pos))
        srgb = etree.SubElement(gs, f'{{{nsmap}}}srgbClr', val=f"{col[0]:02X}{col[1]:02X}{col[2]:02X}")
    lin = etree.SubElement(grad, f'{{{nsmap}}}lin', ang=str(angle_deg * 60000), scaled="0")


def set_slide_background(slide, prs, color: RGBColor):
    """Set the slide background to a solid colour."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text_box(slide, text, left, top, width, height,
                  font_name="Calibri", font_size=14, bold=False, italic=False,
                  color=C_WHITE, align=PP_ALIGN.LEFT, word_wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def add_rect(slide, left, top, width, height, color: RGBColor, radius=None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.line.fill.background()   # no border
    add_solid_fill(shape, color)
    return shape


def add_bullet_slide(prs, title_text, bullets, icon="▸", number_bullets=False):
    """Generic bullet-list slide."""
    slide_layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)

    # header bar
    bar = add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)

    # accent line under header
    accent = add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)

    # title
    add_text_box(slide, title_text,
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    # bullet background panel
    panel = add_rect(slide, Inches(0.4), Inches(1.4), Inches(12.5), Inches(5.8), C_DARK)

    # bullets
    y = Inches(1.6)
    for i, b in enumerate(bullets):
        prefix = f"{i+1}." if number_bullets else icon
        bullet_full = f"  {prefix}  {b}"
        tb = add_text_box(slide, bullet_full,
                          Inches(0.6), y, Inches(12.0), Inches(0.7),
                          font_size=17, color=C_LTGREY, font_name="Calibri")
        # colour the prefix
        y += Inches(0.68)

    return slide


def add_kv_slide(prs, title_text, items: list[tuple]):
    """Key-value / two-column style slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)

    add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)
    add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, title_text,
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    col_w = Inches(5.8)
    col_gap = Inches(0.5)
    padding = Inches(0.5)
    row_h = Inches(1.05)
    start_y = Inches(1.5)

    for idx, (key, val) in enumerate(items):
        col = idx % 2
        row = idx // 2
        x = Inches(0.5) + col * (col_w + col_gap)
        y = start_y + row * row_h

        card = add_rect(slide, x, y, col_w, Inches(0.9), C_DARK)
        # key label (coloured)
        add_text_box(slide, key, x + Inches(0.15), y + Inches(0.05), Inches(2.5), Inches(0.4),
                     font_size=13, bold=True, color=C_ACCENT, font_name="Calibri")
        # value
        add_text_box(slide, val, x + Inches(0.15), y + Inches(0.42), col_w - Inches(0.3), Inches(0.45),
                     font_size=12, color=C_LTGREY, font_name="Calibri")

    return slide


def download_image(url: str) -> bytes | None:
    """Download image bytes from URL."""
    try:
        resp = _requests.get(url, timeout=25,
                            headers={"User-Agent": "Mozilla/5.0 (compatible)"})
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print("  [WARN] Could not download %s: %s" % (url[:60], e))
        return None


def add_image_slide(prs, title_text, img_source, caption="", subtitle=""):
    """Slide with a single large image."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)

    add_rect(slide, 0, 0, SLIDE_W, Inches(1.1), C_DARK)
    add_rect(slide, 0, Inches(1.1), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, title_text,
                 Inches(0.5), Inches(0.12), Inches(10), Inches(0.85),
                 font_size=28, bold=True, color=C_WHITE, font_name="Calibri Light")
    if subtitle:
        add_text_box(slide, subtitle,
                     Inches(0.5), Inches(0.82), Inches(10), Inches(0.35),
                     font_size=13, italic=True, color=C_LTGREY)

    # Add image
    img_data = None
    if isinstance(img_source, str) and img_source.startswith("http"):
        img_data = download_image(img_source)
    elif isinstance(img_source, (str, os.PathLike)) and os.path.exists(img_source):
        with open(img_source, "rb") as f:
            img_data = f.read()

    if img_data:
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.open(io.BytesIO(img_data))
            # Convert to PNG to support webp format in PowerPoint
            png_stream = io.BytesIO()
            pil_img.save(png_stream, format="PNG")
            img_stream = png_stream
            
            img_w, img_h = pil_img.size
            ratio = img_w / img_h
            avail_w = Inches(12.0)
            avail_h = Inches(5.5)
            if ratio > avail_w / avail_h:
                w = avail_w
                h = int(avail_w / ratio)
            else:
                h = avail_h
                w = int(avail_h * ratio)
            cx = (SLIDE_W - w) // 2
            cy = Inches(1.3) + (avail_h - h) // 2
            img_stream.seek(0)
            slide.shapes.add_picture(img_stream, cx, cy, w, h)
        except Exception as e:
            print(f"  [WARN] Could not add image: {e}")
            add_text_box(slide, "[Image could not be loaded]",
                         Inches(2), Inches(3), Inches(9), Inches(1),
                         font_size=14, color=C_ACCENT, align=PP_ALIGN.CENTER)
    else:
        add_text_box(slide, "[Image could not be loaded]",
                     Inches(2), Inches(3), Inches(9), Inches(1),
                     font_size=14, color=C_ACCENT, align=PP_ALIGN.CENTER)

    if caption:
        add_text_box(slide, caption,
                     Inches(0.5), Inches(7.0), Inches(12), Inches(0.35),
                     font_size=11, italic=True, color=RGBColor(0x88, 0xAA, 0xCC),
                     align=PP_ALIGN.CENTER)
    return slide


def add_title_slide(prs):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)

    # Large gradient background bar
    bar = add_rect(slide, 0, Inches(1.8), SLIDE_W, Inches(4.0), C_DARK)

    # top accent stripe
    add_rect(slide, 0, Inches(1.8), SLIDE_W, Inches(0.06), C_ACCENT)
    # bottom accent stripe
    add_rect(slide, 0, Inches(5.74), SLIDE_W, Inches(0.06), C_TEAL)

    # Decorative circle top-right
    circle = slide.shapes.add_shape(9, Inches(10.5), Inches(0.1), Inches(3.5), Inches(3.5))
    circle.fill.solid()
    circle.fill.fore_color.rgb = RGBColor(0x00, 0x6D, 0x9B)
    circle.line.fill.background()

    circle2 = slide.shapes.add_shape(9, Inches(11.2), Inches(0.5), Inches(2.5), Inches(2.5))
    circle2.fill.solid()
    circle2.fill.fore_color.rgb = C_ACCENT
    circle2.line.fill.background()

    # slide number badge
    add_rect(slide, Inches(0.3), Inches(0.3), Inches(1.0), Inches(0.45), C_ACCENT)
    add_text_box(slide, "01", Inches(0.3), Inches(0.3), Inches(1.0), Inches(0.45),
                 font_size=15, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER)

    # Main title
    add_text_box(slide, "RESUME ANALYZER AI",
                 Inches(0.6), Inches(2.1), Inches(10), Inches(1.3),
                 font_size=52, bold=True, color=C_WHITE, font_name="Calibri Light")

    # Subtitle
    add_text_box(slide, "A Smart AI Tool to Read and Search Resumes",
                 Inches(0.6), Inches(3.5), Inches(11), Inches(0.6),
                 font_size=22, color=C_ACCENT, font_name="Calibri")

    add_text_box(slide, "for HR and Recruitment",
                 Inches(0.6), Inches(4.1), Inches(9), Inches(0.5),
                 font_size=22, color=C_LTGREY, font_name="Calibri")

    # tags
    tags = ["AI Powered", "Smart Search", "Easy to Use", "HR Tech"]
    tx = Inches(0.6)
    for tag in tags:
        tb = add_rect(slide, tx, Inches(5.1), Inches(1.3), Inches(0.38), RGBColor(0x01, 0x43, 0x6B))
        add_text_box(slide, tag, tx + Inches(0.05), Inches(5.1), Inches(1.2), Inches(0.38),
                     font_size=11, bold=True, color=C_ACCENT, align=PP_ALIGN.CENTER)
        tx += Inches(1.45)

    # footer
    add_text_box(slide, "Smart HR Assistant",
                 Inches(0), Inches(7.0), SLIDE_W, Inches(0.4),
                 font_size=11, color=RGBColor(0x44, 0x66, 0x88),
                 align=PP_ALIGN.CENTER)

    return slide


def add_section_divider(prs, number, title, subtitle=""):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)

    add_rect(slide, 0, 0, Inches(0.12), SLIDE_H, C_ACCENT)

    num_box = add_rect(slide, Inches(0.5), Inches(2.6), Inches(2.0), Inches(1.8), C_DARK)
    add_text_box(slide, number,
                 Inches(0.5), Inches(2.6), Inches(2.0), Inches(1.8),
                 font_size=72, bold=True, color=C_ACCENT,
                 align=PP_ALIGN.CENTER, font_name="Calibri Light")

    add_text_box(slide, title,
                 Inches(2.9), Inches(2.9), Inches(9.5), Inches(1.2),
                 font_size=38, bold=True, color=C_WHITE, font_name="Calibri Light")

    if subtitle:
        add_text_box(slide, subtitle,
                     Inches(2.9), Inches(4.2), Inches(9.5), Inches(0.6),
                     font_size=18, color=C_LTGREY, font_name="Calibri")

    add_rect(slide, Inches(2.9), Inches(4.0), Inches(7.0), Inches(0.04), C_TEAL)
    return slide


# ─── UML Diagram URLs ────────────────────────────────────────────────────────────
UML_ARCH     = "https://kroki.io/mermaid/png/eJyNUcFOwzAMvecrVpwaF_YFOGBC07SJsT1g12GT1C6uS1KntN0Q_x0nK9oOCASy4yfv-T3bwTVMtyc80-wW6IuLQNNw9i44R_2INURaqoMy_wZmkTftGacI2Aclxr8SUr6jEJ7iA2ZsO-gEImQzVN1pL_1j_wtd12MwkmVz0oZpA4u_bF1R1yN0YF6FE1-2m_y7-6v22E1A17P_CjR4h1_WvVzW2i6-oOqL2lIN8fCUS3SDE0VdI2AieZCQ1XQlr_I5EAbK1Wk9PmLXSkfwCAStsAM9q4Xq7Yr1u8IBYqHb0TzK7rBMeJ1t_j_OQ9ngGTaV9tTqZ_gBU6usRwdJu3as-wWUZ2oOrr7-R9W1_RqbAov119df-oMM2b4NuWv7u-0kcb9f0R_iYJ0ZSp10YspGK-zG00x9EDXdPl1kUu_046k5WbLf_Nq28rXl9rBKVwM="
UML_CLASS    = "https://kroki.io/mermaid/png/eJyNUDtqw0AQ7H0Vg-vEBoQnEAy4SAyB5AHuYlZ7S7IlbVfClfTvHcdOCEG8Hsy85jHDHhU-s7v0G3D4jYDO3t364B11R6who1INav4NTCFv2nPOATh6JsH_SEhxQQle4wNG7DrqACLUhXp12kv__H1b1_UQjGTdnHTLtIHFX1auqOsROjCvwo4vmw1-8E_1sZuA3tP0LdDgFX5f93JZa7v4gnrMakM1_vEhl-gMJwrbCBhPHiRkI13Jg3wOhIFO9Wk9PmLXSkdwAAS9sAe90ELN7or1r8IBYsHbST_K7rBM-DjV_x-PUDZ4QjOVvVrxM_yAqVUWooOkY8e4X0B5IHNw_fU_q27s19gUWKy_tv7Sz2TIXWzIWzu_2k4S9_sd_SEeVmVGTheVmHKhFXbhYaa-EJVuw2OR1N_1w7E5WLLd_Ni08qXl9lhLdwM="
UML_ACTIVITY = "https://kroki.io/mermaid/png/eJyNUktqhDAQ3vMUwdoL6IIR9w2EgV7A0kUw6jQkMeow6UQ8T-kR2tt4ErUzY0N104T8__nmK5qI2y1L0OwaUOMdAZV-t_rBG6qOaIRYS2VQ8U0whoRpThmFv1B0iK-SUnqgEC7xBSM2LTUDRMgL1fLUlv76e5vHcS0IydIppR_SNBTxsnFBXc_QgHkXTnzebPCdf00fewvoXaa_Ag3u4ed5L-e5toiPqHmjNlRDPBzlHL3CQ2G3EZCefUjIaLqSD1kOQYBS1VqO95i1UhE8AkFLbEBPa6J6OWH1u8IBQqPbUX2U9rBMeB4N__vnkDR4hkm13TXyGX7AWCpt0EKSqWGsa0BxIH1w7fVPqp_GNTIFFMuvtb70MxhyGxtyaOeny07ierujP8SBM0Opk01M2WCFXXmYyQZEodv8LJPyt3pwqA6WbIu_Z618bbk5LNLtC9mSGBE="
UML_USECASE  = "https://kroki.io/mermaid/png/eJyNUEtrwzAMvvtXCDs1hXWDHTiMMNph9DB2sE0V21pL3Bq1g1D23ydJlzHQ1eCTnr6n_aH2jE9yF2kEGr8wUEmbFm_JMxoLWhLWRhm0xTVwYcHS3oKjgEOkEvwaEaUblMA1XmDEtrM2IFLeqNanevFv3yvP8zoSia32Z_l13MPkr_B31M0IB2ZZ2ONpu8EP_mV-NBNQez7-BWrM4A-4N3Bf28UXNGRR29DDH6Gco1WcKLYSMJl9SIhqurIP-T0EB8pl2uDxHp2UFsEBCEZiAxpWG9XLDet_CgeIA--m-Ki8YZnwetv-n7xANXjBvA170sNneAJTawtoIelsGNsFkBu0Dq65-WeVm_k1VQQG019df-kVYyjtYkgu1nnadgL7-w38ASbWjSFUSiW0bNDCWnjqKQbixvH1v0b037XD0Tta4s3_tWn4bf3t60N1B6qB4_o="

# Screenshot paths (from previous conversation brain)
BRAIN_DIR = r"C:\Users\akash\.gemini\antigravity\brain\8785f474-d18a-4c2e-b3af-44e056456138"
IMG_DASHBOARD = os.path.join(BRAIN_DIR, "resume_ai_dashboard_1774971052143.png")
IMG_QA        = os.path.join(BRAIN_DIR, "rag_qa_final_working_1774959788127.webp")
IMG_MATCHER   = os.path.join(BRAIN_DIR, "rag_app_qa_fixed_1774958912851.webp")

# ─── Build Presentation ─────────────────────────────────────────────────────────

def build_ppt(output_path="Project_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    print("Building slide 1 - Title slide...")
    add_title_slide(prs)

    # ─── Slide 2: Project Overview ──────────────────────────────────────────────
    print("Building slide 2 - Project Overview...")
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)
    add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, "2. Project Overview",
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    desc = ("Resume Analyzer AI is a state-of-the-art web application designed to significantly "
            "reduce the time HR professionals spend evaluating candidates.")
    add_text_box(slide, desc,
                 Inches(0.5), Inches(1.4), Inches(12.3), Inches(0.9),
                 font_size=16, color=C_LTGREY, font_name="Calibri")

    add_text_box(slide, "Our smart AI platform helps recruiters save time. You can:",
                 Inches(0.5), Inches(2.35), Inches(12.3), Inches(0.5),
                 font_size=15, bold=True, color=C_ACCENT)

    bullets = [
        "Upload many resumes at once and let the system read them.",
        "Ask questions about candidates like you're chatting with a human.",
        "Quickly find the best people for the job based on their skills and experience.",
    ]
    y = Inches(2.95)
    for b in bullets:
        add_text_box(slide, f"  ▸  {b}", Inches(0.7), y, Inches(11.8), Inches(0.6),
                     font_size=16, color=C_LTGREY)
        y += Inches(0.65)

    # Three info cards at bottom
    card_data = [
        ("⏱  Fast", "Reads instantly"),
        ("🔍  Smart", "Understands context"),
        ("🔒  Private", "Your data is safe"),
        ("🤖  AI-Powered", "Smart Answers"),
    ]
    cx = Inches(0.5)
    for label, sub in card_data:
        add_rect(slide, cx, Inches(5.4), Inches(2.9), Inches(1.7), C_DARK)
        add_text_box(slide, label, cx + Inches(0.15), Inches(5.5), Inches(2.6), Inches(0.55),
                     font_size=17, bold=True, color=C_TEAL)
        add_text_box(slide, sub, cx + Inches(0.15), Inches(6.1), Inches(2.6), Inches(0.4),
                     font_size=13, color=C_LTGREY)
        cx += Inches(3.1)

    # ─── Slide 3: Core Modules ──────────────────────────────────────────────────
    print("Building slide 3 - Core Modules...")
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)
    add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, "3. How It's Built (Simple View)",
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    modules = [
        ("🔐  Secure Login",
         "Keeps everything safe so only authorized HR managers can see the resumes.",
         RGBColor(0x00, 0xB4, 0xD8)),
        ("📄  Document Reader",
         "Opens PDFs and Word docs, reads the text, and remembers who it belongs to.",
         RGBColor(0x06, 0xD6, 0xA0)),
        ("🧠  Smart Memory",
         "Stores knowledge in a way the AI can quickly search through to answer your questions.",
         RGBColor(0xFF, 0xD1, 0x66)),
        ("🖥  Easy-to-use Dashboard",
         "A friendly website that's simple to navigate and remembers what you're working on.",
         RGBColor(0xFF, 0x6B, 0x6B)),
    ]

    positions = [
        (Inches(0.4),  Inches(1.4)),
        (Inches(6.8),  Inches(1.4)),
        (Inches(0.4),  Inches(4.2)),
        (Inches(6.8),  Inches(4.2)),
    ]

    for (mx, my), (mod_title, mod_desc, accent_col) in zip(positions, modules):
        add_rect(slide, mx, my, Inches(6.0), Inches(2.5), C_DARK)
        add_rect(slide, mx, my, Inches(0.08), Inches(2.5), accent_col)  # left accent bar
        add_text_box(slide, mod_title, mx + Inches(0.25), my + Inches(0.15), Inches(5.5), Inches(0.65),
                     font_size=17, bold=True, color=C_WHITE)
        add_text_box(slide, mod_desc, mx + Inches(0.25), my + Inches(0.85), Inches(5.5), Inches(1.5),
                     font_size=13, color=C_LTGREY)

    # ─── Slide 4: System Architecture (UML) ────────────────────────────────────
    print("Building slide 4 - System Architecture...")
    add_image_slide(prs, "4. System Overview",
                    UML_ARCH,
                    caption="A simple view of how the website talks to the Brain (AI) to get your answers.",
                    subtitle="How information flows from you to the AI and back")

    # ─── Slide 5: Class Diagram ─────────────────────────────────────────────────
    print("Building slide 5 - UML Class Diagram...")
    add_image_slide(prs, "5. System Components",
                    UML_CLASS,
                    caption="How different parts of the system work together to help you.",
                    subtitle="The main building blocks: System, Document Reader, Memory, and AI")

    # ─── Slide 6: Activity Diagram ──────────────────────────────────────────────
    print("Building slide 6 - Activity Diagram...")
    add_image_slide(prs, "6. How You Use It (Step-by-Step)",
                    UML_ACTIVITY,
                    caption="A visual guide of a typical task on the website.",
                    subtitle="The typical flow from uploading a resume to getting an answer")

    # ─── Slide 7: Use Case & Sequence ──────────────────────────────────────────
    print("Building slide 7 - Use Case Diagram...")
    add_image_slide(prs, "7. What You Can Do",
                    UML_USECASE,
                    caption="A quick look at the main actions you can perform on the platform.",
                    subtitle="The main features available to HR users")

    # ─── Slide 8: Database Design ───────────────────────────────────────────────
    print("Building slide 8 - Database Design...")
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)
    add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, "8. How We Store Your Data",
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    add_text_box(slide, "The platform saves your progress securely on the server so you can resume work anytime without losing data.",
                 Inches(0.5), Inches(1.38), Inches(12.3), Inches(0.45),
                 font_size=14, color=C_LTGREY)

    tables = [
        ("Working Sessions", [
            ("id", "Unique ID"),
            ("hr_username", "Who is logged in"),
            ("session_name", "Chat name"),
            ("created_at", "Date & Time"),
        ]),
        ("Saved Resumes", [
            ("id", "Unique ID"),
            ("session_id", "Link to Session"),
            ("filename", "Name of file"),
            ("file_path", "Where it is stored"),
        ]),
        ("Chat History", [
            ("id", "Unique ID"),
            ("session_id", "Link to Session"),
            ("role", "User or AI"),
            ("content", "Message Text"),
            ("timestamp", "Date & Time"),
        ]),
    ]

    tx = Inches(0.35)
    for tbl_name, cols in tables:
        tw = Inches(4.15)
        add_rect(slide, tx, Inches(2.0), tw, Inches(0.45), C_ACCENT)
        add_text_box(slide, f"  {tbl_name}", tx, Inches(2.0), tw, Inches(0.45),
                     font_size=15, bold=True, color=C_NAVY)
        ty = Inches(2.5)
        for col, dtype in cols:
            add_rect(slide, tx, ty, tw, Inches(0.5), C_DARK)
            add_text_box(slide, col, tx + Inches(0.1), ty + Inches(0.05), Inches(1.5), Inches(0.42),
                         font_size=12, bold=True, color=C_TEAL)
            add_text_box(slide, dtype, tx + Inches(1.55), ty + Inches(0.05), Inches(2.4), Inches(0.42),
                         font_size=11, color=C_LTGREY)
            add_rect(slide, tx, ty + Inches(0.49), tw, Inches(0.01), RGBColor(0x22, 0x44, 0x66))
            ty += Inches(0.5)
        tx += Inches(4.45)

    # FK arrows (text labels)
    add_text_box(slide, "↑  Link", Inches(4.55), Inches(3.1), Inches(0.6), Inches(0.4),
                 font_size=10, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)
    add_text_box(slide, "↑  Link", Inches(9.0), Inches(3.1), Inches(0.6), Inches(0.4),
                 font_size=10, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

    # ─── Slide 9: Frontend Development ─────────────────────────────────────────
    print("Building slide 9 - Frontend Development...")
    add_bullet_slide(prs, "9. The Website Interface",
                     [
                         "Beautiful Design: Looks modern and professional, similar to your favorite top-tier apps.",
                         "Smooth Experience: Drag and drop resumes and switch between modes without waiting for the page to reload.",
                         "Neat Text Formatting: Makes the answers from the AI easy to read with bullet points and bold text.",
                         "Lightning Fast: Built to be incredibly quick when navigating the platform.",
                         "Remembers Your Work: All your uploaded resumes and chat history are saved automatically.",
                     ])

    # ─── Slide 10: Backend Development ─────────────────────────────────────────
    print("Building slide 10 - Backend Development...")
    add_bullet_slide(prs, "10. Behind the Scenes (The Server)",
                     [
                         "The Traffic Cop: Directs your clicks securely to the right places.",
                         "File Reader: Easily opens and understands both PDF and Word document formats.",
                         "Data Separation: Keeps each HR user's uploaded resumes separate and secure.",
                         "Reliable Storage: Saves important data so nothing gets lost if your computer shuts down.",
                         "Strong Security: Ensures no one else can sneak into your private data.",
                     ])

    # ─── Slide 11: Working Process of RAG ──────────────────────────────────────
    print("Building slide 11 - RAG Process...")
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)
    add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, "11. How the Smart AI Works",
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    add_text_box(slide,
                 "Our AI is designed to be truthful: it looks for answers strictly within the resumes you uploaded, preventing 'made-up' facts.",
                 Inches(0.5), Inches(1.38), Inches(12.3), Inches(0.5),
                 font_size=14, color=C_LTGREY)

    steps = [
        ("1", "READING",
         "The system reads every uploaded resume carefully and organizes the details so it's easy to search later.",
         C_ACCENT),
        ("2", "SEARCHING",
         'You ask a question like "Who knows Python?" – and the system quickly grabs only the resumes that match.',
         C_TEAL),
        ("3", "ANSWERING",
         "The AI looks at the matches and gives you a simple, direct answer, and tells you exactly which resume it got it from.",
         C_GOLD),
    ]

    sx = Inches(0.35)
    for num, step_title, step_desc, col in steps:
        sw = Inches(4.1)
        add_rect(slide, sx, Inches(2.1), sw, Inches(4.8), C_DARK)
        add_rect(slide, sx, Inches(2.1), sw, Inches(0.06), col)

        # circle number
        circle = slide.shapes.add_shape(9, sx + Inches(0.15), Inches(2.25), Inches(0.55), Inches(0.55))
        circle.fill.solid()
        circle.fill.fore_color.rgb = col
        circle.line.fill.background()
        add_text_box(slide, num, sx + Inches(0.15), Inches(2.25), Inches(0.55), Inches(0.55),
                     font_size=16, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER)

        add_text_box(slide, step_title,
                     sx + Inches(0.85), Inches(2.3), Inches(3.0), Inches(0.55),
                     font_size=18, bold=True, color=col)

        add_text_box(slide, step_desc,
                     sx + Inches(0.2), Inches(3.0), Inches(3.7), Inches(3.8),
                     font_size=13, color=C_LTGREY, word_wrap=True)

        # arrow
        if num != "3":
            add_text_box(slide, "→",
                         sx + sw + Inches(0.05), Inches(4.0), Inches(0.35), Inches(0.6),
                         font_size=24, bold=True, color=C_ACCENT, align=PP_ALIGN.CENTER)
        sx += Inches(4.45)

    # ─── Slide 12: Technology Stack ─────────────────────────────────────────────
    print("Building slide 12 - Technology Stack...")
    add_kv_slide(prs, "12. Technology We Use (Simplified)", [
        ("Frontend",         "Website / Look & Feel (HTML, CSS, JavaScript)"),
        ("Backend Framework","Server / Traffic Controller (Python, Flask)"),
        ("Database",         "Secure Saving (SQLite)"),
        ("NLP / Embeddings", "AI Smart Search (sentence-transformers)"),
        ("LLM Pipeline",     "Answering Engine (HuggingFace AI)"),
        ("Doc Processing",   "PDF and Word Readers (PyPDF2, python-docx)"),
    ])

    # ─── Slide 13: Advantages ───────────────────────────────────────────────────
    print("Building slide 13 - Advantages...")
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)
    add_rect(slide, 0, 0, SLIDE_W, Inches(1.25), C_DARK)
    add_rect(slide, 0, Inches(1.25), SLIDE_W, Inches(0.04), C_ACCENT)
    add_text_box(slide, "13. Why This Platform Helps You",
                 Inches(0.5), Inches(0.2), Inches(12), Inches(0.9),
                 font_size=30, bold=True, color=C_WHITE, font_name="Calibri Light")

    advantages = [
        ("⏱  Saves You Hours",
         "Instead of reading dozens of resumes manually, the system does it for you instantly.",
         C_ACCENT),
        ("🎯  Fair Choice",
         "Focuses purely on the candidate's actual skills listed in their resume, removing biases.",
         C_TEAL),
        ("🔒  Keeps Data Safe",
         "Your resumes are safe and locked down so only you can see your data.",
         C_GOLD),
        ("💾  Pick Up Later",
         "You can log off, and when you return, all your resumes and chats will still be there.",
         C_GREEN),
        ("✨  Easy and Beautiful",
         "It is fast, responsive, and as simple to use as your favorite modern apps.",
         RGBColor(0xFF, 0x6B, 0x6B)),
    ]

    positions_adv = [
        (Inches(0.35), Inches(1.4)),
        (Inches(6.85), Inches(1.4)),
        (Inches(0.35), Inches(3.5)),
        (Inches(6.85), Inches(3.5)),
        (Inches(3.6),  Inches(5.6)),
    ]

    for (ax, ay), (adv_title, adv_desc, col) in zip(positions_adv, advantages):
        aw = Inches(6.0)
        ah = Inches(1.8)
        add_rect(slide, ax, ay, aw, ah, C_DARK)
        add_rect(slide, ax, ay, aw, Inches(0.05), col)
        add_text_box(slide, adv_title, ax + Inches(0.15), ay + Inches(0.1), aw - Inches(0.3), Inches(0.55),
                     font_size=15, bold=True, color=col)
        add_text_box(slide, adv_desc, ax + Inches(0.15), ay + Inches(0.7), aw - Inches(0.3), Inches(1.0),
                     font_size=12, color=C_LTGREY)

    # ─── Slides 14-16: UI Screenshots ──────────────────────────────────────────
    print("Building slide 14 - UI Dashboard screenshot...")
    add_image_slide(prs, "14. A Look at the Website: Main View",
                    IMG_DASHBOARD,
                    caption="A modern and clean screen that greets you when you log in.",
                    subtitle="Clear options to look at one resume, many resumes, or see your past work.")

    print("Building slide 15 - RAG Q&A screenshot...")
    add_image_slide(prs, "15. A Look at the Website: Asking Questions",
                    IMG_QA,
                    caption="The AI gives easy-to-read answers and clearly shows which file it read.",
                    subtitle="Chatting with the AI to get answers from the uploaded resumes.")

    print("Building slide 16 - Candidate Matcher screenshot...")
    add_image_slide(prs, "16. A Look at the Website: Finding the Best Match",
                    IMG_MATCHER,
                    caption="Use simple controls to narrow down exactly who you are looking for.",
                    subtitle="Easily filter candidates by specific skills and years of experience.")

    # ─── Final Slide: Thank You ──────────────────────────────────────────────────
    print("Building final slide - Thank You...")
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)
    set_slide_background(slide, prs, C_NAVY)

    add_rect(slide, 0, Inches(2.5), SLIDE_W, Inches(2.5), C_DARK)
    add_rect(slide, 0, Inches(2.5), SLIDE_W, Inches(0.05), C_ACCENT)
    add_rect(slide, 0, Inches(4.95), SLIDE_W, Inches(0.05), C_TEAL)

    add_text_box(slide, "Thank You",
                 Inches(0), Inches(2.7), SLIDE_W, Inches(1.3),
                 font_size=60, bold=True, color=C_WHITE,
                 align=PP_ALIGN.CENTER, font_name="Calibri Light")

    add_text_box(slide, "HR Assistant — Making Recruitment Easier with AI",
                 Inches(0), Inches(4.1), SLIDE_W, Inches(0.6),
                 font_size=18, color=C_LTGREY,
                 align=PP_ALIGN.CENTER)

    tags2 = ["Smart AI", "Fast", "Secure Saving", "Easy Chat", "Automated", "HR Tech"]
    tx = Inches(1.5)
    for tag in tags2:
        add_rect(slide, tx, Inches(5.4), Inches(1.6), Inches(0.4), RGBColor(0x01, 0x43, 0x6B))
        add_text_box(slide, tag, tx + Inches(0.05), Inches(5.4), Inches(1.5), Inches(0.4),
                     font_size=12, bold=True, color=C_ACCENT, align=PP_ALIGN.CENTER)
        tx += Inches(1.75)

    # ─── Save ───────────────────────────────────────────────────────────────────
    prs.save(output_path)
    print("\n[DONE] Presentation saved to: %s" % output_path)


if __name__ == "__main__":
    output = r"c:\Users\akash\.gemini\antigravity\scratch\RAG-Resume-Analyzer\Project_Presentation.pptx"
    build_ppt(output)
