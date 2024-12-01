import os

from django.conf import settings
from fpdf import FPDF

from accounts.models import DentalLabData
from orders.models import Order


class Report(FPDF):
    DEFAULT_FONT = "DejaVu"
    BOLD_FONT = "DejaVuBold"
    SMALL_FONT_SIZE = 9
    DEFAULT_FONT_SIZE = 12
    TITLE_FONT_SIZE = 22
    FONT_PATH = os.path.join(settings.BASE_DIR, "documents", "fonts", "DejaVuSansCondensed.ttf")
    BOLD_FONT_PATH = os.path.join(settings.BASE_DIR, "documents", "fonts", "DejaVuSansCondensed-Bold.ttf")
    DOC_WIDTH = 190

    def __init__(self, order: Order, dental_lab_data: DentalLabData):
        super().__init__()
        self.add_font(self.DEFAULT_FONT, "", self.FONT_PATH)
        self.add_font(self.BOLD_FONT, "", self.BOLD_FONT_PATH)
        self.order = order
        self.lab = dental_lab_data
        self.doc_id = str(self.order.id).split("-")[0]
        self.add_page()

    def txt_line(self, txt: str, h: int):
        self.cell(txt=txt)
        self.ln(h=h)

    def set_black_color(self):
        self.set_text_color(0, 0, 0)
        self.set_fill_color(0, 0, 0)

    def set_small_font(self):
        self.set_black_color()
        self.set_font(self.DEFAULT_FONT, size=self.SMALL_FONT_SIZE)

    def set_default_font(self):
        self.set_black_color()
        self.set_font(self.DEFAULT_FONT, size=self.DEFAULT_FONT_SIZE)

    def set_bold_font(self):
        self.set_black_color()
        self.set_font(self.BOLD_FONT, size=16)

    def set_title_font(self):
        self.set_text_color(0, 128, 255)
        self.set_fill_color(0, 128, 255)
        self.set_font(self.BOLD_FONT, size=self.TITLE_FONT_SIZE)

    def divider(self):
        self.ln(h=8)
        self.cell(w=self.DOC_WIDTH, border="B")
