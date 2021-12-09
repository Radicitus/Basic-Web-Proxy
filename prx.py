import select
import socket
import sys


def proxy(url, port, conn, data):
    print("Proxy Initiated... ")
    print("URL: ", url,  " Port: ", port, " Data: ", data)
    prx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    prx.settimeout(100)
    try:
        prx.connect((url, port))
        prx.send(data)

        while 1:
            try:
                reply = prx.recv(1024)
                print(" REPLY PART: ", reply)
                if len(reply) > 0:
                    conn.send(reply)
                else:
                    break
            except Exception as tm:
                print(tm)
                break
        prx.close()

    except Exception as prx_error:
        print(prx_error)
        prx.close()
        sys.exit()
    print("Proxy Task Completed!")

# Take Host IP and Port # from cli arguments
if len(sys.argv) != 2:
    raise Exception("ERROR! Usage: script, Port #")
cli_args = sys.argv

# Create srv socket
host, port = '127.0.0.1', int(cli_args[1])
srv_addr = (host, port)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.setblocking(0)
srv.bind(srv_addr)
srv.listen(1)

print("Starting proxy server on port " + str(port))

# Client vars
connections = [srv]
request_counter = 0

while True:
    try:
        sr, sw, se = select.select(connections, [], [])
        for s in sr:
            if s is srv:
                # Accept client connection
                connection, address = s.accept()
                connections.append(connection)
            else:
                raw_data = s.recv(1024)
                data = raw_data.decode(encoding='utf-8', errors='ignore')
                if data:
                    try:
                        req_url_header = data.split('\n')[0]
                        if req_url_header.split(' ')[0] != 'GET':
                            continue
                        req_url = req_url_header.split(' ')[1]
                        http_idx = req_url.find("://")

                        if http_idx == -1:
                            base_url = req_url
                        else:
                            base_url = req_url[(http_idx+3):]

                        port_idx = base_url.find(":")
                        url_res_idx = base_url.find("/")

                        if url_res_idx == -1:
                            url_res_idx = len(base_url)
                        url = ""
                        url_port = -1

                        if port_idx == -1 or url_res_idx < port_idx:
                            url_port = 80
                            url = base_url[:url_res_idx]
                        else:
                            url_port = int((base_url[(port_idx+1):])[:url_res_idx - port_idx - 1])
                            url = base_url[:port_idx]

                        proxy(url, url_port, s, raw_data)
                    except Exception as e:
                        print(e)
                        pass
                else:

                    # Remove the disconnected client
                    connections.remove(s)

                    # Log client disconnect
                    print("[CLI disconnected]")

                    # Close the socket
                    s.close()
    except KeyboardInterrupt:
        print("\nexit")
        srv.close()
        sys.exit()


