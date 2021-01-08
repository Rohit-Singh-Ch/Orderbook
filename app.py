

if __name__ == '__main__':
    
    
    from OrderFiles import OrderBook
    
    
    
    # Create a Obj object
    Obj = OrderBook()
    
    ########### Limit Orders #############
    
    # Create some limit orders
    someOrders = [{'type' : 'limit', 
                   'side' : 'buy', 
                    'qty' : 5, 
                    'price' : 101,
                    'tid' : 100},
                   {'type' : 'limit', 
                    'side' : 'sell', 
                    'qty' : 5, 
                    'price' : 103,
                    'tid' : 101},
                   {'type' : 'limit', 
                    'side' : 'sell', 
                    'qty' : 5, 
                    'price' : 101,
                    'tid' : 102},
                   {'type' : 'limit', 
                    'side' : 'sell', 
                    'qty' : 5, 
                    'price' : 101,
                    'tid' : 103},
                   {'type' : 'limit', 
                    'side' : 'buy', 
                    'qty' : 5, 
                    'price' : 99,
                    'tid' : 100},
                   {'type' : 'limit', 
                    'side' : 'buy', 
                    'qty' : 5, 
                    'price' : 98,
                    'tid' : 101},
                   {'type' : 'limit', 
                    'side' : 'buy', 
                    'qty' : 5, 
                    'price' : 99,
                    'tid' : 102},
                   {'type' : 'limit', 
                    'side' : 'buy', 
                    'qty' : 5, 
                    'price' : 97,
                    'tid' : 103},
                   ]
    
    # Add orders to LOB
    for order in someOrders:
        trades, idNum = Obj.processOrder(order, False, False)
    
    # The current book may be viewed using a print
    print (Obj)
    
    # Submitting a limit order that crosses the opposing best price will 
    # result in a trade.
    crossingLimitOrder = {'type' : 'limit', 
                          'side' : 'buy', 
                          'qty' : 2, 
                          'price' : 102,
                          'tid' : 109}
    trades, orderInBook = Obj.processOrder(crossingLimitOrder, False, False)
    print ("Trade occurs as incoming buy limit crosses best sell.")
    print (trades)
    print (Obj)
    
    # If a limit order crosses but is only partially matched, the remaining 
    # volume will be placed in the book as an outstanding order
    bigCrossingLimitOrder = {'type' : 'limit', 
                             'side' : 'buy', 
                             'qty' : 50, 
                             'price' : 102,
                             'tid' : 110}
    trades, orderInBook = Obj.processOrder(bigCrossingLimitOrder, False, False)
    print ("Large incoming buy limit crosses best sell.\nRemaining volume is placed in the book.")
    print (Obj)
    
    ############# Market Orders ##############
    
    # Market orders only require that the user specifies a side (buy
    # or sell), a quantity and their unique tid.
    marketOrder = {'type' : 'market', 
                   'side' : 'sell', 
                   'qty' : 40, 
                   'tid' : 111}
    trades, idNum = Obj.processOrder(marketOrder, False, False)
    print ("A limit order takes the specified volume from the inside of the book, regardless of price." )
    print ("A market sell for 40 results in.")
    print (Obj)
    
    ############ Cancelling Orders #############
    
    # Order can be cancelled simply by submitting an order idNum and a side
    print ("cancelling buy for 5 @ 97")
    Obj.cancelOrder('buy', 8)
    print (Obj)
    
    ########### Modifying Orders #############
    
    # Orders can be modified by submitting a new order with an old idNum
    Obj.modifyOrder(5, {'side' : 'buy', 
                    'qty' : 14, 
                    'price' : 99,
                    'tid' : 100})
    print ("book after modify")
    print (Obj)
    