import math
import sys
import random
from multiprocessing import Process, Queue

# extended euclidean algorithm - used to find modular inverse
def egcd(a, n):
    if a == 0:
        return (n, 0, 1)
    else:
        g, y, x = egcd(n%a, a)
        return (g, x - (n//a)*y, y)

# Use egcd to find modular inverse
def ModInverse(a, n):
    g, x, _ = egcd(a, n) 
    if g == 1:
        return x % n
    else:
        raise ArithmeticError("{} is not invertible modulo {}.".format(a, n))

def MontgomeryProduct(a, b, n, nPrime, r):
    t = a * b
    m = t * nPrime % r
    u = (t + m*n)/r

    if u >= n:
        return (u-n, True)
    else:
        return (u, False)

def rsa(a, d, n, nPrime, r):
    aa = (a*r)%n
    xx = (1*r)%n
    k = len(d)
    sub = 0
    for i in range(0, k):
        sub = False
        xx, _ = MontgomeryProduct(xx, xx, n, nPrime, r)
        if d[i] == '1':
            xx, sub_measure = MontgomeryProduct(aa, xx, n, nPrime, r)
        sub += int(sub_measure)
    x, _ = MontgomeryProduct(xx, 1, n, nPrime, r)
    return x, sub 

def rsa_guess(a, d, n, nPrime, r, bit):
    aa = (a*r)%n
    xx = (1*r)%n
    d_guessed = d[:bit]
    d_guessed += '1'
    #Used sub to record whther reduction occured
    sub = False
    for i in range(0, len(d_guessed)):
        xx, _ = MontgomeryProduct(xx, xx, n, nPrime, r)
        if d_guessed[i] == '1':
            xx, sub = MontgomeryProduct(aa, xx, n, nPrime, r)
    res, _ = MontgomeryProduct(xx, 1, n, nPrime, r)
    return res, sub

def guess(right_queue, wrong_queue, input_data, d, n, nPrime, r, bit):
    red = []
    nored = []
    for m in input_data:
        _, sub = rsa_guess(m[0], d, n, nPrime, r, bit)
        if sub:
            red += [m]
        else:
            nored += [m]
    right_queue.put(red)
    wrong_queue.put(nored)

def split_messages(data, d, n, nPrime, r, bit):
    input_data = data
    right_queue = Queue()
    wrong_queue = Queue()
    processes = []
    step = len(input_data) // 8
    total_num = 0
    for i in range(0, len(input_data), step):
        p = Process(target=guess, args=(right_queue, wrong_queue, input_data[i:i+step], d, n, nPrime, r, bit))
        total_num += 1
        p.start()
        processes += [p]

    red = []
    nored = []
    for i in range(total_num):
        red += right_queue.get()
        nored += wrong_queue.get()

    while processes:
        processes.pop().join()
    return (red, nored)

def n_Prime(n):
    k = math.floor(math.log(int(n), 2)) + 1
    r = int(math.pow(2,k))
    rInverse = ModInverse(r,n)
    nPrime = (r * rInverse - 1)//n 
    return (r, nPrime)

def check(data, key_guessed, n, n_prime, r):
    testMessage1, c = rsa(data[0][0], key_guessed, n, n_prime, r)
    testMessage2, c = rsa(data[1][0], key_guessed, n, n_prime, r)
    if (testMessage1 == data[0][1] and testMessage2 == data[1][1]):
        return True
    else:
        return False

def RSATimingAttack(n, data, maxbitlen):
    delta = 2300000
    (r, n_prime) = n_Prime(n)
    win = False
    average = lambda x: sum(x) / len(x)
    while not win:
        key_guessed = '1'
        bit = 1
        diff_lst = []
        for i in range(maxbitlen):
            (red, nored) = split_messages(data, key_guessed, n, n_prime, r, bit)    
            redavg_1 = map(average, zip(*red))[2]
            noredavg_1 = map(average, zip(*nored))[2]
            total_avg =  map(average, zip(*data))[2]
            diff = abs(redavg_1-noredavg_1)
            diff_lst += [diff]
            print("Delta: {}".format(delta))
            print("Difference of guessing 1:" + str(diff))
            #print(redavg_1)
            #print(noredavg_1)
            #print(total_avg)

            if diff > delta:
                key_guessed += '1'
                print("Guessing next bit is 1.")
            else:
                key_guessed += '0'
                print("Guessing next bit is 0.")
            
            print("Derived key: {}\n".format(key_guessed))

            if(check(data, key_guessed, n, n_prime, r)):
                print("KEY FOUND: {}\n".format(key_guessed))
                win = True
                break
            bit += 1
        if(win != True):
            delta = average(diff_lst) - random.randint(-100000, 100000)
            #delta = average(diff_lst) + 100000


if __name__ == "__main__":
    path = sys.argv[1]
    maxbitlen = int(sys.argv[2])
    data = []
    f = open(path + '/data.csv', 'rb')
    _ = f.readline()
    n, e = map(int, f.readline().split(','))
    _ = f.readline()

    data = [[int(x) for x in line.split(',')] for line in f]
    
    RSATimingAttack(n, data, maxbitlen)