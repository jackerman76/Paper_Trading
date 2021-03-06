from yahoo_fin import stock_info as si
import datetime
import pandas as pd
import pickle
import numpy as np
import requests
from bs4 import BeautifulSoup

SHARES_NUM = 0
AMOUNT = 1

def market_open_today():
    page=requests.get("https://www.tradinghours.com/open")
    content=page.content
    soup=BeautifulSoup(content,"html.parser")

    all=soup.find("p",{"class":"display-4 text-center my-5"}).text

    if "open" in all:
        return True
    if "closed" in all:
        return False

def market_open_now():
    tz = pytz.timezone('US/Eastern')
    now = datetime.datetime.now(tz)
    openTime = datetime.time(hour = 9, minute = 30, second = 0)
    closeTime = datetime.time(hour = 16, minute = 0, second = 0)
    if market_open_now():
        # If before 0930 or after 1600
        if (now.time() < openTime) or (now.time() > closeTime):
            return False
        # If it's a weekend
        if now.date().weekday() > 4:
            return False

    return False

def get_stock_price(ticker):
    price = si.get_live_price(ticker)
    return price

def clear_transaction_log(start_val):
    df = pd.DataFrame({"time":[datetime.datetime.now()],
                       "ticker":[0],
                       "transaction":[0],
                       "stock_price":[0],
                       "number_of_shares":[0],
                       "amount":[0],
                       "account_balance":[start_val]})

    set_transaction_log(df)
    position_dict = {}
    set_position_dict(position_dict)

def buy_stock(ticker, number_of_shares):
    df = get_transaction_log()
    stock_price = get_stock_price(ticker)
    amount = stock_price * number_of_shares
    df2 = pd.DataFrame({"time":[datetime.datetime.now()],
                        "ticker":[ticker],
                        "transaction":["buy_stock"],
                        "stock_price":[stock_price],
                        "number_of_shares":[number_of_shares],
                        "amount":[amount],
                        "account_balance":[get_account_balance(df) - amount]
                       })
    df = df.append(df2, ignore_index=True)
    append_position_dict(ticker, number_of_shares, amount, "buy")
    set_transaction_log(df)

def buy_varified(ticker, number_of_shares):
    stock_price = get_stock_price(ticker)
    amount = stock_price * number_of_shares
    df = get_transaction_log()
    balance = get_account_balance(df)
    if amount <= balance:
        return True
    else:
        return False

def sell_varified(ticker, number_of_shars):
    positions = get_position_dict()
    if ticker in positions:
        if positions[ticker][SHARES_NUM] >= number_of_shars:
            return True
    else:
        return False

def sell_stock(ticker, number_of_shares):
    df = get_transaction_log()
    stock_price = get_stock_price(ticker)
    amount = stock_price * number_of_shares
    df2 = pd.DataFrame({"time":[datetime.datetime.now()],
                        "ticker":[ticker],
                        "transaction":["sell_stock"],
                        "stock_price":[stock_price],
                        "number_of_shares":[number_of_shares],
                        "amount":[amount],
                        "account_balance":[get_account_balance(df) + amount]
                       })
    df = df.append(df2, ignore_index=True)
    append_position_dict(ticker, number_of_shares, amount, "sell")
    set_transaction_log(df)

def append_position_dict(ticker, shares_num, amount, transaction):
    dict = get_position_dict()
    if ticker in dict and transaction == "buy":
        cur_shares = dict[ticker][SHARES_NUM]
        cur_amount = dict[ticker][AMOUNT]
        dict[ticker] = [shares_num + cur_shares, amount + cur_amount]
    if ticker not in dict and transaction == "buy":
        dict[ticker] = [shares_num, amount]
    if ticker in dict and transaction == "sell":
        cur_shares = dict[ticker][SHARES_NUM]
        cur_amount = dict[ticker][AMOUNT]
        if cur_shares == shares_num:
            dict.pop(ticker, None)
        if cur_shares > shares_num:
            dict[ticker] = [cur_shares - shares_num, cur_amount - amount]
    set_position_dict(dict)

def get_account_balance(df):
    last_row = df.tail(1)
    balance = last_row["account_balance"].values[0]
    return balance

def set_transaction_log(df):
    pickle_out = open("transaction_log.pickle","wb")
    pickle.dump(df, pickle_out)
    pickle_out.close()

def get_transaction_log():
    pickle_in = open("transaction_log.pickle","rb")
    df = pickle.load(pickle_in)
    return df

def set_position_dict(dict):
    pickle_out = open("position_dict.pickle","wb")
    pickle.dump(dict, pickle_out)
    pickle_out.close()

def get_position_dict():
    pickle_in = open("position_dict.pickle","rb")
    dict = pickle.load(pickle_in)
    return dict

def update_position_values():
    dict = get_position_dict()
    for key in dict:
        dict[key][AMOUNT] = get_stock_price(key)

def create_order_list():
    pickle_out = open("order_list.pickle","wb")
    dict = {}
    pickle.dump(dict, pickle_out)
    pickle_out.close()

def get_order_list():
    pickle_in = open("order_list.pickle","rb")
    dict = pickle.load(pickle_in)
    return dict

def set_order_list(dict):
    pickle_out = open("order_list.pickle","wb")
    pickle.dump(dict, pickle_out)
    pickle_out.close()

def set_limit_order(ticker, number_of_shares, buy_price):
    stock_price = get_stock_price(ticker)
    amount = stock_price * number_of_shares
    df = get_position_dict()
    balance = get_account_balance(df)
    order_list = get_order_list()
    if balance >= amount:
        order_list[ticker] = [number_of_shares, buy_price, "limit"]
    set_order_list(order_list)

def set_stop_order(ticker, number_of_shares, sell_price):
    order_list = get_order_list()
    positions = get_position_dict()
    if ticker in positions and positions[ticker][SHARES_NUM] >= number_of_shares:
        order_list[ticker] = [number_of_shares, buy_price, "stop"]
    set_order_list(order_list)


def main():
    #clear_transaction_log(starting ammount)
    clear_transaction_log(1000)

    if buy_varified("aapl", 3):
        buy_stock("aapl", 3)
    else:
        print("Unable to process transaction")
    print(get_position_dict())
    print()

    if buy_varified("aapl", 2):
        buy_stock("aapl", 2)
    else:
        print("Unable to process transaction")
    print(get_position_dict())
    print()

    buy_stock("f", 15)
    print(get_position_dict())
    print()

    if sell_varified("aapl", 6):
        sell_stock("aapl", 6)
    else:
        print("Unable to process transaction")
    print(get_position_dict())
    print()

    if sell_varified("pnc", 2):
        sell_stock("pnc", 2)
    else:
        print("Unable to process transaction")
    print(get_position_dict())
    print()

    update_position_values()

    log = get_transaction_log()
    print(log)


if __name__ == '__main__':
    main()
