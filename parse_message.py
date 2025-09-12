from datetime import datetime
import re

DEFAULT_ACCOUNT_ID = 1

UPI_REGEXP_TYPE = re.compile(r"\b(credited|debited)\b")
UPI_REGEXP_AMOUNT = re.compile(r"Rs\.?\s?([\d,]+\.\d{2})")
UPI_REGEXP_RECEIVER = re.compile(r"VPA\s+(\S+)\b")
UPI_REGEXP_DATE = re.compile(r"on\s+(\d{2}-\d{2}-\d{2})")

DEBIT_CARD_REGEXP_AMOUNT = re.compile(r"Rs\.?\s?([\d,]+\.\d{2})")
DEBIT_CARD_REGEXP_RECEIVER = re.compile(r'at\s+([A-Z\s]+?)\s+on\s+')
DEBIT_CARD_REGEXP_DATE = re.compile(r"on\s+(\d{2}-\d{2}-\d{2})")

def parse_message(message: str):
    if 'VPA' in message:
        return parse_upi_message(message)
    elif 'Debit Card' in message:
        return parse_debit_card_message(message)
    else:
        return None

def parse_upi_message(message: str):
    tx_type = UPI_REGEXP_TYPE.search(message).group(1)
    amount = UPI_REGEXP_AMOUNT.search(message).group(1)
    receiver = UPI_REGEXP_RECEIVER.search(message).group(1)
    date = UPI_REGEXP_DATE.search(message).group(1)
    return {
        "type": 'income' if tx_type == 'credited' else 'expense',
        "amount": float(amount),
        "date": datetime.strptime(date, "%d-%m-%y"),
        "category": "Uncategorized",
        "title": tx_type == 'credited' and f'Payment from {receiver}' or f'Payment to {receiver}',
        "account_id": DEFAULT_ACCOUNT_ID,
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
        "amount": float(amount),
        "date": datetime.strptime(date, "%d-%m-%y"),
        "category": "Uncategorized",
        "title": f'Payment to {receiver}',
        "account_id": DEFAULT_ACCOUNT_ID,
        "tags": [],
        "receiver": receiver,
        "sender": None
    }

if __name__ == "__main__":
    print(parse_message("HDFC BANK Dear Card Holder, Thank you for using your HDFC Bank Debit Card ending 5339 for ATM withdrawal for Rs 500.00 in PUNE at VIT BRANCH on 16-05-2024 15:00:34. After the above transaction, the total available balance on your card is Rs 88686.37. For more details on this transaction please visit Netbanking-Login here - Accounts. Not you? Please sms BLOCK DEBIT CARD 5339 to 7308080808 to block the card immediately or call on 18002586161 to report this transaction. Regards HDFC Bank (This is a system generated mail and should not be replied to) For more details on Service charges and Fees, click here. \u00a9 HDFC Bank"))