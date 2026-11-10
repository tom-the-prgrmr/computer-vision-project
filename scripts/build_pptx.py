"""Generate docs/slides/presentation.pptx from the same content as
docs/slides/presentation.html — real numbers from docs/problem_statement.md,
not re-derived. Build tool, not part of the app/runtime — needs
`pip install python-pptx` (not in requirements.txt, deliberately not a
runtime dependency). Re-run after editing this file to regenerate the
.pptx: `python scripts/build_pptx.py`.
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---- palette (light theme, matches docs/slides/presentation.html) ----
BG = RGBColor(0xF3, 0xF5, 0xEE)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x1E, 0x2A, 0x20)
INK_SOFT = RGBColor(0x56, 0x63, 0x4F)
LINE = RGBColor(0xD7, 0xDE, 0xCB)
PASS = RGBColor(0x2E, 0x7D, 0x52)
PASS_SOFT = RGBColor(0xE4, 0xF0, 0xE4)
ISSUE = RGBColor(0xC4, 0x48, 0x2E)
ISSUE_SOFT = RGBColor(0xF7, 0xE4, 0xDD)

FONT_DISPLAY = "Georgia"  # Fraunces not available in PowerPoint -> closest serif fallback
FONT_BODY = "Calibri"
FONT_MONO = "Consolas"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]


def new_slide():
    s = prs.slides.add_slide(BLANK)
    bg = s.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    return s


def textbox(slide, l, t, w, h):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tb.text_frame.word_wrap = True
    return tb


def set_run(run, text, size, color, font=FONT_BODY, bold=False, italic=False, spacing=None):
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = font
    run.font.bold = bold
    run.font.italic = italic


def eyebrow(slide, text, top=Inches(0.5)):
    tb = textbox(slide, Inches(0.7), top, Inches(11.9), Inches(0.45))
    p = tb.text_frame.paragraphs[0]
    r1 = p.add_run()
    set_run(r1, "[ ", 13, PASS, FONT_MONO, bold=True)
    r2 = p.add_run()
    set_run(r2, text, 13, INK_SOFT, FONT_MONO, bold=False)
    r3 = p.add_run()
    set_run(r3, " ]", 13, PASS, FONT_MONO, bold=True)
    return tb


def heading(slide, text, top=Inches(1.05), width=Inches(11.9), size=32):
    tb = textbox(slide, Inches(0.7), top, width, Inches(1.5))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run()
    set_run(r, text, size, INK, FONT_DISPLAY, bold=True)
    return tb


def bullet_list(slide, items, left=Inches(0.7), top=Inches(2.2), width=Inches(6.6), size=15):
    tb = textbox(slide, left, top, width, Inches(4.5))
    tf = tb.text_frame
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(14)
        r = p.add_run()
        set_run(r, "—  " + item, size, INK_SOFT, FONT_BODY)
    return tb


def tag_card(slide, left, top, width, height, tag, tag_color, tag_bg, title, desc):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = SURFACE
    box.line.color.rgb = LINE
    box.line.width = Pt(1)
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.22)

    tagbox = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left + Inches(0.22), top + Inches(0.2), Inches(1.5), Inches(0.32))
    tagbox.fill.solid()
    tagbox.fill.fore_color.rgb = tag_bg
    tagbox.line.fill.background()
    tagbox.shadow.inherit = False
    tp = tagbox.text_frame
    tp.margin_left = Inches(0.08)
    tp.margin_top = 0
    tp.margin_bottom = 0
    trun = tp.paragraphs[0].add_run()
    set_run(trun, tag.upper(), 10, tag_color, FONT_MONO, bold=True)

    p1 = tf.paragraphs[0]
    p1.text = ""
    for _ in range(2):
        tf.add_paragraph()
    p_title = tf.paragraphs[1]
    r_title = p_title.add_run()
    set_run(r_title, title, 18, INK, FONT_DISPLAY, bold=True)
    p_desc = tf.paragraphs[2]
    r_desc = p_desc.add_run()
    set_run(r_desc, desc, 12, INK_SOFT, FONT_BODY)
    return box


def stat_tile(slide, left, top, width, height, big, cap, issue=False):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = SURFACE
    box.line.color.rgb = LINE
    box.line.width = Pt(1)
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_top = Inches(0.18)
    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, big, 34, ISSUE if issue else PASS, FONT_DISPLAY, bold=True)
    p2 = tf.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, cap, 11, INK_SOFT, FONT_MONO)
    return box


def callout(slide, left, top, width, height, label, text):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = ISSUE_SOFT
    box.line.color.rgb = ISSUE
    box.line.width = Pt(1.5)
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_top = Inches(0.2)
    tf.margin_right = Inches(0.2)
    p1 = tf.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, label.upper(), 10, ISSUE, FONT_MONO, bold=True)
    p2 = tf.add_paragraph()
    p2.space_before = Pt(6)
    r2 = p2.add_run()
    set_run(r2, text, 12.5, INK, FONT_BODY)
    return box


def lesson_row(slide, left, top, width, tag, text):
    tagbox = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(0.65), Inches(0.3))
    tagbox.fill.background()
    tagbox.line.color.rgb = PASS
    tagbox.line.width = Pt(1)
    tagbox.shadow.inherit = False
    tp = tagbox.text_frame
    tp.margin_left = Inches(0.05)
    tp.margin_top = 0
    tr = tp.paragraphs[0].add_run()
    set_run(tr, tag, 9, PASS, FONT_MONO, bold=True)

    tb = textbox(slide, left + Inches(0.85), top - Inches(0.03), width - Inches(0.85), Inches(0.5))
    r = tb.text_frame.paragraphs[0].add_run()
    set_run(r, text, 12.5, INK_SOFT, FONT_BODY)
    return tb


def table(slide, left, top, width, height, headers, rows, win_rows=()):
    n_rows = len(rows) + 1
    n_cols = len(headers)
    gt = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    t = gt.table
    for c, htext in enumerate(headers):
        cell = t.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = BG
        p = cell.text_frame.paragraphs[0]
        r = p.add_run()
        set_run(r, htext.upper(), 11, INK_SOFT, FONT_MONO, bold=True)
    for ri, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = t.cell(ri, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PASS_SOFT if ri in win_rows else SURFACE
            p = cell.text_frame.paragraphs[0]
            r = p.add_run()
            color = PASS if ri in win_rows else INK
            set_run(r, str(val), 13, color, FONT_BODY, bold=(ri in win_rows))
    return gt


def chip(slide, left, top, text, size=14):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, Inches(0.2), Inches(0.5))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0xEA, 0xEE, 0xE1)
    box.line.color.rgb = LINE
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.08)
    p = tf.paragraphs[0]
    r = p.add_run()
    set_run(r, text, size, INK, FONT_MONO, bold=True)
    box.width = Inches(0.35 + len(text) * 0.095)
    return box


# ============================================================ Slide 0 — Cover
s = new_slide()
eyebrow(s, "COMPUTER VISION MODULE · AI ENGINEER K08-0226", top=Inches(1.6))
tb = textbox(s, Inches(0.7), Inches(2.15), Inches(11), Inches(1.8))
r = tb.text_frame.paragraphs[0].add_run()
set_run(r, "Yoga Pose Detection & Form Scoring", 44, INK, FONT_DISPLAY, bold=True)
tb2 = textbox(s, Inches(0.7), Inches(3.55), Inches(9.5), Inches(1.2))
r2 = tb2.text_frame.paragraphs[0].add_run()
set_run(r2, "Phát hiện + phân loại tư thế yoga bằng YOLOv8 tự train, chấm điểm form "
            "bằng góc khớp MediaPipe, deploy public thật với HTTPS và camera trên iPhone.",
        16, INK_SOFT, FONT_BODY)
chip(s, Inches(0.7), Inches(4.9), "demo · computer-vision-project.pthieu290998.workers.dev", size=12)

# ============================================================ Slide 1 — Bài toán
s = new_slide()
eyebrow(s, "MỞ ĐẦU · BÀI TOÁN")
heading(s, "Một model train được, làm cả định vị lẫn phân loại", width=Inches(7.2), size=28)
bullet_list(s, [
    "Input: ảnh/video học viên đang tập yoga",
    "Output: vị trí + tên tư thế, đánh giá form đúng/sai, gợi ý sửa",
    "Ràng buộc đề bài: bắt buộc 1 model classification/detection/segmentation tự train",
    "Lựa chọn: YOLOv8 detection — vừa localize vừa classify trong 1 bước, hỗ trợ nhiều học viên/khung hình cùng lúc",
], top=Inches(2.3), width=Inches(7.2))
stat_tile(s, Inches(8.3), Inches(2.3), Inches(4.3), Inches(2.0), "5", "LỚP TƯ THẾ\nbridge · downward · plank\nshoulderstand · tree")

# ============================================================ Slide 2 — Kiến trúc
s = new_slide()
eyebrow(s, "KIẾN TRÚC · 2 LỚP ĐỘC LẬP")
heading(s, "Model train được, model mượn, và luật tay — không trộn lẫn", width=Inches(11.9), size=26)
cw = Inches(3.9)
gap = Inches(0.25)
tag_card(s, Inches(0.7), Inches(2.6), cw, Inches(3.2), "trained", PASS, PASS_SOFT,
         "YOLOv8 (ONNX)", "Detect + classify tư thế trong 1 bước. Rubric mục 1-4, 7 chấm điểm lớp này.")
tag_card(s, Inches(0.7) + cw + gap, Inches(2.6), cw, Inches(3.2), "pretrained", RGBColor(0x8A, 0x6D, 0x1F), RGBColor(0xF5, 0xEC, 0xD2),
         "MediaPipe Pose", "33 keypoint mỗi box, dùng nguyên off-the-shelf, không train lại, không tính accuracy riêng.")
tag_card(s, Inches(0.7) + 2 * (cw + gap), Inches(2.6), cw, Inches(3.2), "rule-based", RGBColor(0x5A, 0x4A, 0x9C), RGBColor(0xEA, 0xE4, 0xF7),
         "score_pose()", "So góc khớp với POSE_RULES hiệu chỉnh thủ công. Rubric mục 6 — \u201cý tưởng riêng\u201d.")

# ============================================================ Slide 3 — Dữ liệu
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 01 + 12 · DỮ LIỆU")
heading(s, "README ghi \u201ckhông augmentation\u201d — thực tế 58% ảnh test là bản sao ảnh train", width=Inches(7.4), size=24)
bullet_list(s, [
    "v1: 5 lớp, format YOLO có sẵn bbox, nguồn Roboflow \u201cYOLO YOGA Dataset\u201d, 1013 ảnh",
    "Rò rỉ: ảnh valid/test là bản lật ngang hoặc crop/zoom của ảnh train — phát hiện bằng dHash (kể cả bản lật) + ORB/RANSAC, gom nhóm bằng union-find",
    "Chia lại theo nhóm: 703 / 156 / 154 ảnh, không nhóm nào nằm ở hai split; manifest commit vào repo",
    "Augmentation: fliplr bật, flipud tắt, degrees giới hạn",
], top=Inches(2.55), width=Inches(7.2), size=14)
stat_tile(s, Inches(8.3), Inches(2.55), Inches(4.3), Inches(1.5), "59/101", "ẢNH TEST GỐC TRÙNG NHÓM VỚI ẢNH TRAIN", issue=True)
stat_tile(s, Inches(8.3), Inches(4.2), Inches(4.3), Inches(1.5), "552", "NHÓM ẢNH ĐỘC LẬP TRONG 1013 ẢNH")

# ============================================================ Slide 4 — Training
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 02-03 + 12 · TRAINING")
heading(s, "Rò rỉ thổi phồng mAP@0.5:0.95 khoảng 6 điểm", size=30)
tb = textbox(s, Inches(0.7), Inches(1.95), Inches(11), Inches(0.4))
r = tb.text_frame.paragraphs[0].add_run()
set_run(r, "model yolov8n.pt  ·  seed 42  ·  epochs 50  ·  imgsz 640  ·  augmentation ON", 13, INK_SOFT, FONT_MONO)
table(s, Inches(0.7), Inches(2.5), Inches(11.5), Inches(2.0),
      ["Model · tập test", "mAP@0.5", "mAP@0.5:0.95"],
      [["Model cũ · 101 ảnh test gốc (rò rỉ)", "0.994", "0.833"],
       ["Model cũ · 42 ảnh test sạch", "0.995", "0.774"],
       ["Train lại trên split sạch · 154 ảnh test mới", "0.991", "0.824"]],
      win_rows={3})
tb2 = textbox(s, Inches(0.7), Inches(4.8), Inches(11.5), Inches(0.6))
r2 = tb2.text_frame.paragraphs[0].add_run()
set_run(r2, "mAP@0.5 gần như không đổi — ở IoU 0.5, v1 vẫn dễ. Ablation augmentation ON/OFF (chọn ON) đo trên test bị rò rỉ, chỉ để tham khảo.", 12, INK_SOFT, FONT_BODY, italic=True)

# ============================================================ Slide 5 — Error analysis
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 04 + 12 · ERROR ANALYSIS")
heading(s, "Test sạch lộ ra lỗi thật", width=Inches(7.4), size=28)
bullet_list(s, [
    "Test: 7/154 ảnh lỗi, toàn bộ là shoulderstand — bỏ sót, nhầm sang bridge/downward. Ảnh đồ hoạ, nhiều người chồng lấn, người nhỏ ngược sáng",
    "EigenCAM trên ảnh sai: ảnh nhiều người — kích hoạt trải ra nền thay vì vào người",
    "OOD 45 ảnh, đủ 5 lớp (Kaggle + Wikimedia Commons, không trùng Roboflow): lỗi tập trung ở plank — side plank, ảnh ngoài trời đông người",
    "Lỗi test và lỗi OOD rơi vào hai lớp khác nhau → test cùng phân bố không đại diện cho người dùng thật",
], top=Inches(2.25), width=Inches(7.2), size=14)
stat_tile(s, Inches(8.3), Inches(2.25), Inches(4.3), Inches(1.5), "7/154", "ẢNH TEST SẠCH CÓ LỖI (CONF 0.5)", issue=True)
stat_tile(s, Inches(8.3), Inches(3.9), Inches(4.3), Inches(1.5), "82.2%", "37/45 ẢNH OOD ĐÚNG")

# ============================================================ Slide 6 — Feedback loop
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 12 · FEEDBACK LOOP")
heading(s, "Đổi đúng 1 yếu tố, đo trước/sau — và nó không cải thiện", width=Inches(11.8), size=26)
table(s, Inches(0.7), Inches(2.2), Inches(11.5), Inches(1.5),
      ["Run (cùng seed, cùng dữ liệu)", "mAP@0.5:0.95", "Ảnh test lỗi", "OOD"],
      [["yolov8n · trước", "0.824", "7", "82.2%"],
       ["yolov8s · sau (model lớn hơn)", "0.816", "10", "71.1%"]],
      win_rows={1})
callout(s, Inches(0.7), Inches(4.0), Inches(11.5), Inches(2.0), "Kết luận trung thực",
        "Giữ yolov8n. Giả thuyết: model gấp ~3.5 lần tham số khớp quá mức với 703 ảnh train (1 seed, chưa kiểm chứng). "
        "Thay đổi này không nhắm đúng pattern lỗi quan sát được — hướng tiếp: augmentation scale cho người nhỏ, thêm ảnh side plank. "
        "PROD giữ model cũ (OOD 40/45) vì không model train lại nào hơn.")

# ============================================================ Slide 7 — Form scoring
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 06 · Ý TƯỞNG RIÊNG")
heading(s, "Góc khớp thật hiệu chỉnh ngưỡng, không đoán số", width=Inches(11.5), size=27)
stat_tile(s, Inches(0.7), Inches(2.4), Inches(3.3), Inches(1.5), "14/15", "ẢNH MẪU THẬT ĐÚNG FORM")
stat_tile(s, Inches(0.7), Inches(4.05), Inches(3.3), Inches(1.5), "5/5", "CASE LANDMARK TỔNG HỢP — PHÁT HIỆN ĐÚNG")
callout(s, Inches(4.3), Inches(2.4), Inches(8.3), Inches(3.15), "2 hạn chế ghi nhận công khai",
        "MediaPipe kém tin cậy trên tư thế lộn ngược, nền tương phản thấp — landmark detect sai. "
        "Góc chiếu 2D bị méo khi camera chụp xiên — hạn chế cố hữu của ảnh đơn không có depth, không phải bug.")

# ============================================================ Slide 8 — Hiệu năng PROD
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 07 + 12 · HIỆU NĂNG TRÊN PROD")
heading(s, "Stress test thẳng vào Render, không đo trên máy train", width=Inches(11.8), size=26)
table(s, Inches(0.7), Inches(2.2), Inches(11.5), Inches(2.6),
      ["Đồng thời", "Trước", "Threadpool", "+ giới hạn 2"],
      [["1", "0% · 6.3 s", "5% · 6.6 s *", "0% · 6.1 s"],
       ["2", "0% · 10.9 s", "0% · 8.5 s", "0% · 9.3 s"],
       ["4", "10% · 42.1 s", "0% · 13.3 s", "0% · 16.4 s"],
       ["8", "25% · 49.1 s", "100% lỗi 502", "0% · 31.1 s"]],
      win_rows={4})
tb2 = textbox(s, Inches(0.7), Inches(5.05), Inches(11.5), Inches(1.2))
tb2.text_frame.word_wrap = True
r2 = tb2.text_frame.paragraphs[0].add_run()
set_run(r2, "Tỉ lệ lỗi · p95, 20 request mỗi mức. Trước: async def chặn event loop. Threadpool: nhanh hơn ở 2-4 đồng thời nhưng ở 8 đồng thời "
            "process chết (nghi hết RAM 512 MB; local: peak 555 → 362 MB). Giới hạn 2 ảnh cùng lúc: 80/80 thành công, đổi lại request xếp hàng lâu hơn. "
            "Cold start thật ~33s. * 1 lỗi 502 chưa giải thích được.", 12, INK_SOFT, FONT_BODY, italic=True)

# ============================================================ Slide 9 — Web demo & Deploy
s = new_slide()
eyebrow(s, "GIAI ĐOẠN 08-09 · WEB DEMO & DEPLOY")
heading(s, "2 origin thật, HTTPS thật, camera thật trên iPhone", width=Inches(11.8), size=26)
tb = textbox(s, Inches(0.7), Inches(2.35), Inches(5.4), Inches(2.5))
r = tb.text_frame.paragraphs[0].add_run()
set_run(r, "iPhone Safari  →  Cloudflare Pages (frontend tĩnh)  →  Render "
            "(backend Docker, free) — CORS qua env ALLOWED_ORIGINS.",
        14, INK_SOFT, FONT_BODY)
tbl = textbox(s, Inches(6.5), Inches(2.15), Inches(6.1), Inches(0.4))
rl = tbl.text_frame.paragraphs[0].add_run()
set_run(rl, "3 BUG MÔI TRƯỜNG THẬT, ĐÃ SỬA", 12, INK_SOFT, FONT_MONO, bold=True)
lesson_row(s, Inches(6.5), Inches(2.65), Inches(6.1), "FIX", "Render chọn nhầm runtime Python thay vì Docker → chọn đúng Environment")
lesson_row(s, Inches(6.5), Inches(3.25), Inches(6.1), "FIX", "Thiếu libGL.so.1 trên container Linux tối giản → thêm apt package")
lesson_row(s, Inches(6.5), Inches(3.85), Inches(6.1), "FIX", "iOS Safari đẩy camera vào native fullscreen player → webkit-playsinline")

# ============================================================ Slide 10 — Lỗi & bài học
s = new_slide()
eyebrow(s, "LỖI & BÀI HỌC")
heading(s, "Bài học lớn nhất: kiểm tra dữ liệu và đo ở đúng chỗ", width=Inches(11.8), size=27)
lesson_row(s, Inches(0.7), Inches(2.55), Inches(11.5), "DATA", "Tin README của dataset mà không kiểm tra → 58% ảnh test là bản sao ảnh train, mọi kết luận Giai đoạn 2-5 dựa trên số ảo.")
lesson_row(s, Inches(0.7), Inches(3.2), Inches(11.5), "PERF", "Đo hiệu năng trên máy train không thấy lỗi thật — chỉ khi bắn thẳng vào Render mới lộ event loop bị chặn và process chết.")
lesson_row(s, Inches(0.7), Inches(3.85), Inches(11.5), "FIX", "mediapipe \u2265 1.0 bỏ hẳn solutions.pose (API cũ) → pin đúng bản còn API, xác nhận qua lỗi build thật.")
lesson_row(s, Inches(0.7), Inches(4.5), Inches(11.5), "FIX", "3 bug deploy (runtime Docker, libGL, iOS fullscreen) — chẩn đoán trực tiếp từ log/screenshot thật.")

# ============================================================ Slide 11 — Demo
s = new_slide()
eyebrow(s, "TRÌNH DIỄN TRỰC TIẾP", top=Inches(2.6))
tb = textbox(s, Inches(0.7), Inches(3.1), Inches(11.9), Inches(1.0))
p = tb.text_frame.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
r = p.add_run()
set_run(r, "Camera thật · HTTPS thật · kết quả thật", 32, INK, FONT_DISPLAY, bold=True)
chip(s, Inches(0.7), Inches(4.1), "computer-vision-project.pthieu290998.workers.dev", size=14)
tb2 = textbox(s, Inches(0.7), Inches(4.9), Inches(10.5), Inches(0.8))
r2 = tb2.text_frame.paragraphs[0].add_run()
set_run(r2, "Quay trực tiếp lúc trình bày — camera trên điện thoại thật qua URL public, "
            "không dùng ảnh chụp màn hình dựng sẵn.", 14, INK_SOFT, FONT_BODY)

# ============================================================ Slide 12 — Kết
s = new_slide()
eyebrow(s, "KẾT")
heading(s, "Cảm ơn — câu hỏi?", size=32)
bullet_list(s, [
    "Repo: github.com/tom-the-prgrmr/computer-vision-project",
    "Demo live: computer-vision-project.pthieu290998.workers.dev",
    "Kiến trúc: docs/architecture.md",
    "Chi tiết 7 mục rubric: docs/problem_statement.md",
], top=Inches(2.3), width=Inches(11))

OUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "slides" / "presentation.pptx"
prs.save(str(OUT_PATH))
print(f"Saved {len(prs.slides._sldIdLst)} slides -> {OUT_PATH}")
