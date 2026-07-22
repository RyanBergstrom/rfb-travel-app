import re

CHF_TO_USD = 1.12
EUR_TO_USD = 1.14

def chf_to_usd(chf):
    return round(float(chf) * CHF_TO_USD, 2)

def eur_to_usd(eur):
    return round(float(eur) * EUR_TO_USD, 2)

def parse_quantity(qty_str):
    if not qty_str:
        return None, None
    qty_str = qty_str.strip()
    match = re.match(r'^([\d.]+)?\s*([a-zA-Z]+)$', qty_str)
    if match:
        amount = match.group(1)
        unit = match.group(2)
        if amount:
            return float(amount), unit.lower()
        return None, unit.lower()
    return None, qty_str

def metric_to_us(amount, unit):
    conversions = {
        'g': ('oz', 0.03527396),
        'kg': ('lb', 2.20462),
        'ml': ('fl oz', 0.033814),
        'l': ('qt', 1.05669),
        'pce': ('piece', 1),
        'bd': ('bunch', 1),
    }
    unit = unit.lower()
    if unit in conversions:
        us_unit, factor = conversions[unit]
        us_amount = round(amount * factor, 2)
        return us_amount, us_unit
    return amount, unit

def format_us_value(amount, unit):
    if unit == 'lb' and amount >= 1:
        return f"{amount} lb"
    elif unit == 'lb' and amount < 1:
        return f"{round(amount * 16, 1)} oz"
    elif unit == 'oz' and amount >= 16:
        return f"{round(amount / 16, 2)} lb"
    elif unit == 'qt' and amount >= 4:
        return f"{round(amount / 4, 2)} gal"
    return f"{amount} {unit}"

def convert_product(p):
    result = dict(p)
    if p.get('price_eur') is not None:
        price_usd = eur_to_usd(p['price_eur'])
        result['price_usd'] = price_usd
    else:
        price_usd = chf_to_usd(p['price_chf'])
        result['price_usd'] = price_usd

    result['name_display'] = p.get('name_en') or p.get('name', '')
    result['category_display'] = p.get('category_en') or p.get('category', '')

    if p.get('quantity'):
        amt, unit = parse_quantity(p['quantity'])
        if amt and unit:
            us_amt, us_unit = metric_to_us(amt, unit)
            result['quantity_us'] = format_us_value(us_amt, us_unit)
        else:
            result['quantity_us'] = p['quantity']
    else:
        result['quantity_us'] = None

    if p.get('per_unit') and p.get('price_per_unit_chf'):
        amt, unit = parse_quantity(p['per_unit'])
        if amt and unit:
            us_amt, us_unit = metric_to_us(amt, unit)
            result['per_unit_us'] = format_us_value(us_amt, us_unit)
        else:
            result['per_unit_us'] = p['per_unit']
        ppu = chf_to_usd(p['price_per_unit_chf'])
        result['price_per_unit_usd'] = ppu
    elif p.get('per_unit') and p.get('price_per_unit_eur'):
        amt, unit = parse_quantity(p['per_unit'])
        if amt and unit:
            us_amt, us_unit = metric_to_us(amt, unit)
            result['per_unit_us'] = format_us_value(us_amt, us_unit)
        else:
            result['per_unit_us'] = p['per_unit']
        ppu = eur_to_usd(p['price_per_unit_eur'])
        result['price_per_unit_usd'] = ppu
    else:
        result['per_unit_us'] = None
        result['price_per_unit_usd'] = None

    return result
