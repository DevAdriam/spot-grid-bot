import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from colorama import Fore, Style, init
import time
from datetime import datetime

# Initialize colorama
init()

# Initialize the Binance client
# Binance Test API keys
API_KEY = input("Enter your test api key :")
API_SECRET = input("Enter your test api secret")

# Initialize the Binance client
client = Client(API_KEY, API_SECRET)
client.API_URL = 'https://testnet.binance.vision/api'

# coin and prize
symbol = input("Enter your coin symbol :")
quantity = input("Amount you trade : ")

# Set up logging
logging.basicConfig(filename='trading_log.txt',
                    level=logging.INFO, format='%(message)s')


def log_transaction(action, symbol, price, amount_usdt, amount_coin, wallet_usdt, wallet_coin, condition):
    """Log the transaction details to a file."""
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = (f"{time_now} | {action} | Symbol: {symbol} | Price: {price:.6f} USDT | "
                   f"Amount: {amount_coin:.6f} {symbol[:-4]} | "
                   f"Amount in USDT: {amount_usdt:.6f} USDT | "
                   f"{action} at condition: {condition:.6f}  | "
                   f"Wallet USDT: {wallet_usdt:.6f} | Wallet {symbol[:-4]}: {wallet_coin:.6f}")
    logging.info(log_message)


def get_price(symbol):
    """Fetch the latest price for a given symbol."""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except BinanceAPIException as e:
        print(f"{Fore.RED}Error fetching price for { symbol}: {e.message}{Style.RESET_ALL}")
        return None


def get_asset_balance(asset):
    """Fetch the balance of a specific asset."""
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance['free'])
    except BinanceAPIException as e:
        print(f"{Fore.RED}Error fetching balance for {asset}: {e.message}{Style.RESET_ALL}")
        return None


def get_last_order(symbol, order_type):
    """Fetch the last order price for a given symbol and order type."""
    try:
        orders = client.get_my_trades(symbol=symbol)
        if orders:
            if order_type == 'buy':
                for order in reversed(orders):
                    if order['isBuyer']:
                        return float(order['price'])
            elif order_type == 'sell':
                for order in reversed(orders):
                    if not order['isBuyer']:
                        return float(order['price'])
        return None
    except BinanceAPIException as e:
        print(f"{Fore.RED}Error fetching last order for {symbol}: {e.message}{Style.RESET_ALL}")
        return None


def calculate_profit_or_loss(buy_price, current_price, asset_balance):
    """Calculate profit or loss percentage based on buy price, current price, and asset balance."""
    if buy_price is None or current_price is None or asset_balance is None:
        print(f"{Fore.RED}Error: Missing data for profit or loss calculation.{ Style.RESET_ALL}")

        return None

    if buy_price <= 0:
        print(f"{Fore.RED}Error: Invalid buy price, cannot calculate profit or loss.{Style.RESET_ALL}")

        return None

    current_value = current_price * asset_balance
    buy_value = buy_price * asset_balance

    if buy_value <= 0:
        # print(f"{Fore.RED}Error: Buy value is zero or negative, cannot calculate profit or loss.{Style.RESET_ALL}")
        return 0

    profit_loss = (current_value - buy_value) / buy_value * 100

    print(f"{Fore.CYAN}Profit/Loss Calculation - Buy Price: {buy_price:.6f}, Current Price: { current_price:.6f}, Asset Balance: {asset_balance:.6f}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Calculated Profit/Loss: {profit_loss:.6f}%{Style.RESET_ALL}")

    return profit_loss


def trading_logic(symbol, quantity):
    """Implement the trading logic based on buy and sell conditions."""
    current_price = get_price(symbol)
    if current_price is None:
        return None, None, None, None

    last_sell_price = get_last_order(symbol, 'sell')
    last_buy_price = get_last_order(symbol, 'buy')

    buy_signal = None
    sell_signal = None
    buy_price = None
    sell_price = None

    # Calculate expected buy price levels based on the last sell price
    if last_sell_price is not None:
        expected_buy_level_1 = last_sell_price * (1 - 0.03)
        expected_buy_level_2 = last_sell_price * (1 - 0.04)
        expected_buy_level_3 = last_sell_price * (1 - 0.05)

        print(f"{Fore.GREEN}Expected buy levels: {Style.RESET_ALL}")
        print(f" - Buy level 1 (3% drop): ${expected_buy_level_1:.6f}")
        print(f" - Buy level 2 (4% drop): ${expected_buy_level_2:.6f}")
        print(f" - Buy level 3 (5% drop): ${expected_buy_level_3:.6f}")

    # Calculate expected sell price levels based on the last buy price
    if last_buy_price is not None:
        expected_sell_level_1 = last_buy_price * (1 + 0.03)
        expected_sell_level_2 = last_buy_price * (1 + 0.04)
        expected_sell_level_3 = last_buy_price * (1 + 0.05)

        print(f"{Fore.RED}Expected sell levels: {Style.RESET_ALL}")
        print(f" - Sell level 1 (3% rise): ${expected_sell_level_1:.6f}")
        print(f" - Sell level 2 (4% rise): ${expected_sell_level_2:.6f}")
        print(f" - Sell level 3 (5% rise): ${expected_sell_level_3:.6f}")

    # Buy Conditions
    if last_sell_price is not None:
        # Condition for buying based on price drop and bounce
        if current_price <= last_sell_price * (1 - 0.05):
            print(f"{Fore.YELLOW}Price dropped to 5% drop level: ${current_price:.6f}{Style.RESET_ALL}")
            while True:
                current_price = get_price(symbol)
                if current_price < last_sell_price * (1 - 0.05):
                    # Price has dropped further below 5% drop level
                    continue
                elif current_price >= last_sell_price * (1 - 0.05 + 0.005):
                    # Price bounced back to above 5% drop level but below 5.5% drop level
                    print(f"{Fore.GREEN}Buy Signal Triggered: Price bounced to ${ current_price:.6f} above 5% drop level{Style.RESET_ALL}")
                    buy_signal = True
                    buy_price = current_price
                    break
                else:
                    # Price is still below the 5% drop level
                    break

        elif current_price >= last_sell_price * (1 - 0.055) and current_price < last_sell_price * (1 - 0.05):
            print(f"{Fore.GREEN}Buy Signal Triggered: Price reached 5.5% drop level: ${current_price:.6f}{Style.RESET_ALL}")
            buy_signal = True
            buy_price = current_price

        elif current_price >= last_sell_price * (1 - 0.065):
            print(f"{Fore.YELLOW}Price reached 6.5% drop level: ${  current_price:.6f}{Style.RESET_ALL}")
            initial_high = current_price
            while True:
                current_price = get_price(symbol)
                if current_price < last_sell_price * (1 - 0.065):
                    print(f"{Fore.GREEN}Buy Signal Triggered: Price dropped below 6.5% drop level: ${  current_price:.6f}{Style.RESET_ALL}")
                    buy_signal = True
                    buy_price = current_price
                    break
                elif current_price <= initial_high * (1 - 0.01):
                    print(f"{Fore.GREEN}Buy Signal Triggered: Price dropped by more than 1% from its initial high: ${ current_price:.6f}{Style.RESET_ALL}")
                    buy_signal = True
                    buy_price = current_price
                    break
                elif current_price >= last_sell_price * (1 - 0.065):
                    # Price remains at or above 6.5% drop level
                    print(f"{Fore.GREEN}The price dropped to 6.5%: ${current_price:.6f}{Style.RESET_ALL}")
                    continue
                break

    # Sell Conditions
    if last_buy_price is not None:
        # Condition for selling based on price rise and drop
        if current_price >= last_buy_price * (1 + 0.05):
            print(f"{Fore.YELLOW}Price reached 5% rise level: ${ current_price:.6f}{Style.RESET_ALL}")
            while True:
                current_price = get_price(symbol)
                if current_price > last_buy_price * (1 + 0.05):
                    # Price is still above the 5% rise level
                    continue
                elif current_price <= last_buy_price * (1 + 0.05 - 0.005):
                    # Price dropped to just below 5% rise level
                    print(f"{Fore.RED}Sell Signal Triggered: Price dropped to ${current_price:.6f} below 5% rise level{Style.RESET_ALL}")
                    sell_signal = True
                    sell_price = current_price
                    break
                else:
                    # Price is still above the 5% rise level
                    break

        elif current_price >= last_buy_price * (1 + 0.055) and current_price < last_buy_price * (1 + 0.06):
            print(f"{Fore.RED}Sell Signal Triggered: Price reached 5.5% rise level: ${current_price:.6f}{Style.RESET_ALL}")
            sell_signal = True
            sell_price = current_price

        elif current_price >= last_buy_price * (1 + 0.06):
            print(f"{Fore.YELLOW}Price reached 6% rise level: ${  current_price:.6f}{Style.RESET_ALL}")
            initial_high = current_price
            while True:
                current_price = get_price(symbol)
                if current_price < last_buy_price * (1 + 0.06):
                    print(f"{Fore.RED}Sell Signal Triggered: Price dropped below 6% rise level: ${current_price:.6f}{Style.RESET_ALL}")
                    sell_signal = True
                    sell_price = current_price
                    break
                elif current_price >= initial_high * (1 + 0.01):
                    print(f"{Fore.RED}Sell Signal Triggered: Price rose by more than 1% from its initial high: ${ current_price:.6f}{Style.RESET_ALL}")
                    sell_signal = True
                    sell_price = current_price
                    break
                elif current_price >= last_buy_price * (1 + 0.065):
                    # Price remains at or above 6.5% rise level
                    continue
                break

    # Execute buy or sell
    if buy_signal:
        try:
            buy(symbol, quantity)
            print(f"{Fore.GREEN}Buy order executed at ${ buy_price:.6f}{Style.RESET_ALL}")
            last_sell_price = buy_price  # Update last_sell_price after buy
        except BinanceAPIException as e:
            print(f"{Fore.RED}Buy order failed: {e.message}{Style.RESET_ALL}")
    if sell_signal:
        try:
            sell(symbol, quantity)
            print(f"{Fore.RED}Sell order executed at ${ sell_price:.6f}{Style.RESET_ALL}")
            last_buy_price = sell_price  # Update last_buy_price after sell
        except BinanceAPIException as e:
            print(f"{Fore.RED}Sell order failed: {e.message}{Style.RESET_ALL}")

    return buy_signal, sell_signal, buy_price, sell_price


def buy(symbol, quantity, condition):
    """Place a market buy order."""
    order = client.order_market_buy(symbol=symbol, quantity=quantity)
    buy_price = float(order['fills'][0]['price'])
    buy_amount_coin = float(order['executedQty'])
    buy_amount_usdt = buy_price * buy_amount_coin
    wallet_usdt = get_asset_balance('USDT')
    wallet_coin = get_asset_balance(symbol[:-4])

    log_transaction("BUY", symbol, buy_price, buy_amount_usdt,
                    buy_amount_coin, wallet_usdt, wallet_coin, condition)
    print(f"{Fore.GREEN}Buy order placed for {quantity} {symbol}{Style.RESET_ALL}")


def sell(symbol, quantity, condition):
    """Place a market sell order."""
    order = client.order_market_sell(symbol=symbol, quantity=quantity)
    sell_price = float(order['fills'][0]['price'])
    sell_amount_coin = float(order['executedQty'])
    sell_amount_usdt = sell_price * sell_amount_coin
    wallet_usdt = get_asset_balance('USDT')
    wallet_coin = get_asset_balance(symbol[:-4])

    log_transaction("SELL", symbol, sell_price, sell_amount_usdt,
                    sell_amount_coin, wallet_usdt, wallet_coin, condition)
    print(f"{Fore.RED}Sell order placed for { quantity} {symbol}{Style.RESET_ALL}")


if __name__ == "__main__":

    while True:
        wallet_balance = get_asset_balance('USDT')
        asset_price = get_price(symbol)
        asset_balance = get_asset_balance(symbol[:-4])

        asset_value_in_usdt = asset_balance * \
            asset_price if asset_price is not None else 0
        buy_price = get_last_order(symbol, 'buy')
        profit_loss = calculate_profit_or_loss(
            buy_price, asset_price, asset_balance) if buy_price else None

        print(f"\n{Fore.CYAN}Current wallet balance: ${ wallet_balance:.6f}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Current market price of { symbol}: ${asset_price:.6f}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total value of {symbol} in USDT: ${ asset_value_in_usdt:.6f}{Style.RESET_ALL}")
        if profit_loss is not None:
            if profit_loss >= 0:
                print(f"{Fore.GREEN}Profit: {profit_loss:.6f}%{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Loss: {profit_loss:.6f}%{Style.RESET_ALL}")

        buy_signal, sell_signal, buy_price, sell_price = trading_logic(
            symbol, quantity)
        if buy_signal:
            print(f"{Fore.GREEN}Buy signal detected at price: { buy_price:.6f}{Style.RESET_ALL}")
        if sell_signal:
            print(f"{Fore.RED}Sell signal detected at price: {sell_price:.6f}{Style.RESET_ALL}")

        time.sleep(2)  # Sleep for 60 seconds before checking again
