class Item:
    def __init__(self, name :str, price : int, quantity : int, dictData : dict):
        if dictData:
            self.name = name
            self.price = dictData.get("price")
            self.quantity = dictData.get("quantity")
        else:
            self.name = name
            self.price = price
            self.quantity = quantity
    
    def getName(self):
        return self.name
    
    def getPrice(self):
        return self.price
    
    def setPrice(self, price):
        self.price = price

    def getQuantity(self):
        return self.quantity
    
    def setQuantity(self, quantity):
        self.quantity = quantity
    
    def getDict(self):
        return {
            self.name : {
                "price" : self.price,
                "quantity" : self.quantity
            }
        }
    

    