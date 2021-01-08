

import sys
import math
from collections import deque
import io
from .ordertree import OrderTree
import datetime



class OrderBook(object):
    def __init__(self, tick_size = 0.0001):
        self.tape = deque(maxlen=None) # Index [0] is most recent trade
        self.buy = OrderTree()
        self.sell = OrderTree()
        self.lastTick = None
        self.lastTimestamp = 0
        self.tickSize = tick_size
        self.time = datetime.datetime.now()
        self.nextQuoteID = 0
        
    def clipPrice(self, price):
        """ Clips the price according to the ticksize """
        return round(price, int(math.log10(1 / self.tickSize)))
    
    def updateTime(self):
        self.time+=datetime.timedelta(days = 1)
    
    def processOrder(self, quote, fromData, verbose):
        orderType = quote['type']
        orderInBook = None
        if fromData:
            self.time = quote['timestamp']
        else:
            self.updateTime()
            quote['timestamp'] = self.time
        if quote['qty'] <= 0:
            sys.exit('processLimitOrder() given order of qty <= 0')
        if not fromData: self.nextQuoteID += 1
        if orderType=='market':
            trades = self.processMarketOrder(quote, verbose)
        elif orderType=='limit':
            quote['price'] = self.clipPrice(quote['price'])
            trades, orderInBook = self.processLimitOrder(quote, fromData, verbose)
        else:
            sys.exit("processOrder() given neither 'market' nor 'limit'")
        return trades, orderInBook
    
    def processOrderList(self, side, orderlist, 
                         qtyStillToTrade, quote, verbose):
        '''
        Takes an order list (stack of orders at one price) and 
        an incoming order and matches appropriate trades given 
        the orders quantity.
        '''
        trades = []
        qtyToTrade = qtyStillToTrade
        while len(orderlist) > 0 and qtyToTrade > 0:
            headOrder = orderlist.getHeadOrder()
            tradedPrice = headOrder.price
            counterparty = headOrder.tid
            if qtyToTrade < headOrder.qty:
                tradedQty = qtyToTrade
                # Amend book order
                newBookQty = headOrder.qty - qtyToTrade
                headOrder.updateQty(newBookQty, headOrder.timestamp)
                # Incoming done with
                qtyToTrade = 0
            elif qtyToTrade == headOrder.qty:
                tradedQty = qtyToTrade
                if side=='buy':
                    # Hit the buy
                    self.buy.removeOrderById(headOrder.idNum)
                else:
                    # Lift the sell
                    self.sell.removeOrderById(headOrder.idNum)
                # Incoming done with
                qtyToTrade = 0
            else:
                tradedQty = headOrder.qty
                if side=='buy':
                    # Hit the buy
                    self.buy.removeOrderById(headOrder.idNum)
                else:
                    # Lift the sell
                    self.sell.removeOrderById(headOrder.idNum)
                # We need to keep eating into volume at this price
                qtyToTrade -= tradedQty
            if verbose: print('>>> TRADE \nt=%d $%f n=%d p1=%d p2=%d' % 
                              (self.time, tradedPrice, tradedQty, 
                               counterparty, quote['tid']))
            
            transactionRecord = {'timestamp': self.time,
                                 'price': tradedPrice,
                                 'qty': tradedQty,
                                 'time': self.time}
            if side == 'buy':
                transactionRecord['Order1'] = [counterparty, 
                                               'buy', 
                                               headOrder.idNum]
                transactionRecord['Order2'] = [quote['tid'], 
                                               'sell',
                                               None]
            else:
                transactionRecord['Order1'] = [counterparty, 
                                               'sell', 
                                               headOrder.idNum]
                transactionRecord['Order2'] = [quote['tid'], 
                                               'buy',
                                               None]
            self.tape.append(transactionRecord)
            trades.append(transactionRecord)
        return qtyToTrade, trades
    
    def processMarketOrder(self, quote, verbose):
        trades = []
        qtyToTrade = quote['qty']
        side = quote['side']
        if side == 'buy':
            while qtyToTrade > 0 and self.sell: 
                bestPricesells = self.sell.minPriceList()
                qtyToTrade, newTrades = self.processOrderList('sell', 
                                                                 bestPricesells, 
                                                                 qtyToTrade, 
                                                                 quote, verbose)
                trades += newTrades
        elif side == 'sell':
            while qtyToTrade > 0 and self.buy: 
                bestPricebuys = self.buy.maxPriceList()
                qtyToTrade, newTrades = self.processOrderList('buy', 
                                                                 bestPricebuys, 
                                                                 qtyToTrade, 
                                                                 quote, verbose)
                trades += newTrades
        else:
            sys.exit('processMarketOrder() received neither "buy" nor "sell"')
        return trades
    
    def processLimitOrder(self, quote, fromData, verbose):
        orderInBook = None
        trades = []
        qtyToTrade = quote['qty']
        side = quote['side']
        price = quote['price']
        if side == 'buy':
            while (self.sell and 
                   price >= self.sell.minPrice() and 
                   qtyToTrade > 0):
                bestPricesells = self.sell.minPriceList()
                qtyToTrade, newTrades = self.processOrderList('sell', 
                                                              bestPricesells, 
                                                              qtyToTrade, 
                                                              quote, verbose)
                trades += newTrades
            # If volume remains, add to book
            if qtyToTrade > 0:
                if not fromData:
                    quote['idNum'] = self.nextQuoteID
                quote['qty'] = qtyToTrade
                self.buy.insertOrder(quote)
                orderInBook = quote
        elif side == 'sell':
            while (self.buy and 
                   price <= self.buy.maxPrice() and 
                   qtyToTrade > 0):
                bestPricebuys = self.buy.maxPriceList()
                qtyToTrade, newTrades = self.processOrderList('buy', 
                                                              bestPricebuys, 
                                                              qtyToTrade, 
                                                              quote, verbose)
                trades += newTrades
            # If volume remains, add to book
            if qtyToTrade > 0:
                if not fromData:
                    quote['idNum'] = self.nextQuoteID
                quote['qty'] = qtyToTrade
                self.sell.insertOrder(quote)
                orderInBook = quote
        else:
            sys.exit('processLimitOrder() given neither buy nor sell')
        return trades, orderInBook

    def cancelOrder(self, side, idNum, time = None):
        if time:
            self.time = time
        else:
            self.updateTime()
        if side == 'buy':
            if self.buy.orderExists(idNum):
                self.buy.removeOrderById(idNum)
        elif side == 'sell':
            if self.sell.orderExists(idNum):
                self.sell.removeOrderById(idNum)
        else:
            sys.exit('cancelOrder() given neither buy nor sell')
    
    def modifyOrder(self, idNum, orderUpdate, time=None):
        if time:
            self.time = time
        else:
            self.updateTime()
        side = orderUpdate['side']
        orderUpdate['idNum'] = idNum
        orderUpdate['timestamp'] = self.time
        if side == 'buy':
            if self.buy.orderExists(orderUpdate['idNum']):
                self.buy.updateOrder(orderUpdate)
        elif side == 'sell':
            if self.sell.orderExists(orderUpdate['idNum']):
                self.sell.updateOrder(orderUpdate)
        else:
            sys.exit('modifyOrder() given neither buy nor sell')
    
    def getVolumeAtPrice(self, side, price):
        price = self.clipPrice(price)
        if side =='buy':
            vol = 0
            if self.buy.priceExists(price):
                vol = self.buy.getPrice(price).volume
            return vol
        elif side == 'sell':
            vol = 0
            if self.sell.priceExists(price):
                vol = self.sell.getPrice(price).volume
            return vol
        else:
            sys.exit('getVolumeAtPrice() given neither buy nor sell')
    
    def getBestbuy(self):
        return self.buy.maxPrice()
    def getWorstbuy(self):
        return self.buy.minPrice()
    def getBestsell(self):
        return self.sell.minPrice()
    def getWorstsell(self):
        return self.sell.maxPrice()
    
    def tapeDump(self, fname, fmode, tmode):
            dumpfile = open(fname, fmode)
            for tapeitem in self.tape:
                dumpfile.write('%s, %s, %s\n' % (tapeitem['time'], 
                                                 tapeitem['price'], 
                                                 tapeitem['qty']))
            dumpfile.close()
            if tmode == 'wipe':
                    self.tape = []
        
    def __str__(self):
        fileStr = io.BytesIO()
        fileStr.write("------ buys -------\n")
        if self.buy != None and len(self.buy) > 0:
            for k, v in self.buy.priceTree.items(reverse=True):
                fileStr.write('%s' % v)
        fileStr.write("\n------ sells -------\n")
        if self.sell != None and len(self.sell) > 0:
            for k, v in self.sell.priceTree.items():
                fileStr.write('%s' % v)
        fileStr.write("\n------ Trades ------\n")
        if self.tape != None and len(self.tape) > 0:
            num = 0
            for entry in self.tape:
                if num < 5:
                    fileStr.write(str(entry['qty']) + " @ " + 
                                  str(entry['price']) + 
                                  " (" + str(entry['timestamp']) + ")\n")
                    num += 1
                else:
                    break
        fileStr.write("\n")
        return fileStr.getvalue()

