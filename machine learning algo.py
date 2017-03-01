#https://pythonprogramming.net/python-programming-finance-machine-learning-framework/?completed=/python-programming-finance-understanding-hedgefunds/

#Trying for machine learning

#importing classifiers
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC, LinearSVC, NuSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn import preprocessing
from collections import Counter
import numpy as np

#initializing stocks and history data size and feature wiindow for machine learning prediction
def initialize(context):

    context.stocks = symbols('XLY',  # XLY Consumer Discrectionary SPDR Fund   
                           'XLF',  # XLF Financial SPDR Fund  
                           'XLK',  # XLK Technology SPDR Fund  
                           'XLE',  # XLE Energy SPDR Fund  
                           'XLV',  # XLV Health Care SPRD Fund  
                           'XLI',  # XLI Industrial SPDR Fund  
                           'XLP',  # XLP Consumer Staples SPDR Fund   
                           'XLB',  # XLB Materials SPDR Fund  
                           'XLU')  # XLU Utilities SPRD Fund
    
    context.historical_bars = 100
    context.feature_window = 10
    

   

def handle_data(context, data):
    #extracting prices for the last 100 days
    prices = data.history(context.stocks,'price',context.historical_bars,'1d')

    for stock in context.stocks:
        try:
            #calculating short term and short term MAs
            da = data.history(stock,'price',50,'1d')
            ma1 = da.mean()
            da = data.history(stock,'price',200,'1d')
            ma2 = da.mean()

            #extracting prices of interest and storing them in a list
            start_bar = context.feature_window
            price_list = prices[stock].tolist()

            X = [] #list of features
            y = [] #list of prediction labels

            bar = start_bar

            # feature creation
            while bar < len(price_list)-1:
                try:
                    end_price = price_list[bar+1]
                    begin_price = price_list[bar]

                    pricing_list = []
                    xx = 0
                    for _ in range(context.feature_window):
                        price = price_list[bar-(context.feature_window-xx)]
                        pricing_list.append(price)
                        xx += 1

                    features = np.around(np.diff(pricing_list) / pricing_list[:-1] * 100.0, 1)


                    #print(features)

                    if end_price > begin_price:
                        label = 1
                    else:
                        label = -1

                    bar += 1
                    X.append(features)
                    y.append(label)

                except Exception as e:
                    bar += 1
                    print(('feature creation',str(e)))




            clf1 = RandomForestClassifier()
            clf2 = LinearSVC()
            clf3 = NuSVC()
            clf4 = LogisticRegression()

            last_prices = price_list[-context.feature_window:]
            current_features = np.around(np.diff(last_prices) / last_prices[:-1] * 100.0, 1)

            X.append(current_features)
            X = preprocessing.scale(X)

            current_features = X[-1]
            X = X[:-1]

            clf1.fit(X,y)
            clf2.fit(X,y)
            clf3.fit(X,y)
            clf4.fit(X,y)

            p1 = clf1.predict(current_features)[0]
            p2 = clf2.predict(current_features)[0]
            p3 = clf3.predict(current_features)[0]
            p4 = clf4.predict(current_features)[0]
            
            
            if Counter([p1,p2,p3,p4]).most_common(1)[0][1] >= 4:
                p = Counter([p1,p2,p3,p4]).most_common(1)[0][0]
                
            else:
                p = 0
                
            print(('Prediction',p))


            if p == 1 and ma1 > ma2:
                order_target_percent(stock,0.11)
            elif p == -1 and ma1 < ma2:
                order_target_percent(stock,-0.11)

        except Exception as e:
            print(str(e))
            
            
    record('ma1',ma1)
    record('ma2',ma2)
    record('Leverage',context.account.leverage)