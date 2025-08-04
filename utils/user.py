class User:
    def __init__(self, id : int, name : str):
        self.id = id
        self.name = name
    
    def getId(self):
        return self.id

    def getName(self):
        return self.name
    
    def getDict(self):
        return {
            str(self.id) : {
                "chatId" : self.id,
                "name" : self.name
            }
        }