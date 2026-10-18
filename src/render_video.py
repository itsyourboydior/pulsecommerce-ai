import os
import subprocess
import math
from PIL import Image, ImageDraw, ImageFont

FFMPEG = r"C:\Users\Besitzer\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
FFPROBE = r"C:\Users\Besitzer\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffprobe.exe"
BASE_DIR = r"C:\Users\Besitzer\Downloads\inventory-agent-step1\inventory-agent"
AUDIO_DIR = os.path.join(BASE_DIR, "video_assets", "audio")
OUT_DIR = os.path.join(BASE_DIR, "video_assets", "scenes")
FINAL_VIDEO = os.path.join(BASE_DIR, "pulsecommerce_explainer_video.mp4")

os.makedirs(OUT_DIR, exist_ok=True)

# Typography helper
def get_font(name="segoeui.ttf", size=32):
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

FONT_HERO = get_font("georgiab.ttf", 52)
FONT_TITLE = get_font("georgia.ttf", 38)
FONT_SUBTITLE = get_font("segoeui.ttf", 26)
FONT_BODY = get_font("segoeui.ttf", 22)
FONT_BOLD = get_font("segoeuib.ttf", 24)
FONT_KEY_NUM = get_font("segoeuib.ttf", 60)
FONT_CODE = get_font("consola.ttf", 19)
FONT_CAPTION = get_font("segoeui.ttf", 18)

# Palette
BG_COLOR = "#FBF9F5"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E8E3DA"
INK = "#17191C"
GRAPHITE = "#4A5568"
SLATE = "#94A3B8"
RUST = "#C2410C"
CORAL = "#DC2626"
AMBER = "#D97706"
MINT = "#059669"
BLUE = "#2563EB"

def get_audio_duration(scene_id):
    path = os.path.join(AUDIO_DIR, f"scene_{scene_id}.mp3")
    out = subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]).decode().strip()
    return float(out)

def draw_header(draw, scene_num, title, show_ui_caption=False):
    draw.rectangle([0, 0, 1920, 68], fill="#FFFFFF")
    draw.line([0, 68, 1920, 68], fill="#EAE6DF", width=1)
    
    # Logo
    draw.ellipse([50, 18, 82, 50], fill=RUST)
    draw.text((95, 18), "PULSECOMMERCE AI", fill=INK, font=get_font("segoeuib.ttf", 22))
    draw.text((360, 20), "|   Autonomous Retail Intelligence", fill=GRAPHITE, font=FONT_BODY)
    
    # Badge
    badge_text = f"SCENE {scene_num} : {title.upper()}"
    draw.rounded_rectangle([1520, 16, 1870, 52], radius=16, fill="#F2EFE9")
    draw.text((1545, 23), badge_text, fill=GRAPHITE, font=get_font("segoeuib.ttf", 15))
    
    if show_ui_caption:
        draw.text((1440, 1025), "Example data, illustrative interface", fill=SLATE, font=FONT_CAPTION)

def draw_subtitle(draw, text):
    draw.rounded_rectangle([140, 940, 1780, 1010], radius=14, fill="#17191C")
    draw.text((180, 958), text[:125], fill="#FFFFFF", font=get_font("segoeui.ttf", 21))

# ==========================================
# SCENE RENDERERS
# ==========================================

def render_scene_1(t, dur):
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 1, "The Problem")
    
    # Left: Boutique Shop illustration
    draw.rounded_rectangle([120, 120, 920, 880], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Storefront Awning
    for i in range(8):
        col = RUST if i % 2 == 0 else "#F7E6D7"
        draw.rectangle([180 + i * 85, 170, 180 + (i + 1) * 85, 250], fill=col)
    draw.text((390, 275), "MARIA'S BOUTIQUE", fill=INK, font=FONT_BOLD)
    
    # Empty Shelves visual
    draw.rounded_rectangle([180, 340, 860, 560], radius=16, fill="#FAF8F5", outline="#E2DDD5")
    draw.line([220, 440, 820, 440], fill="#D5CFC5", width=6)
    draw.line([220, 520, 820, 520], fill="#D5CFC5", width=6)
    
    # Warning callout on empty shelf
    draw.rounded_rectangle([420, 375, 780, 425], radius=12, fill="#FEE2E2", outline=CORAL)
    draw.text((450, 388), "MONDAY: BEST-SELLER OUT OF STOCK", fill=CORAL, font=FONT_BOLD)
    
    # Sad customer / empty cart text
    draw.text((220, 460), "Customers leave empty-handed", fill=GRAPHITE, font=FONT_BODY)
    draw.text((220, 600), "Lost Revenue: $4,200/month", fill=CORAL, font=FONT_BOLD)
    
    # Right: Storage Room full of excess
    draw.rounded_rectangle([1000, 120, 1800, 880], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((1060, 160), "STORAGE ROOM (DEAD INVENTORY)", fill=INK, font=FONT_TITLE)
    
    # Draw boxes
    for row in range(3):
        for col in range(4):
            x = 1060 + col * 165
            y = 250 + row * 130
            draw.rounded_rectangle([x, y, x + 145, y + 110], radius=8, fill="#E6BE8A", outline="#C29B64", width=2)
            draw.line([x, y + 55, x + 145, y + 55], fill="#C29B64", width=2)
            draw.text((x + 25, y + 38), "EXCESS", fill="#8C6228", font=get_font("segoeuib.ttf", 16))
    
    draw.rounded_rectangle([1060, 680, 1740, 820], radius=16, fill="#FEF3C7", outline=AMBER)
    draw.text((1100, 705), "TIED CAPITAL: $14,200 LOCKED ON SHELVES", fill=AMBER, font=FONT_BOLD)
    draw.text((1100, 755), "Maria is not bad at business. She is guessing.", fill=INK, font=FONT_SUBTITLE)
    
    # Subtitle
    sub = "Imagine Maria, who owns a small shop. On Monday, her best-seller runs out. On Friday, storage is full of excess."
    if t > 15:
        sub = "Maria is not bad at business. She is guessing. And every guess costs her real money."
    draw_subtitle(draw, sub)
    return img

def render_scene_2(t, dur):
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 2, "The Idea")
    
    # Title
    draw.text((140, 110), "AN AUTONOMOUS RETAIL OPERATIONS COPILOT", fill=INK, font=FONT_HERO)
    draw.text((140, 180), "Bridging statistical machine learning, LLM reasoning, and human governance.", fill=GRAPHITE, font=FONT_SUBTITLE)
    
    # 4 Flow Steps
    steps = [
        ("1. FORECAST", "Predict weekly demand", "HistGradientBoosting", MINT),
        ("2. DECIDE", "Reorder or Markdown", "Deterministic Rules", BLUE),
        ("3. EXPLAIN", "Plain-English reasoning", "Gemma 4 on AMD", RUST),
        ("4. APPROVE", "Store manager sign-off", "Human-in-the-Loop", AMBER)
    ]
    
    card_w = 360
    card_h = 380
    start_x = 140
    y = 280
    
    progress = min(1.0, t / (dur * 0.75))
    active_idx = int(progress * 4)
    
    for i, (title, sub, tech, col) in enumerate(steps):
        x = start_x + i * (card_w + 50)
        is_active = i <= active_idx
        bg = CARD_BG if is_active else "#F3EFE9"
        border = col if is_active else CARD_BORDER
        
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=20, fill=bg, outline=border, width=3 if is_active else 1)
        draw.ellipse([x + 35, y + 35, x + 85, y + 85], fill=col if is_active else SLATE)
        draw.text((x + 50, y + 42), str(i + 1), fill="#FFFFFF", font=FONT_BOLD)
        
        draw.text((x + 35, y + 115), title, fill=INK if is_active else SLATE, font=FONT_TITLE)
        draw.text((x + 35, y + 175), sub, fill=GRAPHITE if is_active else SLATE, font=FONT_BODY)
        
        draw.rounded_rectangle([x + 35, y + 270, x + card_w - 35, y + 330], radius=12, fill="#F7F5F0")
        draw.text((x + 50, y + 288), tech, fill=col if is_active else SLATE, font=get_font("segoeuib.ttf", 16))
        
        # Arrow connecting cards
        if i < 3:
            ax = x + card_w + 12
            draw.line([ax, y + 190, ax + 26, y + 190], fill=col if is_active else CARD_BORDER, width=4)
    
    # Bottom key callout
    draw.rounded_rectangle([140, 720, 1780, 880], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((190, 755), "Core Principle: Mathematical Precision with Human Control", fill=INK, font=FONT_TITLE)
    draw.text((190, 815), "The agent forecasts what will sell, explains every action in plain language, and waits for approval.", fill=GRAPHITE, font=FONT_BODY)
    
    draw_subtitle(draw, "We built an agent for people like Maria. It forecasts sales, explains decisions, and waits for approval.")
    return img

def render_scene_3(t, dur):
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 3, "How It Works")
    
    draw.text((140, 100), "THE FOUR PILLARS OF PULSECOMMERCE", fill=INK, font=FONT_HERO)
    
    # 4 Pillars
    pillars = [
        ("1. Demand Forecast", "Statistical ML, not LLM", "Measurable & defendable numbers", MINT),
        ("2. Inventory Rules", "Deterministic Engine", "Reorder, discount, or hold", BLUE),
        ("3. Gemma 4 on AMD", "Open model on AMD GPUs", "Plain language PO & email drafts", RUST),
        ("4. Evolus Workflow", "Knowledge Library & MCP", "Manager approval & ERP sync", AMBER)
    ]
    
    active_count = min(4, int((t / (dur * 0.8)) * 4) + 1)
    
    card_w = 370
    card_h = 480
    y = 200
    
    for i in range(4):
        x = 140 + i * (card_w + 40)
        p = pillars[i]
        is_lit = i < active_count
        
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=20, fill=CARD_BG if is_lit else "#F4EFE6", outline=p[3] if is_lit else CARD_BORDER, width=3 if is_lit else 1)
        
        # Pillar badge
        draw.rounded_rectangle([x + 30, y + 30, x + card_w - 30, y + 80], radius=12, fill=p[3] if is_lit else SLATE)
        draw.text((x + 45, y + 42), f"PART {i+1}", fill="#FFFFFF", font=FONT_BOLD)
        
        draw.text((x + 30, y + 110), p[0], fill=INK if is_lit else SLATE, font=FONT_TITLE)
        draw.text((x + 30, y + 175), p[1], fill=p[3] if is_lit else SLATE, font=FONT_BOLD)
        draw.text((x + 30, y + 230), p[2], fill=GRAPHITE if is_lit else SLATE, font=FONT_BODY)
        
        # Decorative progress bar
        draw.line([x + 30, y + 430, x + card_w - 30, y + 430], fill=p[3] if is_lit else CARD_BORDER, width=6)
    
    draw.rounded_rectangle([140, 730, 1780, 890], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((190, 760), "Track 3 Compliance: LLMs do NOT forecast. Classical ML handles numbers; Gemma reasons.", fill=RUST, font=FONT_BOLD)
    draw.text((190, 810), "Evolus orchestrates knowledge retrieval, vendor MOQ constraints, and auditable ERP execution.", fill=GRAPHITE, font=FONT_BODY)
    
    draw_subtitle(draw, "Four parts: Statistical forecasting, policy rules, Google Gemma on AMD, and Evolus workflow orchestration.")
    return img

def render_scene_4(t, dur):
    # Scene 4 [UI]
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 4, "The Forecast", show_ui_caption=True)
    
    # UI Card Window
    draw.rounded_rectangle([140, 100, 1780, 910], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Window Chrome
    draw.ellipse([175, 130, 190, 145], fill="#EF4444")
    draw.ellipse([200, 130, 215, 145], fill="#F59E0B")
    draw.ellipse([225, 130, 240, 145], fill="#10B981")
    draw.text((260, 126), "Demand Forecasting Benchmark Engine  -  Rolling-Origin Evaluation", fill=GRAPHITE, font=get_font("segoeui.ttf", 18))
    draw.line([140, 165, 1780, 165], fill=CARD_BORDER, width=1)
    
    draw.text((190, 195), "EMPIRICAL ACCURACY BENCHMARK (WAPE)", fill=INK, font=FONT_HERO)
    draw.text((190, 265), "Tested on unseen temporal holdout weeks. Lower error = higher forecast accuracy.", fill=GRAPHITE, font=FONT_SUBTITLE)
    
    # Animated Bars
    bar_anim = min(1.0, (t / (dur * 0.6)))
    
    # Baseline Bar
    draw.text((190, 340), "Best Simple Baseline (4-Week Moving Average)", fill=GRAPHITE, font=FONT_BOLD)
    base_w = int(750 * bar_anim)
    draw.rounded_rectangle([190, 385, 190 + base_w, 455], radius=14, fill="#94A3B8")
    draw.text((220 + base_w, 398), "13.5% WAPE", fill=SLATE, font=FONT_TITLE)
    
    # Our Model Bar
    draw.text((190, 485), "Our HistGradientBoosting Model (Python / Scikit-Learn)", fill=INK, font=FONT_BOLD)
    model_w = int(680 * bar_anim)
    draw.rounded_rectangle([190, 530, 190 + model_w, 600], radius=14, fill=MINT)
    draw.text((220 + model_w, 543), "12.4% WAPE", fill=MINT, font=FONT_TITLE)
    
    # Big Highlight Badge
    draw.rounded_rectangle([1180, 340, 1720, 600], radius=20, fill="#ECFDF5", outline=MINT, width=3)
    draw.text((1220, 375), "7.8% BETTER", fill=MINT, font=FONT_KEY_NUM)
    draw.text((1220, 460), "ACCURACY GAIN", fill=INK, font=FONT_TITLE)
    draw.text((1220, 520), "(+21.6% vs Seasonal Naive Baseline)", fill=GRAPHITE, font=FONT_BODY)
    
    # Caption notice
    draw.rounded_rectangle([190, 680, 1720, 780], radius=14, fill="#F8FAFC", outline="#CBD5E1")
    draw.text((230, 705), "Caption: Synthetic test data", fill=RUST, font=FONT_BOLD)
    draw.text((230, 740), "Tested on simulated retail data as a rigorous proof of method and pipeline reproducibility.", fill=GRAPHITE, font=FONT_BODY)
    
    draw_subtitle(draw, "We tested the model on weeks it had never seen. Error is 12.4% vs 13.5% baseline: 7.8% better.")
    return img

def render_scene_5(t, dur):
    # Scene 5 [UI] Table of Actions
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 5, "Proposed Actions", show_ui_caption=True)
    
    draw.rounded_rectangle([140, 100, 1780, 910], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Header
    draw.text((190, 140), "DETERMINISTIC ACTION PROPOSALS", fill=INK, font=FONT_HERO)
    draw.text((190, 210), "Every proposed action shows the mathematical reasoning behind it. Nothing is a black box.", fill=GRAPHITE, font=FONT_SUBTITLE)
    
    # Row 1: Urgent Reorder
    draw.rounded_rectangle([190, 280, 1720, 480], radius=18, fill="#FEF2F2", outline=CORAL, width=2)
    draw.rounded_rectangle([220, 310, 440, 360], radius=10, fill=CORAL)
    draw.text((245, 322), "REORDER URGENT", fill="#FFFFFF", font=FONT_BOLD)
    
    draw.text((470, 315), "SKU001 - Microcontroller Unit (Apex Electronics)", fill=INK, font=FONT_TITLE)
    draw.text((220, 385), "Stock on hand: 12 units   |   Weeks of cover: 0.8 weeks   |   Lead time: 3 weeks", fill=GRAPHITE, font=FONT_BODY)
    draw.text((220, 425), "ACTION: Reorder 420 units (Vendor MOQ: 100 units)   |   Status: Imminent stockout risk", fill=CORAL, font=FONT_BOLD)
    
    # Row 2: Discount Markdown
    draw.rounded_rectangle([190, 520, 1720, 720], radius=18, fill="#FFFBEB", outline=AMBER, width=2)
    draw.rounded_rectangle([220, 550, 440, 600], radius=10, fill=AMBER)
    draw.text((255, 562), "DISCOUNT 20%", fill="#FFFFFF", font=FONT_BOLD)
    
    draw.text((470, 555), "SKU014 - Seasonal Knitwear (Lumina Apparel)", fill=INK, font=FONT_TITLE)
    draw.text((220, 625), "Stock on hand: 340 units   |   Weeks of cover: 18.2 weeks   |   Overstock threshold: 12 weeks", fill=GRAPHITE, font=FONT_BODY)
    draw.text((220, 665), "ACTION: Apply 20% promotional discount   |   Target: Free $4,500 in locked working capital", fill=AMBER, font=FONT_BOLD)
    
    # Summary note
    draw.rounded_rectangle([190, 750, 1720, 830], radius=12, fill="#F1F5F9")
    draw.text((230, 775), "Mathematical Z-score: 1.65 (95% Service Level)  -  100% Auditable Rule Engine", fill=INK, font=FONT_BOLD)
    
    draw_subtitle(draw, "Example actions: Product 1 almost out of stock -> Reorder 420 units urgent. Product 2 has 18w cover -> Discount 20%.")
    return img

def render_scene_6(t, dur):
    # Scene 6 [UI] Gemma on AMD
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 6, "Gemma on AMD", show_ui_caption=True)
    
    draw.rounded_rectangle([140, 100, 1780, 910], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.text((190, 130), "GOOGLE GEMMA 4 ON AMD INSTINCT GPUS", fill=INK, font=FONT_HERO)
    draw.text((190, 200), "Evolus workflow bridge contextualizes vendor policies & drafts supplier POs.", fill=GRAPHITE, font=FONT_SUBTITLE)
    
    # Left: Process flow box
    draw.rounded_rectangle([190, 270, 880, 700], radius=18, fill="#F8FAFC", outline="#CBD5E1", width=2)
    draw.text((230, 300), "EVOLUS AGENT PIPELINE", fill=INK, font=FONT_TITLE)
    
    steps = [
        "1. Ingest Proposal (actions.json)",
        "2. Retrieve Supplier Rules (Net 30, MOQ 100)",
        "3. Route to AMD vLLM (Gemma 4 31B/26B)",
        "4. Synthesize Plain-English Rationale",
        "5. Draft Supplier Email & PO Confirmation"
    ]
    for i, s in enumerate(steps):
        y_pos = 370 + i * 55
        draw.ellipse([230, y_pos, 255, y_pos + 25], fill=RUST)
        draw.text((270, y_pos), s, fill=INK, font=FONT_BODY)
    
    # Right: Live Output Card
    draw.rounded_rectangle([920, 270, 1720, 700], radius=18, fill="#1E293B")
    draw.text((960, 300), "OUTPUT: GEMMA 4 EXECUTIVE REASONING", fill="#38BDF8", font=FONT_BOLD)
    
    gemma_text = (
        "REASONING:\n"
        "SKU001 has only 0.8 weeks of cover remaining against a 3-week lead time.\n"
        "Pacific Semiconductor MOQ requires minimum 100 units under Net 30.\n\n"
        "SUPPLIER PO DRAFT:\n"
        "Subject: Urgent Purchase Order - SKU001 (420 Units)\n"
        "Dear Vendor Partner,\n"
        "Please issue PO-20261018 confirmation for 420 units under Net 30 terms."
    )
    draw.text((960, 360), gemma_text, fill="#E2E8F0", font=FONT_CODE)
    
    # Metrics
    draw.rounded_rectangle([190, 730, 920, 840], radius=14, fill="#ECFDF5", outline=MINT)
    draw.text((230, 750), "4 SECONDS", fill=MINT, font=FONT_KEY_NUM)
    draw.text((540, 765), "Per explanation on AMD Instinct", fill=INK, font=FONT_BOLD)
    
    draw.rounded_rectangle([960, 730, 1720, 840], radius=14, fill="#EFF6FF", outline=BLUE)
    draw.text((1000, 750), "40 ACTIONS", fill=BLUE, font=FONT_KEY_NUM)
    draw.text((1340, 765), "Processed in under 2 minutes", fill=INK, font=FONT_BOLD)
    
    draw_subtitle(draw, "Evolus starts the workflow. Gemma on AMD reads supplier rules, explains the action, and writes the email draft.")
    return img

def render_scene_7(t, dur):
    # Scene 7 [UI] Human Approval
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 7, "Human Governance", show_ui_caption=True)
    
    draw.rounded_rectangle([140, 100, 1780, 910], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.text((190, 140), "HUMAN-IN-THE-LOOP APPROVAL GATE", fill=INK, font=FONT_HERO)
    draw.text((190, 210), "Nothing runs without a person. Autonomous financial commitments are strictly prevented.", fill=GRAPHITE, font=FONT_SUBTITLE)
    
    # Decision Card 1: Approved Order
    draw.rounded_rectangle([190, 290, 920, 680], radius=20, fill="#F0FDF4", outline=MINT, width=2)
    draw.text((230, 330), "REORDER APPROVAL", fill=MINT, font=FONT_TITLE)
    draw.text((230, 390), "SKU001 - 420 Units ($18,900)", fill=INK, font=FONT_BOLD)
    draw.text((230, 430), "Store manager reviews supplier draft & lead time.", fill=GRAPHITE, font=FONT_BODY)
    
    # Big Green Approve Button
    draw.rounded_rectangle([230, 480, 880, 560], radius=14, fill=MINT)
    draw.text((450, 502), "APPROVE ORDER", fill="#FFFFFF", font=FONT_TITLE)
    
    draw.rounded_rectangle([230, 580, 880, 640], radius=10, fill="#DCFCE7")
    draw.text((260, 598), "MCP Ledger: PO-89214 Dispatched to ERP", fill=MINT, font=FONT_BOLD)
    
    # Decision Card 2: Rejected Discount
    draw.rounded_rectangle([980, 290, 1720, 680], radius=20, fill="#FEF2F2", outline=CORAL, width=2)
    draw.text((1020, 330), "DISCOUNT REJECTION", fill=CORAL, font=FONT_TITLE)
    draw.text((1020, 390), "SKU014 - 20% Markdown Proposal", fill=INK, font=FONT_BOLD)
    draw.text((1020, 430), "Store manager evaluates minimum gross margin floor.", fill=GRAPHITE, font=FONT_BODY)
    
    # Big Red Reject Button
    draw.rounded_rectangle([1020, 480, 1680, 560], radius=14, fill=CORAL)
    draw.text((1250, 502), "REJECT ACTION", fill="#FFFFFF", font=FONT_TITLE)
    
    draw.rounded_rectangle([1020, 580, 1680, 640], radius=10, fill="#FEE2E2")
    draw.text((1050, 598), "Audit Trail: Margin below 18% target floor", fill=CORAL, font=FONT_BOLD)
    
    # Callout
    draw.rounded_rectangle([190, 730, 1720, 840], radius=16, fill="#17191C")
    draw.text((580, 765), "THE AGENT NEVER ACTS ALONE.", fill="#FFFFFF", font=FONT_HERO)
    
    draw_subtitle(draw, "The manager approves the order (sent via MCP). They reject the discount because margin is too low. Never acts alone.")
    return img

def render_scene_8(t, dur):
    # Scene 8 Value and Limits
    img = Image.new("RGB", (1920, 1080), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, 8, "Value & Limits")
    
    draw.text((140, 110), "EMPOWERING MERCHANTS WITH VERIFIABLE AI", fill=INK, font=FONT_HERO)
    draw.text((140, 180), "For Maria, that means fewer empty shelves and less money locked in slow products.", fill=GRAPHITE, font=FONT_SUBTITLE)
    
    # 3 Summary Cards
    summaries = [
        ("1. Eliminate Stockouts", "Statistical safety stock prevents missed sales and protects customer loyalty.", MINT),
        ("2. Unlock Dead Capital", "Automated proactive markdowns liberate trapped cash from stagnant inventory.", AMBER),
        ("3. Audited Governance", "Mathematical classical ML for numbers; Google Gemma 4 on AMD for transparent oversight.", BLUE)
    ]
    
    for i, (title, desc, col) in enumerate(summaries):
        y = 260 + i * 150
        draw.rounded_rectangle([140, y, 1780, y + 125], radius=16, fill=CARD_BG, outline=col, width=2)
        draw.ellipse([180, y + 38, 230, y + 88], fill=col)
        draw.text((198, y + 46), str(i + 1), fill="#FFFFFF", font=FONT_TITLE)
        
        draw.text((260, y + 30), title, fill=INK, font=FONT_TITLE)
        draw.text((260, y + 78), desc, fill=GRAPHITE, font=FONT_BODY)
    
    # Honest limit callout
    draw.rounded_rectangle([140, 730, 1780, 860], radius=16, fill="#FFFBEB", outline=AMBER, width=2)
    draw.text((190, 755), "TRANSPARENT STATEMENT OF LIMITS & NEXT MILESTONES", fill=AMBER, font=FONT_BOLD)
    draw.text((190, 800), "Our forecast benchmark evaluated on synthetic retail data. The immediate next step is live ERP API integration.", fill=GRAPHITE, font=FONT_BODY)
    
    draw_subtitle(draw, "For Maria: fewer empty shelves, less dead capital. Next step: live inventory integration. Thank you for watching.")
    return img

SCENE_RENDERERS = {
    1: render_scene_1,
    2: render_scene_2,
    3: render_scene_3,
    4: render_scene_4,
    5: render_scene_5,
    6: render_scene_6,
    7: render_scene_7,
    8: render_scene_8
}

def render_and_encode_scene(scene_id, fps=24):
    audio_path = os.path.join(AUDIO_DIR, f"scene_{scene_id}.mp3")
    duration = get_audio_duration(scene_id)
    # Pad duration slightly by 1.2s for clean breathing room
    total_dur = duration + 1.2
    total_frames = int(total_dur * fps)
    
    out_scene_mp4 = os.path.join(OUT_DIR, f"scene_{scene_id}.mp4")
    print(f"Rendering Scene {scene_id} ({total_frames} frames @ {fps}fps, dur {total_dur:.2f}s)...", flush=True)
    
    cmd = [
        FFMPEG, "-y",
        "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1920x1080",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        out_scene_mp4
    ]
    
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    renderer = SCENE_RENDERERS[scene_id]
    
    for f in range(total_frames):
        t = f / fps
        frame_img = renderer(t, total_dur)
        p.stdin.write(frame_img.tobytes())
        
    p.stdin.close()
    p.wait()
    
    if p.returncode != 0:
        print(f"Error encoding scene {scene_id}", flush=True)
        raise RuntimeError("Encoding failed")
    print(f"Scene {scene_id} successfully saved to {out_scene_mp4}", flush=True)
    return out_scene_mp4

def assemble_final_video():
    scenes = []
    for i in range(1, 9):
        scenes.append(render_and_encode_scene(i))
        
    concat_list = os.path.join(OUT_DIR, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for s in scenes:
            clean_path = s.replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
            
    print("Concatenating all scenes into final video...")
    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        FINAL_VIDEO
    ]
    subprocess.check_call(cmd)
    print(f"SUCCESS! Master 5-Minute Explainer Video generated at:\n{FINAL_VIDEO}")

if __name__ == "__main__":
    assemble_final_video()
