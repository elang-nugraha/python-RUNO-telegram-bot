from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def __init__(self, orientation, unit, format, width, height, title, data):
        super().__init__(orientation, unit, format)
        self.width = width
        self.height = height
        self.title = title
        self.data = data

    def header(self):
        # font
        image = 'utilsData/gambar.png'
        imageWidth = self.width - 50
        self.image(image, (self.width / 2) - (imageWidth / 2), 3, imageWidth)

        height = 35
        width = 10
        self.set_y(height)
        self.set_draw_color(0, 0, 0)  # optional: set line color (black)
        self.line(width, height, self.width - width, height)
        self.set_font('helvetica', '', 10)

        transactionDate = datetime.now().strftime("%d - %m - %Y")
        self.cell(self.width, 5, f"Transaction Date : {transactionDate}", ln=1)
        self.cell(self.width, 5, f"Order Date : {self.data["date"]["day"]} - {self.data["date"]["month"]} - {self.data["date"]["year"]}", ln=1)


    def body(self):
        height = 45
        width = 10
        self.set_draw_color(0, 0, 0)  # optional: set line color (black)
        self.line(width, height, self.width - width, height)

        self.set_y(height)
        order = self.data["order"]
        for i in order:
            self.set_x(width + 1)
            self.set_font('helvetica', 'B', 10)
            self.cell(self.width, 10, "Siomay " + f"{i}".capitalize(), ln=1)


            self.set_x(width + 5)
            self.set_font('helvetica', '', 10)
            self.cell(10, 0,  str(order[i]["quantity"]))
            self.cell(15, 0, f"X {order[i]["price"] / order[i]["quantity"]}")
            self.cell(self.width - 72, 0, f"...", align="C")
            self.cell(self.width - 80, 0, f"{order[i]["price"]}", align="R" ,ln=1)
            self.cell(self.width, 3, ln=1)
    
    def footer(self):
        self.set_y(-10)
        self.set_x(0)
        height = self.height - 20
        width = 10

        self.set_draw_color(0, 0, 0) 
        self.line(width, height, self.width - width, height)

        self.set_x(width + 2)
        self.set_font('helvetica', 'B', 13)
        self.cell(self.width / 2, -10, f"Total : ", align="L")
        self.cell(self.width - 74, -10, f"{self.data["Total Price"]}", align="R" ,ln=1)

data = {
    "date": {"day": "12", "month": "12", "year": "1234"}, 
    "customer": "asd", 
    "order": {"ori": {"quantity": 100, "price": 400000}}, 
    "Total Price": 400000}

def generateRecipt(data):
    title = 'SIOMAY RUNO'
    width = 100
    height = 150 if len(data["order"].keys()) > 3 else 100

    pdf = PDF("P", "mm", (width, height), width, height, title, data)

    pdf.add_page()
    pdf.body()

    pdf.output('data/recipt.pdf')