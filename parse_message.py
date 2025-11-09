from datetime import datetime
import re

from auto_categorize import try_auto_categorize_chase

HDFC_ACCOUNT_ID = 1
HDFC_FOREX_ACCOUNT_ID = 2
CHASE_ACCOUNT_ID = 3

UPI_REGEXP_TYPE = re.compile(r"\b(credited|debited)\b")
UPI_REGEXP_AMOUNT = re.compile(r"Rs\.?\s?([\d,]+\.\d{2})")
UPI_REGEXP_RECEIVER = re.compile(r"VPA\s+(\S+)\b")
UPI_REGEXP_DATE = re.compile(r"on\s+(\d{2}-\d{2}-\d{2})")

DEBIT_CARD_REGEXP_AMOUNT = re.compile(r"Rs\.?\s?([\d,]+\.\d{2})")
DEBIT_CARD_REGEXP_RECEIVER = re.compile(r'at\s+([A-Z\s]+?)\s+on\s+')
DEBIT_CARD_REGEXP_DATE = re.compile(r"on\s+(\d{2}-\d{2}-\d{2})")

FOREX_CARD_REGEXP_AMOUNT = re.compile(r"USD\s+([\d,]+(?:\.\d{0,2})?)")
FOREX_CARD_REGEXP_RECEIVER = re.compile(r'\bat\s+(.+?)\s+on\s+')
FOREX_CARD_REGEXP_DATE = re.compile(r"\bon\s+(\d{2}-\d{2}-\d{4})")

CHASE_REGEXP_AMOUNT = re.compile(r"\$([\d,]+\.\d{2})")
CHASE_REGEXP_RECEIVER = re.compile(r'with\s+([A-Z\s\d\*\-\.\&\#]+?)\s+Account\s+ending\s+in')
CHASE_REGEXP_DATE = re.compile(r"Made\s+on\s+(\w{3}\s+\d{1,2},?\s+\d{4})")

def parse_message(message: str):
    if 'VPA' in message:
        return parse_upi_message(message)
    elif 'ISIC Forex' in message and 'used for making a payment' in message:
        return forex_message(message)
    elif 'chase.com' and 'Transaction alert' in message:
        return chase_message(message)
    else:
        return None

def parse_upi_message(message: str):
    tx_type = UPI_REGEXP_TYPE.search(message).group(1)
    amount = UPI_REGEXP_AMOUNT.search(message).group(1)
    receiver = UPI_REGEXP_RECEIVER.search(message).group(1)
    date = UPI_REGEXP_DATE.search(message).group(1)

    return {
        "type": 'income' if tx_type == 'credited' else 'expense',
        "amount": float(amount) * 100,
        "date": datetime.strptime(date, "%d-%m-%y"),
        "category": "Uncategorized",
        "title": tx_type == 'credited' and f'Payment from {receiver}' or f'Payment to {receiver}',
        "account_id": HDFC_ACCOUNT_ID,
        "tags": [],
        "receiver": receiver if tx_type == 'debited' else None,
        "sender": receiver if tx_type == 'credited' else None
    }

def parse_debit_card_message(message: str):
    tx_type = 'expense'
    amount = DEBIT_CARD_REGEXP_AMOUNT.search(message).group(1)
    receiver = DEBIT_CARD_REGEXP_RECEIVER.search(message).group(1)
    date = DEBIT_CARD_REGEXP_DATE.search(message).group(1)

    return {
        "type": tx_type,
        "amount": float(amount) * 100,
        "date": datetime.strptime(date, "%d-%m-%y"),
        "category": "Uncategorized",
        "title": f'Payment to {receiver}',
        "account_id": HDFC_ACCOUNT_ID,
        "tags": [],
        "receiver": receiver,
        "sender": None
    }

def forex_message(message: str):
    tx_type = 'expense'
    amount = FOREX_CARD_REGEXP_AMOUNT.search(message).group(1)
    receiver = FOREX_CARD_REGEXP_RECEIVER.search(message).group(1)
    date = FOREX_CARD_REGEXP_DATE.search(message).group(1)

    return {
        "type": tx_type,
        "amount": float(amount) * 100,
        "date": datetime.strptime(date, "%d-%m-%Y"),
        "category": "Uncategorized",
        "title": f'Payment to {receiver}',
        "account_id": HDFC_FOREX_ACCOUNT_ID,
        "tags": [],
        "receiver": receiver,
        "sender": None
    }

def chase_message(message: str):
    tx_type = 'expense'
    amount = CHASE_REGEXP_AMOUNT.search(message).group(1)
    receiver = CHASE_REGEXP_RECEIVER.search(message).group(1)
    date = CHASE_REGEXP_DATE.search(message).group(1)

    auto_categorize = try_auto_categorize_chase(receiver, f'Payment to {receiver}')

    return {
        "type": tx_type,
        "amount": float(amount) * 100,
        "date": datetime.strptime(date, "%b %d, %Y"),
        "category": auto_categorize['category'],
        "title": auto_categorize['title'],
        "account_id": CHASE_ACCOUNT_ID,
        "tags": [],
        "receiver": receiver,
        "sender": None
    }
