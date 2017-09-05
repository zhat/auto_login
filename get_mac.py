import uuid

def get_mac_address():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

if __name__=='__main__':
    mac=get_mac_address()
    print(mac)
    input("按任意键结束")