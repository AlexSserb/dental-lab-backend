from accounts.models import DentalLabData
from orders.reports.report import Report
from orders.models import Order


class AcceptanceReport(Report):
    def __init__(self, order: Order, dental_lab_data: DentalLabData):
        super().__init__(order, dental_lab_data)
        self.print_customer_and_dental_lab_data()
        self.print_works()

    def header(self):
        self.set_title_font()
        self.cell(txt="InColor", ln=True, border="B")
        self.ln()
        self.set_bold_font()
        self.cell(txt="Акт сдачи-приема")
        self.divider()

    def print_works(self):
        self.set_default_font()
        self.ln(h=10)
        self.cell(txt="Перечень выполненных работ")
        self.ln(h=10)
        self.cell(w=70, txt="Работа")
        self.cell(w=25, txt="Кол-во")
        self.cell(w=30, txt="Цена (руб)")
        self.cell(w=28, txt="Скидка (%)")
        self.cell(w=35, txt="Стоимость (руб)")
        self.divider()
        sum_cost = 0
        for work in self.order.works.all():
            self.ln(h=5)
            self.cell(w=70, txt=str(work.work_type.name))
            self.cell(w=25, txt=str(work.amount))
            self.cell(w=30, txt=str(work.work_type.cost))
            self.cell(w=28, txt=str(work.get_discount()))
            cost = work.get_cost()
            sum_cost += cost
            self.cell(w=40, txt=str(cost))
            self.divider()

        self.ln(h=5)
        self.cell(txt=f"Итого: {sum_cost} руб.")
        self.ln(h=10)

    def print_customer_and_dental_lab_data(self):
        self.set_default_font()
        self.ln(h=10)
        self.cell(txt=f"Настоящий акт составлен в том, что зуботехническая лаборатория {self.lab.name}")
        self.ln(h=10)
        self.cell(txt=f"выполнила работы для Заказчика {self.order.customer.name}")
        self.ln(h=10)
        self.cell(txt=f"по наряду № {self.doc_id} от {self.order.order_date.strftime('%d.%m.%Y')}")
        self.ln(h=10)

    def footer(self):
        self.set_default_font()
        self.ln()
        signature_w, label_w = 40, 38
        self.cell(txt="Вышеперечисленные работы выполнены полностью и в срок.")
        self.ln(h=8)
        self.cell(txt="Заказчик претензий по объему, сроку и качеству оказания работ не имеет.")
        self.ln(h=8)
        self.cell(w=18, txt="Дата")
        self.cell(w=signature_w, txt="         ", border="B")
        self.ln(h=10)
        self.cell(w=93, txt="Работу принял:")
        self.cell(w=92, txt="Работу сдал:")
        self.ln(h=8)
        self.cell(w=label_w, txt="Заказчик")
        self.cell(w=signature_w, txt="         ", border="B")
        self.cell(w=15)
        self.cell(w=label_w, txt="Исполнитель")
        self.cell(w=signature_w, txt="         ", border="B")
