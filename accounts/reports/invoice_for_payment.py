from black import datetime

from accounts.models import DentalLabData
from accounts.reports.report import Report
from api.models import Order


class InvoiceForPayment(Report):
    def __init__(self, order: Order, dental_lab_data: DentalLabData):
        super().__init__(order, dental_lab_data)
        self.print_customer_data()
        self.print_dental_lab_data()
        self.print_products()
        self.print_conditions()

    def header(self):
        self.set_title_font()
        self.cell(txt="InColor", ln=True, border="B")
        self.ln()
        self.set_bold_font()
        self.cell(txt=f"Счет на оплату от {datetime.today().strftime('%d.%m.%Y')}")
        self.ln(h=8)
        self.set_default_font()
        self.cell(
            txt=f"Основанием является наряд № {self.doc_id} от {self.order.order_date.strftime('%d.%m.%Y')}"
        )
        self.divider()

    def print_products(self):
        self.set_default_font()
        self.ln(h=10)
        self.cell(txt="Перечень изделий")
        self.ln(h=10)
        self.cell(w=70, txt="Изделие")
        self.cell(w=25, txt="Кол-во")
        self.cell(w=30, txt="Цена (руб)")
        self.cell(w=28, txt="Скидка (%)")
        self.cell(w=35, txt="Стоимость (руб)")
        self.divider()
        sum_cost = 0
        for product in self.order.products.all():
            self.ln(h=5)
            self.cell(w=70, txt=str(product.product_type.name))
            self.cell(w=25, txt=str(product.amount))
            self.cell(w=30, txt=str(product.product_type.cost))
            self.cell(w=28, txt=str(product.get_discount()))
            cost = product.get_cost()
            sum_cost += cost
            self.cell(w=40, txt=str(cost))
            self.divider()

        self.ln(h=5)
        self.cell(txt=f"Итого: {sum_cost} руб.")
        self.ln(h=10)

    def print_customer_data(self):
        self.set_default_font()
        self.ln()
        self.cell(txt=f"Заказчик: {self.order.customer.name}")
        self.cell(w=20)
        self.cell(txt=f"Врач: {self.order.user.last_name} {self.order.user.first_name}")
        self.ln(h=10)
        self.cell(
            txt=f"Адрес заказчика: г. {self.order.customer.adrs_city} ул. {self.order.customer.adrs_street} д. {self.order.customer.adrs_house}"
        )
        self.ln(h=10)
        self.cell(txt=f"ИНН: {self.order.customer.tax_payer_id}")
        self.cell(w=20)
        self.cell(txt=f"КПП: {self.order.customer.reason_code_for_reg}")
        self.cell(w=20)
        self.cell(txt=f"Р/с: {self.order.customer.checking_account}")
        self.divider()

    def print_dental_lab_data(self):
        self.set_default_font()
        self.ln()
        self.txt_line(f"Исполнитель: {self.lab.name}", 10)
        self.txt_line(f"Банк исполнителя: {self.lab.bank_name}", 10)
        self.cell(txt=f"БИК: {self.lab.bank_id_code}")
        self.cell(w=20)
        self.cell(txt=f"ИНН: {self.lab.tax_payer_id}")
        self.cell(w=20)
        self.txt_line(f"КПП: {self.lab.reason_code_for_reg}", 10)
        self.cell(txt=f"Р/с: {self.lab.current_account}")
        self.cell(w=20)
        self.cell(txt=f"Кор/с: {self.lab.correspondent_account}")
        self.divider()

    def print_conditions(self):
        self.set_small_font()
        h = 6
        self.ln()
        self.txt_line("Оплата данного счета означает согласие Заказчика с условиями оказания услуг:", h)
        self.txt_line(
            "1. Исполнитель обязуется оказать Заказчику услуги, а Заказчик обязуется их принять и оплатить.", h
        )
        self.txt_line("2. Сведения об оказанных услугах содержатся в настоящем счете.", h)
        self.txt_line(
            "3. Оплата услуг осуществляется Заказчиком путем безналичного перевода денежных средств на расчетный счет",
            h,
        )
        self.txt_line("    Исполнителя с обязательным указанием в платежном поручении реквизитов настоящего счета.", h)
        self.txt_line("4. Заказчик обязуется оплатить услуги в размере 100% в течение 5 рабочих дней.", h)
        self.txt_line(
            "5. Исполнитель обязуется оказать услуги в течение 10 рабочих дней со дня поступления оплаты на расчетный счет.",
            h,
        )
        self.txt_line(
            "6. Приемка оказанных услуг осуществляется путем подписания Заказчиком и Исполнителем акта о сдаче-приемке.",
            h,
        )

    def footer(self):
        self.set_default_font()
        self.ln()
        signature_w, label_w = 40, 45
        self.cell(w=label_w, txt="Заказчик")
        self.cell(w=signature_w, txt="         ", border="B")
        self.cell(w=15)
        self.cell(w=label_w, txt="Бухгалтер")
        self.cell(w=signature_w, txt="         ", border="B")
        self.ln(h=10)
        self.cell(w=label_w, txt="Зав. лаборатории")
        self.cell(w=signature_w, txt="         ", border="B")
