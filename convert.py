import csv
import sys
import os.path

from bs4 import BeautifulSoup
import pandas as pd

def parse(fname):
    print('Parsing ', fname)
    with open(fname, 'r') as f:
        page = f.read()
    soup = BeautifulSoup(page, 'html.parser')
    item_tables = soup.find_all('table', attrs={'class': ['delivered']})

    res = []
    for item_table in item_tables:
        rows = item_table.find_all('tr')

        metadata = rows[0]
        store = metadata.find('th', align='left').string.strip()
        num_items = int(metadata.find('th', align='right').div.string.strip())
        print('{}: {} items delivered from {}'.format(fname, num_items, store)) 
        
        category = None
        num_items_found = 0
        for row in  rows[1:]:
            kind = row.td.attrs.get('class', ['none'])
            assert len(kind) == 1
            kind = kind[0]
            if kind == 'section-head':
                category = row.td.string.strip()
            elif kind == 'order-item':
                num_items_found += 1
                order = row.td.find('div', attrs={'class': 'item-name'})
                name = order.contents[0].strip()
                price_quantity = order.find('small', attrs={'class': 'muted'}).string.strip()
                quantity, price = price_quantity.split('×')
                quantity = float(quantity.strip(' lb'))
                price = float(price.strip(' $'))
                out = {'name': name, 'quantity': quantity, 'price': price, 'category': category, 'store': store}
                res.append(out)
            elif kind == 'none':
                pass
            else:
                print('WARNING: unexpected row type "{}"'.format(kind))

        if num_items_found != num_items:
            print('WARNING: expected number of items did not match number of rows') 

    df = pd.DataFrame(res)
    df = df.reindex(columns=['name', 'price', 'quantity', 'category', 'store'])
    return df

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage: <output csv> <html receipt 1> [<html receipt 2> ...]')
        sys.exit(1)
    out_path = sys.argv[1]
    in_paths = sys.argv[2:]
    tables = []
    for fname in in_paths:
        table = parse(fname)
        table['source'] = os.path.basename(fname).split('.html')[0]
        tables.append(table)
    table = pd.concat(tables)
    table.to_csv(out_path, index=False)
