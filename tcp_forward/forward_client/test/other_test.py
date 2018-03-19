




if __name__ == '__main__':
    s = {1:1,2:2,3:3,4:4}

    for key,value in s.items():
        if value == 3:
            s.pop(key)
            print 'del item 3'
            continue
        else:
            print '****' + str(key)

    print s