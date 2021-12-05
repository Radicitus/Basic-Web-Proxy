import select
import socket
import sys


# Take Host IP and Port # from cli arguments
if len(sys.argv) != 3:
    raise Exception("ERROR! Usage: script, IP addr, Port #")
cli_args = sys.argv

# Create srv socket
host, port = str(cli_args[1]), int(cli_args[2])
srv_addr = (host, port)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setblocking(0)
srv.bind(srv_addr)
srv.listen(2)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


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
                data = s.recv(1024)
                if data:
                    #TODO: Add request functionality
                    try:
                        first = data.split('\n')[0]
                        url = first.split('')[1]
                        http_idx = url.find("://")
                        if http_idx == -1:
                            sub = url
                        else:
                            sub = url[(http_idx+3):]
                        port_idx = sub.find(":")
                        ext_srv_idx = sub.find("/")
                        if ext_srv_idx == -1:
                            ext_srv_idx = len(sub)
                        ext_srv = ""
                        ext_srv_port = -1
                        if port_idx == -1 or ext_srv_idx < port_idx:
                            port = 80
                            ext_srv = sub[:ext_srv_idx]
                        else:
                            port = int((sub[(port_idx+1):])[:ext_srv_idx - port_idx - 1])
                            ext_srv = sub[:port_idx]
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