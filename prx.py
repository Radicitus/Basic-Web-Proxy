import select
import socket
import sys


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
srv.listen(5)

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
                data = raw_data.decode('utf-8')
                if data:
                    #TODO: Add request functionality
                    try:
                        req_url_header = data.split('\n')[0]
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

                        print("Port: ", url_port, " URL: ", url)
                    except:
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

def proxy(url, port, conn, addr, data):
    return
