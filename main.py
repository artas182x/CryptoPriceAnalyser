import csv
from datetime import datetime
from dataclasses import dataclass
import math
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.ticker import FormatStrFormatter


@dataclass
class HistoryPoint:
    date: datetime
    price: float
    macd: float
    signal: float


@dataclass
class Wallet:
    budget = 0.0
    units = 1000.0


@dataclass
class SimulationAction:
    type: str
    price: float
    units: float


def main():

    usingHMA = True
    history = []

    with open('LTCPrice.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        #for row in csv_reader:
        #    history.append(HistoryPoint(datetime.strptime(row[0], "%d.%m.%Y"), float(row[1]), 0, 0))

        for row in csv_reader:
            history.append(HistoryPoint(datetime.strptime(row[0], "%Y-%m-%d"), float(row[2]), 0, 0))

    #history = history[938:]
    history = calculateMACD_Signal(history, usingHMA)
    generateCharts(history)

    wallet = Wallet()

    simulation(history, wallet, usingHMA)

def calculateEMA(history, actualindex, n):

    alpha = 1-(2/(n-1))

    nominator = float(0.0)
    denominator = float(0.0)

    for i in range(n+1):
        if actualindex - i > 0:
            nominator += history[actualindex-i-1] * pow(alpha, i)
        else:
            nominator += pow(alpha, i)*history[0]

        denominator += pow(alpha, i)

    return nominator / denominator

#def calculateWMA(history, n):
#
#    array = [0.0] * (n-1)
#
#    for i in range(history.__len__()-n+1):
#        sum = float(0.0)
#        for j in range(n):
#            sum += history[i+j]*(n-j)
#        array.append(sum / ((n*(n+1)) / 2))

#    return array


def calculateHMA(history,n):
    period = int(math.sqrt(n))

    wma1 = []
    wma2 = []
    for i in range(len(history)):
        wma1.append(calculateEMA(history, i, int(n/2)))
        wma2.append(calculateEMA(history, i, n))


  #  wma1 = calculateWMA(history, int(n/2))
   # wma2 = calculateWMA(history, n)

    for el in range(wma2.__len__()):
        wma1[el] = 2*wma1[el]-wma2[el]

    wma3 = []
    for i in range(len(history)):
        wma3.append(calculateEMA(wma1, i, period))

    return wma3
   # return calculateWMA(wma1, period)


def calculateMACD_Signal(history, hma):
    price = [l.price for l in history]

    if hma==True:
        macd = calculateHMA(price, 12)
        macd2 = calculateHMA(price, 26)

        for el in range(len(history)):
            macd[el] = macd[el] - macd2[el]

        signal = calculateHMA(macd, 9)

        for i in range(len(history)):
            history[i].signal = signal[i]
            history[i].macd = macd[i]
    else:

         for i in range(len(history)):
            history[i].macd = calculateEMA(price, i+1, 12) - calculateEMA(price, i, 26)

         macd = [l.macd for l in history]
         for i in range(len(history)):
            history[i].signal = calculateEMA(macd, i+1, 9)

    return history


def generateCharts(history):
    price = [l.price for l in history]
    days = [l.date for l in history]
    plt.rcParams.update({'figure.autolayout': True})
    #plt.rcParams["figure.figsize"] = [11, 9]

    plt.plot(days,price)
    plt.xticks(rotation=45)

    plt.xlabel("Days")
    plt.ylabel("Price (USD)")
    plt.tight_layout()

    plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%d USD'))
    plt.title("Price of LiteCoin from last %d days" % history.__len__())
    plt.legend(loc='upper left')

    plt.savefig("price%d.svg" % history.__len__(), format="svg")

    plt.show()



    macd = [l.macd for l in history]
    signal = [l.signal for l in history]

    plt.plot(days, macd, color='green', label='Macd')
    plt.plot(days, signal, color='orange', label='Signal')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.xlabel("Days")
    plt.ylabel("MACD and Signal units")
    plt.legend(loc='upper left')

    plt.title("MACD and Signal pointers from last %d days" % history.__len__())
   # plt.text(days[-200], signal[-100]-20, 'MACD')
   # plt.text(days[-290], signal[-300], 'Signal')

    plt.savefig("macd%d.svg" % history.__len__(), format="svg")

    plt.show()






def simulation(history, wallet, hma):
    i = 5

    simulationhistory = []

    alltransactions = 0
    successfull = 0
    buyprice = 0
    sold = False

    compare = 0.1
    if hma:
        compare = 0.6

    while i < history.__len__():
        macdminussignal = history[i].macd-history[i].signal
        macdminussignal1 = history[i-1].macd - history[i-1].signal
        macdminussignal2 = history[i-2].macd - history[i-2].signal

        macdminussignal3 = history[i - 5].macd - history[i - 5].signal

        #if not hma:
         #   macdminussignal3 = macdminussignal1

        if macdminussignal > 0 > macdminussignal3 and macdminussignal-macdminussignal3 > compare:
            if wallet.budget > 0:
                tmp = int(wallet.budget / history[i].price)
                if tmp > 0:
                    wallet.budget -= tmp * history[i].price
                    wallet.units += tmp

                    simulationhistory.append(SimulationAction("BUY", history[i].price, tmp))

                    if not sold:
                        if buyprice > history[i].price:
                            buyprice = history[i].price
                    else:
                        buyprice = history[i].price
                    sold = 0
                    print("Bought %d LTC %s for %f USD" % (tmp, history[i].date.date().__str__(), history[i].price))

        elif macdminussignal < macdminussignal2 < macdminussignal3 and macdminussignal1-macdminussignal > compare:
            if wallet.units > 0:
                wallet.budget += wallet.units * history[i].price
                alltransactions += 1
                sold = 1
                simulationhistory.append(SimulationAction("SELL", history[i].price, wallet.units))
                if history[i].price > buyprice:
                    successfull += 1
                wallet.units = 0
                print("Sold %s LTC for %f USD" % (history[i].date.date().__str__(), history[i].price))
                print("We have %f USD" % wallet.budget)

        i += 1

    if sold:
        tmp = int(wallet.budget / history[i-1].price)
        if tmp > 0:
            wallet.budget -= tmp * history[i-1].price
            wallet.units += tmp

            simulationhistory.append(SimulationAction("BUY", history[i-1].price, tmp))

            if not sold:
                if buyprice > history[i-1].price:
                    buyprice = history[i-1].price
            else:
                buyprice = history[i-1].price
            sold = 0
            print("Bought %d LTC %s for %f USD" % (tmp, history[i-1].date.date().__str__(), history[i-1].price))

    print("We have: %d LTC" % wallet.units)
    print("Success rate: %f" % (successfull/alltransactions*100))
    print("All transactions: %d" % alltransactions)

    print("We had: %d USD" % (1000*history[0].price))
    print("We have: %f USD" % (wallet.units*history[history.__len__()-1].price))

    with open('LTCHistory.csv', encoding='utf-8', mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        csv_writer.writerow(['Type', 'Units', 'Price'])

        for i in range(len(simulationhistory)):
            csv_writer.writerow([simulationhistory[i].type, simulationhistory[i].units, simulationhistory[i].price])

    return wallet


if __name__ == "__main__":
    main()

