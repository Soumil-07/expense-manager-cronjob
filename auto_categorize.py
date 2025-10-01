def try_auto_categorize_chase(receiver: str, default_title: str):
    if 'lyft' in receiver.lower():
        return {
            'category': 'Lyft',
            'title': default_title
        }
    elif 'panda express' in receiver.lower():
        return {
            'category': 'Food',
            'title': 'Panda Express'
        }
    elif 'street corner' in receiver.lower():
        return {
                'category': 'Groceries',
                'title': 'Street Corner'
            }
    elif 'enterprise carshare' in receiver.lower():
        return {
            'category': 'Transport',
            'title': 'Enterprise Rental'
        }
    return {
        'category': 'Uncategorized',
        'title': default_title
    }
