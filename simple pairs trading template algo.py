#Importing stuff
import numpy as np
import statsmodels.api as sm
import pandas as pd
from zipline.utils import tradingcalendar
import pytz

#Defining initialize function
def initialize(context):
    #Quantopian backtester specific variables
    set_slippage(slippage.FixedSlippage(spread=0))
    set_commission(commission.PerTrade(cost=1))
    set_symbol_lookup_date('2014-01-01')
    
    #Assuming these are the cointegrated securitites as returned after calculating cointegration parameters as shown in the notebook for Pairs Trading
    context.stock_pairs = [(symbol('ABGB'), symbol('FSLR')),
                           (symbol('CSUN'), symbol('ASTI'))]
    
    context.num_pairs = len(context.stock_pairs)
    
    #Strategy specific variables
    context.lookback = 20 #Used for regression
    context.z_window = 20 #Used for the z-score calculation, must be <= lookback
    
    context.spread = np.ndarray((context.num_pairs,0))
    
    context.inLong = [False] * context.num_pairs
    context.inShort = [False] * context.num_pairs
    
    #Only do work 30 minutes before the close every day
    schedule_function(func=check_pair_status, date_rule=date_rules.every_day(), time_rule=time_rules.market_close(minutes=30))
    
# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    # Our work is now scheduled in check_pair_status
    pass

#Defining the logic in check pair status function
def check_pair_status(context, data):
    if get_open_orders():
        return
    
    #prices = history(35, '1d', 'price').iloc[-context.lookback::]
    
    new_spreads = np.ndarray((context.num_pairs, 1))
    
    for i in range(context.num_pairs):
        
        (stock_y, stock_x) = context.stock_pairs[i]
        
        Y = data.history(stock_y, 'price', 36, '1d').iloc[-context.lookback::]
        X = data.history(stock_x, 'price', 36, '1d').iloc[-context.lookback::]
        
        try:
            hedge = hedge_ratio(Y, X, add_const = True)
        except ValueError as e:
            log.debug(e)
            return
        
        new_spreads[i, :] = Y[-1] - hedge * X[-1]
        
        if context.spread.shape[1] > context.z_window:
            #Keep only the z-score lookback period
            spreads = context.spread[i, -context.z_window:]
            
            zscore = (spreads[-1] - spreads.mean()) / spreads.std()
            
            #If already present in either long or short list, sell the stock
            if context.inShort[i] and zscore < 0.0:
                order_target(stock_y, 0)
                order_target(stock_x, 0)
                context.inShort[i] = False
                context.inLong[i] = False
                record(X_pct=0, Y_pct=0)
                return
            
            if context.inLong[i] and zscore > 0.0:
                order_target(stock_y, 0)
                order_target(stock_x, 0)
                context.inShort[i] = False
                context.inLong[i] = False
                record(X_pct=0, Y_pct=0)
                return
            
            if zscore < -1.0 and (not context.inLong[i]):
                #Only trade if NOT already in a trade
                y_target_shares = 1
                X_target_shares = -hedge
                context.inShort[i] = False
                context.inLong[i] = True
                
                (y_target_pct, x_target_pct) = computeHoldingsPct(y_target_shares, X_target_shares, Y[-1], X[-1])
                order_target_percent( stock_y, y_target_pct * (1.0/context.num_pairs) / float(context.num_pairs) )
                order_target_percent( stock_x, x_target_pct * (1.0/context.num_pairs) / float(context.num_pairs) )
                record(Y_pct=y_target_pct, X_pct=x_target_pct)
                return
            
            if zscore > 1.0 and (not context.inShort[i]):
                # Only trade if NOT already in a trade
                y_target_shares = -1
                X_target_shares = hedge
                context.inShort[i] = True
                context.inLong[i] = False

                (y_target_pct, x_target_pct) = computeHoldingsPct( y_target_shares, X_target_shares, Y[-1], X[-1] )
                order_target_percent( stock_y, y_target_pct * (1.0/context.num_pairs) / float(context.num_pairs) )
                order_target_percent( stock_x, x_target_pct * (1.0/context.num_pairs) / float(context.num_pairs) )
                record(Y_pct=y_target_pct, X_pct=x_target_pct)
        
    context.spread = np.hstack([context.spread, new_spreads])
    
def hedge_ratio(Y, X, add_const=True):
    if add_const:
        X = sm.add_constant(X)
        model = sm.OLS(Y, X).fit()
        return model.params[1]
    model = sm.OLS(Y, X).fit()
    return model.params.values

def computeHoldingsPct(yShares, xShares, yPrice, xPrice):
    yDol = yShares * yPrice
    xDol = xShares * xPrice
    notionalDol = abs(yDol) + abs(xDol)
    y_target_pct = yDol / notionalDol
    x_target_pct = xDol / notionalDol
    return (y_target_pct, x_target_pct)