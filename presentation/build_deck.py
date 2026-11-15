#!/usr/bin/env python3
"""Build editable PowerPoint and vector PDF slides from the selected paper data.

Run from any directory with Python 3.8+ and presentation/requirements.txt.
All slide objects, including charts and diagrams, are native editable shapes.
The PDF uses the same coordinates and text as the PowerPoint.
"""
import csv
import json
import re
from pathlib import Path
from lxml import etree

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'presentation'
W, H = 13.333333, 7.5
BG, INK, MUTED = 'FFFFFF', '202428', '60676D'
BLUE, MID, PALE, GRID = '234F77', '8B949D', 'A8BFD1', 'D3D8DC'
FONT = 'Arial'
FONT_ROOT = Path('/usr/share/fonts/gnu-free')
for label, filename in [('regular', 'FreeSans.ttf'), ('bold', 'FreeSansBold.ttf')]:
    pdfmetrics.registerFont(TTFont(label, str(FONT_ROOT / filename)))


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


selection = json.loads((ROOT / 'paper/experiment_data.json').read_text())
assert selection['status'] == 'validated'
paths = {k: ROOT / v for k, v in selection['files'].items()}
validation = json.loads(paths['validation'].read_text())
assert validation['status'] == 'validated'
assert validation['main_points'] == 12 and validation['simulator_processes'] == 107
width = {(int(r['n']), int(r['width'])): r for r in rows(paths['width'])}
bandwidth = {(int(r['width']), int(r['bandwidth'])): r for r in rows(paths['bandwidth'])}
graph = {int(r['width']): r for r in rows(paths['graph'])}
warm = {(r['input_case'], int(r['width']), r['mode'], int(r['call'])): r for r in rows(paths['warm'])}

def repeated_us(w, call):
    return int(warm['unchanged', w, 'timed', call]['offload_ticks']) / 1e6

slowdown = 100 * (repeated_us(4, 1) / repeated_us(1, 1) - 1)


def num(n, w, key):
    return float(width[n, w][key])


def reduction(n, key):
    return 100 * (1 - num(n, 4, key) / num(n, 1, key))


def benefit(b):
    return 100 * (1 - float(bandwidth[4, b]['offload_ticks']) /
                  float(bandwidth[1, b]['offload_ticks']))


deck = Presentation()
deck.slide_width, deck.slide_height = Inches(W), Inches(H)
deck.core_properties.title = 'Output-Column Reuse in a Coherent GEMM Accelerator'
deck.core_properties.subject = 'Completed coherent-GEMM framework and performance-resource study'
deck.core_properties.author = 'Yasir Mahmud; Rasin Mohammed Ihtemam; Mohyeu Hussain'
# Set the actual Office theme as well as the visible slide styling.
for part in deck.part.package.iter_parts():
    if part.content_type == 'application/vnd.openxmlformats-officedocument.theme+xml':
        theme=etree.fromstring(part.blob)
        theme.set('name','Academic White')
        ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
        for latin in theme.xpath('.//a:fontScheme/a:majorFont/a:latin | .//a:fontScheme/a:minorFont/a:latin',namespaces=ns):
            latin.set('typeface','Arial')
        scheme=theme.find('.//a:clrScheme',ns)
        scheme.set('name','Academic White')
        for name,value in [('dk1',INK),('lt1',BG),('dk2',BLUE),('lt2','F5F6F7'),
                           ('accent1',BLUE),('accent2',MID),('accent3',PALE),
                           ('accent4','6F7A83'),('accent5','A5AAAE'),('accent6','D8DCDF')]:
            element=scheme.find('a:'+name,ns)[0]
            element.set('lastClr' if element.tag.endswith('sysClr') else 'val',value)
        part._blob=etree.tostring(theme,xml_declaration=True,encoding='UTF-8',standalone=True)
pdf = canvas.Canvas(str(OUT / 'project_presentation.pdf'), pagesize=(W * 72, H * 72))
pdf.setTitle(deck.core_properties.title)
pdf.setAuthor(deck.core_properties.author)
notes, audit = [], []
CONTENT = json.loads((OUT/'content.json').read_text())
MAIN_SLIDES = sum(not item['backup'] for item in CONTENT)


class Slide:
    def __init__(self, index, title, title_page=False):
        self.entry = CONTENT[index-1]
        self.slide = deck.slides.add_slide(deck.slide_layouts[6])
        self.index = index
        self.records = []
        self.backup = self.entry['backup']
        self.sources = self.entry['sources']
        self.script = self.entry['script']
        self.seconds = self.entry['seconds']
        self.title = title
        self.rect(0, 0, W, H, BG)
        if not title_page:
            self.text(title, .72, .52, 11.90, 29, color=BLUE)
            self.line(.72, 1.25, 12.61, 1.25, GRID, .8)

    def rect(self, x, y, w, h, color, stroke=None):
        assert x >= 0 and y >= 0 and x+w <= W+.002 and y+h <= H+.002, (x,y,w,h)
        shape = self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(color)
        if stroke:
            shape.line.color.rgb = RGBColor.from_string(stroke)
            shape.line.width = Pt(.8)
        else:
            shape.line.fill.background()
        pdf.setFillColor(HexColor('#'+color))
        pdf.setStrokeColor(HexColor('#'+(stroke or color)))
        pdf.setLineWidth(.8 if stroke else 0)
        pdf.rect(x*72, (H-y-h)*72, w*72, h*72, fill=1, stroke=int(bool(stroke)))
        return shape

    def line(self, x1, y1, x2, y2, color=GRID, thickness=1.2):
        shape = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        shape.line.color.rgb = RGBColor.from_string(color)
        shape.line.width = Pt(thickness)
        pdf.setStrokeColor(HexColor('#'+color))
        pdf.setLineWidth(thickness)
        pdf.line(x1*72, (H-y1)*72, x2*72, (H-y2)*72)

    def text(self, content, x, y, w, size=20, color=INK, bold=False, align='left', h=None):
        face = 'bold' if bold else 'regular'
        lines = []
        for paragraph in content.split('\n'):
            current = ''
            for word in paragraph.split():
                candidate = (current+' '+word).strip()
                if current and pdfmetrics.stringWidth(candidate, face, size) > w*72-3:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        height = h or ((len(lines)*size*1.22+5)/72)
        assert x >= 0 and y >= 0 and x+w <= W+.002 and y+height <= H+.002, (content,x,y,w,height)
        assert len(lines)*size*1.22 <= height*72, (content, 'text overflow')
        shape = self.slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(height))
        tf = shape.text_frame
        tf.clear()
        tf.word_wrap = False
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.font.name = FONT
            p.font.size = Pt(size)
            p.font.bold = bold
            p.font.color.rgb = RGBColor.from_string(color)
            p.space_before = p.space_after = Pt(0)
            p.line_spacing = Pt(size*1.22)
            p.alignment = {'left': PP_ALIGN.LEFT, 'center': PP_ALIGN.CENTER, 'right': PP_ALIGN.RIGHT}[align]
            pdf.setFont(face, size)
            pdf.setFillColor(HexColor('#'+color))
            baseline = (H-y)*72-size*.94-i*size*1.22
            if align == 'center':
                pdf.drawCentredString((x+w/2)*72, baseline, line)
            elif align == 'right':
                pdf.drawRightString((x+w)*72, baseline, line)
            else:
                pdf.drawString(x*72, baseline, line)
        self.records.append(dict(text=content, x=x, y=y, w=w, h=height, size=size, lines=len(lines)))
        return shape

    def finish(self, source_label):
        self.line(.72, 6.91, 12.61, 6.91, GRID, .6)
        self.text(source_label, .72, 7.02, 10.8, 9, color=MUTED)
        marker = str(self.index) if not self.backup else f'Appendix {self.index-MAIN_SLIDES}'
        self.text(marker, 11.55, 7.02, 1.06, 10, color=MUTED, align='right')
        start = sum(n['seconds'] for n in notes)
        entry = dict(slide=self.index, title=self.title, seconds=self.seconds,
                     start=start, script=self.script, sources=self.sources, backup=self.backup)
        notes.append(entry)
        time_label = 'Q&A backup — outside the five-minute recording' if self.backup else f'{start//60}:{start%60:02d}–{(start+self.seconds)//60}:{(start+self.seconds)%60:02d} ({self.seconds} seconds)'
        self.slide.notes_slide.notes_text_frame.text = (
            time_label+'\n\nNARRATION\n'+self.script+'\n\nSOURCES\n'+'\n'.join(self.sources))
        audit.append(dict(slide=self.index, title=self.title, text_boxes=self.records))
        pdf.showPage()


def table(s, headers, data, x, y, widths, row_height=.59, size=21):
    """Plain academic table with horizontal rules and no cell decoration."""
    total = sum(widths)
    s.line(x, y, x+total, y, MUTED, 1)
    xx = x
    for label, w in zip(headers, widths):
        s.text(label, xx+.12, y+.15, w-.24, size-3, bold=True)
        xx += w
    header_h=max(h.count('\n')+1 for h in headers)*(size-3)*1.22/72+.28
    s.line(x, y+header_h, x+total, y+header_h, MUTED, .7)
    for i,row in enumerate(data):
        yy=y+header_h+i*row_height
        xx=x
        for label,w in zip(row,widths):
            s.text(str(label),xx+.12,yy+.14,w-.24,size)
            xx+=w
        if i<len(data)-1:
            s.line(x,yy+row_height,x+total,yy+row_height,GRID,.4)
    s.line(x,y+header_h+len(data)*row_height,x+total,y+header_h+len(data)*row_height,MUTED,.8)


def arrow(s,x1,y1,x2,y2,color=MUTED,both=False):
    s.line(x1,y1,x2,y2,color,1.2)
    # Connections used here are horizontal or vertical.
    if abs(y1-y2)<.001:
        direction=1 if x2>x1 else -1
        s.line(x2-direction*.09,y2-.055,x2,y2,color,1.2)
        s.line(x2-direction*.09,y2+.055,x2,y2,color,1.2)
        if both:
            s.line(x1+direction*.09,y1-.055,x1,y1,color,1.2)
            s.line(x1+direction*.09,y1+.055,x1,y1,color,1.2)
    else:
        direction=1 if y2>y1 else -1
        s.line(x2-.055,y2-direction*.09,x2,y2,color,1.2)
        s.line(x2+.055,y2-direction*.09,x2,y2,color,1.2)


# 1. Open with the completed system and the design question.
s=Slide(1,'A complete framework for coherent GEMM tradeoffs',True)
s.text('Coherent GEMM Accelerator',.85,1.30,11.60,40,color=BLUE)
s.text('A complete framework for studying\nperformance–resource tradeoffs',.85,2.32,11.60,30)
s.line(.85,3.64,12.25,3.64,GRID,.8)
s.text('Yasir Mahmud · Rasin Mohammed Ihtemam · Mohyeu Hussain',.85,4.04,11.60,21)
s.text('Implemented kernels, host integration, simulator extensions,\nautomated experiments, validation, and analysis.',.85,5.01,11.60,24)
s.finish('Completed study · simulation engine: gem5-Aladdin')

# 2. State both sides of the tradeoff before introducing the study.
s=Slide(2,'The tradeoff: useful parallelism versus resource cost')
s.text('Width w is the number of output columns computed together.',.88,1.60,11.54,22)
s.text('Narrow: w = 1',.98,2.23,4.20,22,bold=True)
s.text('Wider: w = 4',6.12,2.23,6.20,22,bold=True)
s.rect(1.02,3.03,1.40,.59,BG,MID)
s.text('one A',1.12,3.15,1.20,20,align='center')
arrow(s,2.45,3.33,3.15,3.33)
s.rect(3.18,3.03,1.40,.59,BG,BLUE)
s.text('one sum',3.25,3.15,1.26,19,align='center')
s.rect(6.12,3.03,1.32,.59,BG,MID)
s.text('one A',6.18,3.15,1.20,20,align='center')
s.line(7.47,3.33,7.71,3.33,MUTED)
s.line(7.71,3.33,7.71,4.05,MUTED)
s.line(7.71,4.05,12.04,4.05,MUTED)
for j in range(4):
    x=8.10+j*1.10
    s.rect(x,3.03,.94,.59,BG,BLUE)
    s.text(f'sum {j+1}',x+.04,3.18,.86,16,align='center')
    arrow(s,x+.47,4.05,x+.47,3.64)
s.text('Potential benefit',.98,4.60,5.35,20,color=BLUE,bold=True)
s.text('Fewer repeated input operations\nMore independent arithmetic',.98,5.08,5.35,23)
s.text('Cost and system constraints',6.62,4.60,5.70,20,color=BLUE,bold=True)
s.text('More live sums and resource demand\nSpeedup depends on the full system',6.62,5.08,5.70,23)
s.text('We measure latency, modeled area, and whole-program time together.',.98,6.34,11.45,22)
s.finish('Width changes the dataflow; it does not guarantee faster execution in every invocation or workload')

# 2. Define the core symbols graphically before using them in the analysis.
s=Slide(3,'Notation: matrix size, tile width, and issue limit')
s.text('A and B are the inputs; C = A × B is the output. Each matrix has N rows and N columns.',
       .86,1.56,11.62,20)
cell,top=.24,2.70
matrix_x={'A':1.55,'B':5.45,'C':9.65}
for name,x in matrix_x.items():
    s.text(f'{name}: '+('output' if name=='C' else 'input'),x-.22,2.31,2.36,21,
           color=BLUE,align='center')
    for row in range(8):
        for column in range(8):
            fill=BG
            if name=='A' and row==3:
                fill='E6EEF5'
            if name=='B' and 2<=column<6:
                fill='E6EEF5'
            if name=='B' and row==3 and 2<=column<6:
                fill=PALE
            if name=='A' and row==3 and column==3:
                fill=BLUE
            if name=='C' and row==3 and 2<=column<6:
                fill=BLUE
            s.rect(x+column*cell,top+row*cell,cell,cell,fill,GRID)
s.text('×',4.02,3.39,.60,30,align='center')
s.text('=',8.22,3.39,.60,30,align='center')
# Dimension brackets label the full matrix extent, not the highlighted tile.
s.line(1.32,top,1.32,top+8*cell,MID,.8)
s.line(1.24,top,1.40,top,MID,.8)
s.line(1.24,top+8*cell,1.40,top+8*cell,MID,.8)
s.text('N=8\nrows',.75,3.30,.48,14,color=MUTED,align='center')
s.line(1.55,4.77,3.47,4.77,MID,.8)
for xx in [1.55,3.47]:
    s.line(xx,4.69,xx,4.85,MID,.8)
s.text('N = 8 columns',1.43,4.97,2.16,17,color=MUTED,align='center')
s.text('8 × 8',5.45,4.97,1.92,17,color=MUTED,align='center')
tile_left=matrix_x['C']+2*cell
tile_right=matrix_x['C']+6*cell
# Guides link the four computed output cells to the tile-width bracket.
for xx in [tile_left,tile_right]:
    s.line(xx,top+4*cell,xx,4.77,PALE,.6)
    s.line(xx,4.69,xx,4.85,BLUE,.8)
s.line(tile_left,4.77,tile_right,4.77,BLUE,.8)
s.text('w = 4 output columns together',8.74,4.97,3.82,17,color=BLUE,align='center')
# A separate time-step diagram distinguishes the issue limit from matrix B.
s.text('Lowercase b limits requests per cycle; uppercase B is a matrix.',.86,5.57,11.62,20)
s.rect(.98,6.13,2.66,.53,BG,MID)
s.text('Request queue',1.08,6.25,2.46,18,align='center')
for yy in [6.25,6.51]:
    arrow(s,3.73,yy,5.15,yy,BLUE)
s.rect(5.27,6.13,2.19,.53,BG,MID)
s.text('Cache',5.37,6.25,1.99,18,align='center')
s.text('b = 2: at most two requests\nissued in one accelerator cycle',8.00,6.13,4.46,17)
s.finish('Illustrative N=8 grid; the issue-limit setting b is independent of tile width w')

# 4. Attribute the simulation engine and show our full implementation stack.
s=Slide(4,'We built the complete experimental framework')
s.text('Project-specific implementation, from accelerator kernels to validated design comparisons.',.88,1.60,11.54,21)
for x,w,title,detail in [(.92,2.90,'CPU + host harness','Invoke · time · verify'),
                        (5.04,3.05,'Ruby coherence','Shared L2 + DRAM'),
                        (9.42,3.00,'GEMM accelerator','Datapath + coherent cache')]:
    s.rect(x,2.27,w,1.10,BG,MID)
    s.text(title,x+.10,2.48,w-.20,21,color=BLUE,align='center')
    s.text(detail,x+.10,2.95,w-.20,16,color=MUTED,align='center')
arrow(s,3.86,2.82,4.97,2.82,both=True)
arrow(s,8.15,2.82,9.35,2.82,both=True)
s.text('32 kB coherent cache · bounded 32-entry request queue · resource-constrained scheduling',.92,3.66,11.50,18,color=MUTED)
layers=[('Kernels','Baseline + two wider\nGEMM implementations'),
        ('Host harnesses','CPU reference checks\nSegmented timing\nRepeated invocations'),
        ('Simulator','Queue / retry integration\nPassive graph + request\ninstrumentation'),
        ('Experiment tools','Isolated run automation\nConfiguration validation\nGenerated plots + tables')]
for j,(title,body) in enumerate(layers):
    x=.94+j*2.97
    s.text(title,x,4.43,2.72,19,bold=True,color=BLUE)
    s.text(body,x,4.99,2.72,18)
    if j<3: s.line(x+2.80,4.38,x+2.80,6.47,GRID,.6)
s.finish('Built on gem5-Aladdin; project contributions include kernels, harnesses, simulator extensions, and analysis')

# 5. Completed execution coverage, not a list of future tasks.
s=Slide(5,'A completed study across five experiment families')
s.text('Each experiment family answers a different part of the design question.',.88,1.60,11.54,21)
table(s,['Experiment family','What we established','Runs'],[
    ['Dataflow + workload','Three widths across four matrix sizes','60'],
    ['Memory interface','How request capacity changes the width benefit','20'],
    ['Mechanism observer','Graph operations versus actual cache requests','12'],
    ['Repeated invocations','How execution history changes performance','12'],
    ['Input boundary checks','Which input changes the trace model supports','3'],
],.88,2.27,[3.15,7.24,1.15],row_height=.59,size=20)
s.text('107 simulator executions, with retained inputs, programs, traces, checks, and results.',.98,6.34,11.43,21,color=BLUE)
s.finish('Complete fresh experiment suite; observer/reference pairs and correctness outcomes validated')

# 6. Plot the measured design points directly in latency–area space.
s=Slide(6,'The latency–area tradeoff changes with workload size')
s.text('Offload latency (µs)',.92,1.53,6.9,20)
left,right,top,bottom=1.68,7.91,2.48,5.74
xmin,xmax,ymin,ymax=1.15,1.70,2.10,4.50
def area_x(v): return left+(v-xmin)/(xmax-xmin)*(right-left)
def latency_y(v): return bottom-(v-ymin)/(ymax-ymin)*(bottom-top)
for tick in [2.5,3.0,3.5,4.0,4.5]:
    yy=latency_y(tick)
    s.line(left,yy,right,yy,GRID,.45)
    s.text(f'{tick:.1f}',.97,yy-.12,.50,15,color=MUTED,align='right')
for tick in [1.2,1.4,1.6]:
    xx=area_x(tick)
    s.line(xx,top,xx,bottom,GRID,.45)
    s.text(f'{tick:.1f}',xx-.25,5.90,.50,16,color=MUTED,align='center')
s.line(left,bottom,right,bottom,MID,.8)
for j,(n,color) in enumerate([(24,BLUE),(32,'687682')]):
    lx=2.12+j*2.38
    s.line(lx,2.14,lx+.34,2.14,color,1.5)
    s.text(f'N = {n}',lx+.47,2.03,1.42,16,color=MUTED)
    points=[]
    for w in [1,2,4]:
        xx=area_x(num(n,w,'total_area_um2')/1e6)
        yy=latency_y(num(n,w,'offload_ns')/1000)
        points.append((xx,yy))
        s.rect(xx-.045,yy-.045,.09,.09,color)
        dx,dy=(.12,-.13)
        if n==32 and w==1: dx,dy=(-.58,-.37)
        if n==24 and w==1: dx,dy=(.12,-.30)
        if n==24 and w==2: dx,dy=(.12,-.04)
        if n==24 and w==4: dx,dy=(-.61,.03)
        s.text(f'w={w}',xx+dx,yy+dy,.63,16,color=color)
    for p1,p2 in zip(points,points[1:]): s.line(*p1,*p2,color,1.25)
s.text('Modeled total area (mm²)',1.75,6.30,6.10,19,align='center')
s.line(8.39,1.91,8.39,6.44,GRID,.7)
s.text('N = 24: w=4 vs. w=1',8.73,1.97,3.80,20,bold=True)
s.text('11.8% shorter offload\n0.33% less modeled area',8.73,2.56,3.80,22,color=BLUE)
s.text('N = 32: w=4 vs. w=1',8.73,3.90,3.80,20,bold=True)
s.text('25.1% shorter offload\n27.7% more modeled area',8.73,4.49,3.80,22,color=BLUE)
s.text('Compact w=1 or faster w=4:\nthe choice depends on cost.',8.73,5.85,3.80,18)
s.finish('Lower and farther left is preferable · modeled area is pre-RTL · widths compared within each N')

# 7. Use a real, validated reversal; do not invent a generic width slowdown.
s=Slide(7,'A wider design can also take longer to execute')
s.text('N = 24 · unchanged inputs · timed repeated-call experiment · offload time (µs)',.88,1.60,11.54,20)
table(s,['Invocation','w = 1','w = 2','w = 4'],[
    ['First',f'{repeated_us(1,0):.3f}',f'{repeated_us(2,0):.3f}',f'{repeated_us(4,0):.3f}'],
    ['Second',f'{repeated_us(1,1):.3f}',f'{repeated_us(2,1):.3f}',f'{repeated_us(4,1):.3f}'],
],.98,2.40,[3.30,2.70,2.70,2.70],row_height=.76,size=25)
first_gain=100*(1-repeated_us(4,0)/repeated_us(1,0))
s.text(f'First invocation: width 4 takes {first_gain:.1f}% less time than width 1.',1.10,4.94,11.20,25,color=BLUE)
s.text(f'Second invocation: width 4 takes {slowdown:.1f}% more time than width 1.',1.10,5.61,11.20,25)
s.text('The same workload can favor different designs as invocation history changes.',1.10,6.37,11.20,20)
s.finish('Matched timed harness; these are observed diagnostic outcomes, not a general warm-cache scaling law')

# 8. Show where local gains are reduced on the way to the application.
s=Slide(8,'The memory interface and host set the useful gain')
s.text('Request interface · N = 24',.94,1.65,5.86,21,bold=True)
s.text('Width-4 offload benefit (%)',.94,2.20,5.86,18,color=MUTED)
ll,rr,tt,bb=1.65,6.21,2.91,5.49
for tick in [0,6,12]:
    yy=bb-tick/14*(bb-tt)
    s.line(ll,yy,rr,yy,GRID,.5)
    s.text(str(tick),.99,yy-.12,.40,15,color=MUTED,align='right')
points=[]
for b in [1,2,4]:
    xx=1.99+(b-1)*1.30
    yy=bb-benefit(b)/14*(bb-tt)
    points.append((xx,yy))
    s.rect(xx-.045,yy-.045,.09,.09,BLUE)
    s.text(f'{benefit(b):.1f}%',xx-.38,yy-.43,.76,19,color=BLUE,align='center')
    s.text(str(b),xx-.20,5.66,.40,17,align='center')
for p1,p2 in zip(points,points[1:]): s.line(*p1,*p2,BLUE,1.4)
s.text('Issue limit b (requests/cycle)',1.09,6.07,5.53,18,align='center')
s.line(6.96,1.74,6.96,6.30,GRID,.7)
s.text('Application impact · N = 32',7.43,1.65,5.04,21,bold=True)
s.text('Reduction from w=1 to w=4',7.43,2.20,5.04,18,color=MUTED)
for label,key,yy in [('Datapath','datapath_ns',3.20),('Offload','offload_ns',4.23),('Program','whole_program_ticks',5.26)]:
    value=reduction(32,key)
    s.text(label,7.43,yy,1.66,19)
    s.rect(9.31,yy+.05,value/30*1.93,.26,BLUE)
    fmt=f'{value:.2f}%' if value<1 else f'{value:.1f}%'
    s.text(fmt,11.49,yy-.01,.97,19,align='right')
s.text('Measure the benefit delivered by the full system.',.98,6.48,11.43,21,color=BLUE)
s.finish('Issue-limit sweep uses N=24 matched baselines; application reductions use the N=32 main sweep')

# 9. Report established conclusions, with no progress or submission logistics.
s=Slide(9,'What our completed study established')
items=[('Framework','Implemented and validated the full path from GEMM kernels\nto coherent-system timing, cost, and analysis.'),
       ('Tradeoff','At N=32: 25.1% shorter offload with 27.7% more modeled area.\nAt N=24: the wider design is faster and slightly smaller.'),
       ('Design choice','Width 4 is 2.3% slower on the second call in our diagnostic.\nWidth, workload, memory interface, and history must be evaluated together.')]
for i,(label,body) in enumerate(items):
    yy=1.92+i*1.43
    s.text(label,.98,yy,2.20,22,bold=True,color=BLUE)
    s.text(body,3.36,yy,9.00,22)
s.text('Choose the dataflow using latency, cost, and application benefit together.',.98,6.30,11.43,23,color=BLUE)
s.finish('Completed coherent-GEMM framework and study · powered by gem5-Aladdin')

# 5. Evidence table instead of a dashboard panel.
s=Slide(10,'Fewer graph loads do not imply fewer cache requests')
s.text('Passive graph and request observer · N = 24 · b = 4',.88,1.62,11.55,20,color=MUTED)
table(s,['Tile width','Source / optimized\nA loads','Accepted\nA requests'],[
    [f'w = {w}',f'{int(graph[w]["after_connected_Load_A"]):,}',int(graph[w]['accepted_A_load'])]
    for w in [1,2,4]
],1.10,2.20,[2.80,4.80,3.40],row_height=.66,size=24)
s.text('B requests and C stores also remain unchanged: 36 loads and 576 stores.',1.10,5.50,11.0,21)
s.text('The queue merges loads to the same cache line.',1.10,6.05,11.0,23,color=BLUE)
s.finish('Observer and reference simulated statistics match · accepted requests equal returned requests per array')

# 11. Keep metric definitions available for technical questions.
s=Slide(11,'Appendix: measurement definitions')
items=[('Offload time','Reset before invocation → completion → host return.'),
       ('Datapath time','Modeled datapath cycles × 1 ns.'),
       ('Program time','Whole-program execution, including setup and host work.'),
       ('Modeled area','Functional-unit + memory estimates before RTL.'),
       ('Issue limit b','Allowed requests per accelerator cycle; cache capacity is fixed.')]
for i,(label,body) in enumerate(items):
    yy=1.91+i*.87
    s.text(label,.90,yy,2.37,20,bold=True)
    s.text(body,3.40,yy,8.96,21)
    if i<4: s.line(.90,yy+.65,12.36,yy+.65,GRID,.45)
s.text('The 107 executions cover different experiments; they are not statistical repetitions.',.90,6.45,11.40,18,color=MUTED)
s.finish('Source selection: paper/experiment_data.json · complete data paths in speaker notes')

# 12. Retain trace-model boundaries without confusing them with unfinished work.
s=Slide(12,'Appendix: repeated-call correctness and scope')
table(s,['Input case','Validated outcome'],[
    ['Matched to trace','Every per-call checker output passes at widths 1, 2, and 4.'],
    ['Independent mutations','20 / 24 / 19 mismatches across calls at every width.'],
],.88,1.94,[3.54,8.00],row_height=.90,size=21)
s.text('The main-slide reversal uses unchanged inputs in the timed harness.',.98,4.88,11.30,22,color=BLUE)
s.text('• Timed repeated runs check the final output.\n• Intermediate timed outputs are not individually checked.\n• Checker timing has a different cache history from the timed harness.',.98,5.52,11.30,20)
s.finish('Input-boundary tests completed; unsupported mutations are excluded from performance comparisons')

assert sum(n['seconds'] for n in notes)==300
assert len(notes)==len(CONTENT) and sum(not n['backup'] for n in notes)==MAIN_SLIDES
deck.save(str(OUT/'project_presentation.pptx'))
pdf.save()

md=['# Five-minute presentation speaker notes','',
    f'Present slides 1–{MAIN_SLIDES} in **5:00**. Slides {MAIN_SLIDES+1}–{len(notes)} are Q&A backups, excluded from the recording.','',
    'Narration is also embedded in the PowerPoint. Rehearse to the target times.','',
    '| Slide | Time | Topic |','| --- | --- | --- |']
for n in notes:
    if not n['backup']:
        a,b=n['start'],n['start']+n['seconds']
        md.append(f'| {n["slide"]} | {a//60}:{a%60:02d}–{b//60}:{b%60:02d} | {n["title"]} |')
for n in notes:
    md+=['',f'## {n["slide"]}. {n["title"]}'+(' (Q&A backup)' if n['backup'] else ''),'',n['script'],'','Sources:','']
    md+=[f'- [{p}](../{p.replace(" ","%20")})' for p in n['sources']]
(OUT/'speaker_notes.md').write_text('\n'.join(md))
(OUT/'layout_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
words=sum(len(re.findall(r"\b[\w’'-]+\b",n['script'])) for n in notes if not n['backup'])
print(f'Created white-background academic deck: {MAIN_SLIDES} main slides + {len(notes)-MAIN_SLIDES} backups; 300 seconds; {words} narration words.')
