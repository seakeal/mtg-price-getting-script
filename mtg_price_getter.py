# MTG Price Getter
# Nicholas Gill
# Uses Scryfall's API

import csv
from datetime import datetime
import json
import requests
import time
import urllib

# FUNCTION DEFS
## Gets API for specific card
def getCard(card, set_code):
    apistring = api + '/cards/named?exact=' + urllib.quote_plus(card.strip()) + '&set=' + set_code

    response = requests.get(apistring)
    time.sleep(0.1)

    card_details = response.json()
    #print(json.dumps(card_details, indent=2))
    return card_details

## Gets API for sets and codes
def getSets():
    apistring = api + '/sets'
    mtg_sets = {}

    response = requests.get(apistring)
    time.sleep(0.1)

    r = response.json()
    for set_data in r['data']:
        mtg_sets[set_data["name"].upper()] = set_data["code"]

    return mtg_sets

# BEGIN
api = 'https://api.scryfall.com'
mtgfile = 'spreadsheets/mtg_sell_list.csv'
card_dict = {}
cards_without_price_info = []
cwpi_filename = 'cards_without_price_info.txt'
num_cards = 0
num_processed = 0
completion_flags = [0,0,0]
total_price = 0.0
total_price_over_2 = 0.0
total_price_foils = 0.0

# Get list of set codes
print('Getting set codes...')
mtg_sets = getSets()
print('Set code list built')

# Get cards from CSV and build card dict
print('Building card dict...')
with open(mtgfile, 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        card_dict[row[0]] = {
            'set': row[1],
            'set_code': mtg_sets[row[1].upper()],
            'quantity': 1,
            'foil': 'N',
            'price': 0.0,
        }
        if row[2]: card_dict[row[0]]['quantity'] = row[2]
        if row[3]: card_dict[row[0]]['foil'] = 'Y'
        
        num_cards += 1

print('Card dict complete. Analyzing {} cards'.format(num_cards))

#print(json.dumps(card_dict, indent=2))

# Get price data for each card
print('0% complete')
for c in card_dict.items():
    name = c[0]
    details = c[1]

    card_info = getCard(name, details['set_code'])
    
    if 'prices' not in card_info:
        print('WARNING: card {} does not have price info'.format(name))
        cards_without_price_info.append((name, details['set']))
        continue

    if details['foil'] == 'Y':
        card_dict[name]['price'] = float(card_info['prices']['usd_foil'])
    else:
        card_dict[name]['price'] = float(card_info['prices']['usd'])

    price_to_add = card_dict[name]['price'] * float(card_dict[name]['quantity'])

    total_price += price_to_add
    if card_dict[name]['price'] >= 2.0:
        total_price_over_2 += price_to_add
    if card_dict[name]['foil'] == 'Y':
        total_price_foils += price_to_add

    #print(json.dumps(card_dict[name], indent=2))

    num_processed += 1
    if num_processed > num_cards/4 and not completion_flags[0]:
        print('25% complete')
        completion_flags[0] = 1
    elif num_processed > num_cards/2 and not completion_flags[1]:
        print('50% complete')
        completion_flags[1] = 1
    elif num_processed > (num_cards/2 + num_cards/4) and not completion_flags[2]:
        print('75% complete')
        completion_flags[2] = 1

print('100% complete') 

# Write to file all cards that do not have price info
if len(cards_without_price_info):
    print('Writing to cards_without_price_info.txt...')
    with open(cwpi_filename, 'w') as f:
        f.write('File written at: {}\n'.format(datetime.now()))
        for c in cards_without_price_info:
            f.write('{} ++ {}\n'.format(c[0], c[1]))

# Final output
print('')
print('Total price: ${:.2f}'.format(total_price))
print('Total price of cards over $2: ${:.2f}'.format(total_price_over_2))
print('Total price of foils: ${:.2f}'.format(total_price_foils))

# END