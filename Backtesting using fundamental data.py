#https://pythonprogramming.net/python-programming-finance-fundamental-data/?completed=/python-programming-finance-back-testing/

#backtesting with fundamental data

def initialize(context):
    context.limit = 10
    schedule_function(rebalance,date_rule = date_rules.every_day(),time_rule = time_rules.market_open())
    
#method run each day before the trading. Due to fundamentals of a company changing, we desire some scheduling
def before_trading_start(context):
    context.fundamentals = get_fundamentals(
        query(
            fundamentals.valuation_ratios.pb_ratio,
            fundamentals.valuation_ratios.pe_ratio,
        )
        .filter(
            fundamentals.valuation_ratios.pe_ratio < 14
        )
        .filter(
            fundamentals.valuation_ratios.pb_ratio < 2
        )
        .order_by(
            fundamentals.valuation.market_cap.desc()
        )
        .limit(context.limit)
    )
    
    context.assets = context.fundamentals.columns.values
    
def rebalance(context,data):
    for stock in context.portfolio.positions:
        if stock not in context.fundamentals and data.can_trade(stock):
            order_target_percent(stock,0)
    
def handle_data(context, data):
    cash = context.portfolio.cash
    current_positions = context.portfolio.positions
    
    for stock in context.assets:
        current_position = context.portfolio.positions[stock].amount
        stock_price = data.current(stock,'price')
        plausible_investment = cash / context.limit
        stop_price = stock_price - (stock_price*0.005)
        
        share_amount = int(plausible_investment / stock_price)
        
        #buying logic
        try:
            if stock_price < plausible_investment:
                if current_position == 0:
                    if context.fundamentals[stock]['pe_ratio'] < 11:
                        order(stock, share_amount, style=StopOrder(stop_price))
        except Exception as e:
            print(str(e))