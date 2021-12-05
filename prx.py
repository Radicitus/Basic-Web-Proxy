import select
import socket
import sys


# Take Host IP and Port # from cli arguments
if len(sys.argv) != 3:
    raise Exception("ERROR! Usage: script, IP addr, Port #")
cli_args = sys.argv
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

while True:
    try:
        sr, sw, se = select.select(connections, [], [])
        for s in sr:
            if s is srv:
                connection, address = s.accept()
                connections.append(connection)
            else:
                data = s.recv(1024)
                if data:
                    ip, port = s.getpeername()[0], s.getpeername()[1]
                    print("[" + str(ip) + ":" + str(port) + "] " + data.decode('ascii'))
                    for c in connections:
                        if c is not srv and c is not s:
                            ip, port = s.getpeername()[0], s.getpeername()[1]
                            message = "[" + str(ip) + ":" + str(port) + "] " + data.decode('ascii')
                            c.send(message.encode())
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