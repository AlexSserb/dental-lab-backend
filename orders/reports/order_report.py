from accounts.models import DentalLabData
from orders.reports.report import Report
from orders.models import Order


class OrderReport(Report):
    def __init__(self, order: Order, dental_lab_data: DentalLabData):
        super().__init__(order, dental_lab_data)
        self.print_customer_data()
        self.print_dental_lab_data()
        self.print_products()

    def header(self):
        self.set_title_font()
        self.cell(txt="InColor", ln=True, border="B")
        self.ln()
        self.set_bold_font()
        self.cell(txt=f"Наряд № {self.doc_id} от {self.order.order_date.strftime('%d.%m.%Y')}")
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
        self.ln(h=10)
        self.cell(txt=f"Заказчик: {self.order.customer.name}")
        self.ln(h=10)
        self.cell(
            txt=f"Адрес заказчика: г. {self.order.customer.adrs_city} ул. {self.order.customer.adrs_street} д. {self.order.customer.adrs_house}"
        )
        self.ln(h=10)
        self.cell(txt=f"Врач: {self.order.user.last_name} {self.order.user.first_name}")
        self.divider()

    def print_dental_lab_data(self):
        self.set_default_font()
        self.ln(h=10)
        self.cell(txt=f"Исполнитель: {self.lab.name}")
        self.ln(h=10)
        self.cell(txt=f"Банк исполнителя: {self.lab.bank_name}")
        self.ln(h=10)
        self.cell(txt=f"БИК: {self.lab.bank_id_code}")
        self.cell(w=20)
        self.cell(txt=f"ИНН: {self.lab.tax_payer_id}")
        self.cell(w=20)
        self.cell(txt=f"КПП: {self.lab.reason_code_for_reg}")
        self.ln(h=10)
        self.cell(txt=f"Р/с: {self.lab.current_account}")
        self.ln(h=10)
        self.cell(txt=f"Кор/с: {self.lab.correspondent_account}")
        self.divider()

    def footer(self):
        self.set_default_font()
        self.ln()
        signature_w, label_w = 40, 45
        self.cell(w=label_w, txt="Заказчик")
        self.cell(w=signature_w, txt="         ", border="B")
        self.cell(w=15)
        self.cell(w=label_w, txt="Администратор")
        self.cell(w=signature_w, txt="         ", border="B")
        self.ln(h=10)
        self.cell(w=label_w, txt="Зав. лаборатории")
        self.cell(w=signature_w, txt="         ", border="B")
