import json
import operator
import os
from dotenv import load_dotenv
from pymongo import MongoClient

#Telegram
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

# class
from utils.user import User
from utils.item import Item
import utils.generateRecipt as generateRecipt

# learn how to logging
import logging
logging.basicConfig(level= logging.INFO)

# load env
load_dotenv()

# Telegram Token
TOKEN = os.getenv("TELEGRAM_KEY")
# Mongo database
client = MongoClient(os.getenv("DB_CONNECTION"))
db = client[os.getenv("DB_DATABASE")]

ops = {
    '+' : operator.add,
    '-' : operator.sub
}

# Command function
async def startCommand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Heloo welcome to RUNO bot...")

# User handling
def storeUserData(users):
    with open("Data/User.json", "w") as userFile:
        json.dump(users, userFile, indent=4)

def storeUserDataMongo(user):
    userDB = db["user"]
    userDB.insert_one(user)

def getUsersData():
    try:
        with open("Data/User.json", "r") as userFile:
            users = json.load(userFile)

        return users
    except FileNotFoundError:
        return {}

def getUsersDataMongo():
    userDB = db["user"]
    userData = {}
    for i in userDB.find():
        data = {
            f"{int(i.get("chatId"))}" : i
        }
        userData.update(data)

    return(userData)

def validateUser(user: Update.effective_user):
    # get users data
    users = getUsersDataMongo()
    if users.get(str(user.id)):
        return True
    else:
        bot = Bot(TOKEN)
        bot.sendMessage(5761507238, f"{user.id} {user.full_name}, wants to user the Bot")
        return False

async def userRegistration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = getUsersDataMongo()
    newUser = User(update.effective_user.id, update.effective_user.full_name)
    registration = os.environ.get('USER_REGIS')

    # add new user
    if  registration and str(newUser.getId()) not in users:
        # # add new user
        # users.update(newUser.getDict())

        # # rewrite json file          
        # storeUserData(users)

        # store data in mongo
        storeUserDataMongo(newUser.getDictMongo())
        await update.message.reply_text(f"user {update.effective_user.full_name} registered")
    else :
        await update.message.reply_text(f"user {update.effective_user.full_name}, already registered")

async def openRegistration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(validateUser(update.effective_user)):
        os.environ['USER_REGIS'] = "True"
        await update.message.reply_text("Regitration is open")

async def closeRegistration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(validateUser(update.effective_user)):
        os.environ['USER_REGIS'] = "False"
        await update.message.reply_text("Regitration is closed")

# stock and item handling
def storeStockData(stock):
    with open("Data/Stock.json", "w") as userFile:
        json.dump(stock, userFile, indent=4)

def getStockData():
    try: 
        with open("Data/Stock.json", "r") as userFile:
            stock = json.load(userFile)

        return stock
    except FileNotFoundError:
        return {}

def getStockDataMongo():
    stockDB= db["stock"]
    stockData = stockDB.find()
    stocks = {}
    for i in stockData:
        stocks.update(i)

    return stocks
    
async def getStock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(validateUser(update.effective_user)):
        # get stock data
        stock = getStockData()

        if len(stock) > 0:
            message = "----- STOCK -----"
            for i in stock:
                message = message + f"\n{i} \t:\t{stock.get(i)["quantity"]}"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("No stock data")

# add or update item
async def addItem(update : Update, context : ContextTypes.DEFAULT_TYPE):
    if(validateUser(update.effective_user)):
        await update.message.reply_text("input item ([name] . [price] . [quantity])")
        await update.message.reply_text("type /done to end the sesion")
        return "inputItem"

async def inputItem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # process user message 
    a = update.effective_message.text
    b = a.split(" . ")

    # new item 
    item = Item(b[0], int(b[1]), int(b[2]), None)

    stock = getStockData()
    stock.update(item.getDict())

    # rewrite json file
    storeStockData(stock)

    await update.message.reply_text(f"Successfully add {b[0]}")
    await getStock(update, context)
    return ConversationHandler.END

# update item quantity
async def updateStock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(validateUser(update.effective_user)):
        await update.message.reply_text("update the stock ([name] . [+/-] . [sum])")
        await update.message.reply_text("type /done to end the sesion")

        return "inputStock"

async def inputStock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # process user message 
    message = update.effective_message.text.strip()
    await inputStockItem(update, context, message)
    return ConversationHandler.END

async def inputStockItem(update : Update, context, message : str):
    itemMessage = message.split("\n")
    stock = getStockData()
    for i in itemMessage:
        text = i.split(" . ")
        itemData = stock.get(text[0])

        if itemData:
            item = Item(text[0], None, None, dictData=itemData)
            try:
                quantity = int(text[2])
            except:
                await update.message.reply_text("can't process item", i[0])
                return "updateStock"
            
            newQuantity = ops[text[1]](item.getQuantity(), quantity)
            if  newQuantity > 0:
                item.setQuantity(newQuantity)
                stock.update(item.getDict())
                await update.message.reply_text(f"{text[0]} stock item is updated")
            else:
                 await update.message.reply_text(f"There is no {text[0]} ready in the stock items")
        else:
            await update.message.reply_text(f"There is no {text[0]} in stock items")

    storeStockData(stock)
    await getStock(update, context)

async def doneStock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Session end...")
    return ConversationHandler.END


# transation handling
def storeTransactionDataMongo(update, data):
    transactionData = {
        "day" : data["date"]["day"],
        "month" : data["date"]["month"],
        "year" : data["date"]["year"],
        "customer" : data["customer"],
        "order" : data["order"]
    }

    transactionDB = db["transaction"]
    transactionDB.insert_one(transactionData)

async def transactionStart(update, context):
    if(validateUser(update.effective_user)):
        await update.message.reply_text("Input order date: ([dd]-[mm]-[yyyy])")
        return "customer"

async def processCustomer(update, context : ContextTypes.DEFAULT_TYPE):
        message = update.effective_message.text
        iteMessage = message.split("-")
        dateData = {
            "day" : iteMessage[0],
            "month" : iteMessage[1],
            "year" : iteMessage[2]
        }

        context.user_data["transaction"] = {
            "date" : dateData
        }

        await update.message.reply_text("Input Custmer Name:")
        return "item"

async def processItem(update, context : ContextTypes.DEFAULT_TYPE):
    customer = context.user_data["transaction"].get("customer")
    if (customer == None):
        message = update.effective_message.text
        context.user_data["transaction"].update({
            "customer" : message
        })

    await getStock(update, context)
    await update.message.reply_text("Input ordered item: ([name] . [number])")
    return "transaction"

async def transactionValidation(update, context):
    message = update.effective_message.text
    itemMessage = message.split("\n")

    stockData = getStockData()

    totalPrice = 0
    order = {}

    for items in itemMessage:
        i = items.split(" . ")
        orderItem = stockData.get(i[0])
        try:
            sumOrder = int(i[1])
        except :
            await update.message.reply_text("can't process item", i[0])
            return "item"
    
        item = Item(None, None, None, orderItem)
        if orderItem == None:
            await update.message.reply_text("No", i[0], " in stock")
            return ConversationHandler.END
        elif item.getQuantity() < sumOrder:
            await update.message.reply_text("No stock ready for", i[0])
            return ConversationHandler.END
        
        price = item.getPrice() * sumOrder
        totalPrice = totalPrice + price

        order.update({
            i[0] : {
                "quantity" : sumOrder,
                "price" : price
            }
        })

    context.user_data["transaction"].update({
            "order" : order,
            "Total Price" : totalPrice
        })
    
    date = context.user_data["transaction"].get("date")
    confirmationMessage = f"Date \t: {date.get("day")} - {date.get("month")} - {date.get("year")}"
    confirmationMessage += f"\nCustmer \t: {context.user_data["transaction"].get("customer")}"
    confirmationMessage += f"\nOrder \t:"
    for i in order.keys():
        orderMessage = f"\n\t\t - {i} : {order.get(i)["quantity"]}"
        confirmationMessage += orderMessage
    confirmationMessage += f"\n\nTotal price \t: {totalPrice}"

    await update.message.reply_text(confirmationMessage)
    await update.message.reply_text("transaction check: [y/n]")

    # confirmation of no return to earlier state
    return "success"

async def processTransaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # transaction json
    message = update.effective_message.text
    message = message.strip()

    if message.strip() == "n":
        await update.message.reply_text("transaction cancelled...")
        return ConversationHandler.END
    
    data = context.user_data["transaction"]

    # process stock
    inputMessage = ""
    order = data.get("order")
    for i in order:
        item = order.get(i)
        inputMessage = inputMessage + f"\n{i} . - . {item["quantity"]}"
    await inputStockItem(update, context, inputMessage.strip())

    # Store transaction data to mongo
    storeTransactionDataMongo(update, data)
    
    # Store transaction to database
    date = data.get("date")
    # foder check
    folderPath = f"Data/{date.get("year")}/{date.get("month")}"
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    filePath = folderPath + f"/{date.get("day")}-{date.get("month")}-{date.get("year")}.json"
    transaction = []
    # file check
    if os.path.exists(filePath):
        with open(filePath, "r") as userFile:
            transaction = json.load(userFile)

    transaction.append(data)
    with open(filePath, "w") as userFile:
        json.dump(transaction, userFile, indent=4)

    await update.message.reply_text("Transcation recorded...")

    # generate recipt
    generateRecipt.generateRecipt(data)
    chat_id = update.effective_chat.id
    with open("Data/recipt.pdf", "rb") as file:
        await context.bot.send_document(chat_id=chat_id, document=file, filename="recipt.pdf")

    return ConversationHandler.END
    
async def cancelTransaction(update, context):
    await update.message.reply_text("Transaction canceled...")
    return ConversationHandler.END

# get all data
async def getAllData(update, context):
    try:
        with open("Data/Stock.json", "rb") as file:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=file, filename="stock.json")
    except:
        logging.warning("No stock data")
    
    try:
        users = getUsersDataMongo()
        await update.message.reply_text(f"{users}")
    except:
        logging.warning("No user Data")


    for i in os.listdir('Data/'):
        if os.path.isdir(f'Data/{i}'):
            for j in os.listdir(f'Data/{i}'):
                for k in os.listdir(f'Data/{i}/{j}'):
                    try:
                        with open(f"Data/{i}/{j}/{k}", "rb") as file:
                            await context.bot.send_document(chat_id=update.effective_chat.id, document=file, filename=f"{k}")
                    except:
                        logging.warning("No Data")

# app
app = ApplicationBuilder().token(TOKEN).build()

# handle user inputed command
app.add_handler(CommandHandler("start", startCommand))

# user
app.add_handler(CommandHandler("userRegistration", userRegistration))
app.add_handler(CommandHandler("openRegistration", openRegistration))
app.add_handler(CommandHandler("closeRegistration", closeRegistration))

# stock and item
addItemConv = ConversationHandler(
    entry_points=[CommandHandler("addItem", addItem)],
    states={
        "inputItem": [MessageHandler(filters.TEXT & ~filters.COMMAND, inputItem)],
    },
    fallbacks=[CommandHandler("done", doneStock)],
)

udpateStockConv = ConversationHandler(
    entry_points=[CommandHandler("updateStock", updateStock)],
    states={
        "inputStock": [MessageHandler(filters.TEXT & ~filters.COMMAND, inputStock)],
        "updateStock": [MessageHandler(filters.TEXT & ~filters.COMMAND, updateStock)],
    },
    fallbacks=[CommandHandler("done", doneStock)],
)

app.add_handler(addItemConv)
app.add_handler(udpateStockConv)
app.add_handler(CommandHandler("getStock", getStock))

# transaction
transactionConv = ConversationHandler(
    entry_points=[CommandHandler("addTransaction", transactionStart)],
    states={
        "item": [MessageHandler(filters.TEXT & ~filters.COMMAND, processItem)],
        "customer": [MessageHandler(filters.TEXT & ~filters.COMMAND, processCustomer)],
        "transaction": [MessageHandler(filters.TEXT & ~filters.COMMAND, transactionValidation)],
        "success": [MessageHandler(filters.TEXT & ~filters.COMMAND, processTransaction)],
    },
    fallbacks=[CommandHandler("cancelTransaction", cancelTransaction)],
)

# add convert transaction data to excel data (upcoming)
app.add_handler(transactionConv)


# test message handling
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (validateUser(update.effective_user)):    
        await update.message.reply_text("Ask admin to register account..")
    else :
        await update.message.reply_text(update.effective_message)
        await update.message.reply_text(update.effective_chat)

# handle user message
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# get all data handler
app.add_handler(CommandHandler("getAllData", getAllData))


app.run_polling(3)