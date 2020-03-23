import time
import csv

def dump(name, articles):
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    filename = name + '_' + timestamp

    with open('dump/%s.csv' % filename, 'w', encoding='utf8', newline='') as fp:
        dict_writer = csv.DictWriter(fp, fieldnames=articles[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(articles)

        print('dumped to csv!')
