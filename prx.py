import select
import socket
import sys


def process_base_url(base):
    port_idx = base.find(":")
    url_res_idx = base.find("/")

    if url_res_idx == -1:
        url_res_idx = len(base)

    if port_idx == -1 or url_res_idx < port_idx:
        url_port = 80
        url = base[:url_res_idx]
    else:
        url_port = int((base[(port_idx + 1):])[:url_res_idx - port_idx - 1])
        url = base[:port_idx]
    return [url, url_port]


def proxy(url, port, conn, data):
    print("Proxy Initiated... ")
    print("URL: ", url, " Port: ", port, " Data: ", data)
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
print("---------------------------------------------")

# Client vars
connections = [srv]
request_counter = 0
redirect = False
redirect_url = ""
mobile = False

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
                            base_url = req_url[(http_idx + 3):]

                        # Checks for special features
                        start_redir_feat = base_url.find("start_redirect")
                        stop_redir_feat = base_url.find("stop_redirect")
                        start_mobile_feat = base_url.find("start_mobile")
                        stop_mobile_feat = base_url.find("stop_mobile")
                        if start_redir_feat != -1:
                            redirect = True
                            redirect_url = base_url[start_redir_feat + 15:]
                        if stop_redir_feat != -1:
                            redirect_url = False
                        if start_mobile_feat != -1:
                            mobile = True
                        if stop_mobile_feat != -1:
                            mobile = False

                        # # Check redirect
                        # if redirect:
                        #     old_base_url = base_url
                        #     old_url = process_base_url(base_url)[0]
                        #     base_url = redirect_url
                        #     data = data.replace(old_base_url, base_url)
                        #     data = data.replace(old_url, base_url)

                        # Check mobile
                        if mobile:
                            user_agent_start = data.find("User-Agent:") + 12
                            user_agent_end = data.find("\r\n", user_agent_start) + 1
                            data = data.replace(data[user_agent_start:user_agent_end],
                                                'Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) '
                                                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 '
                                                'Mobile Safari/537.36\r')
                            data = data.replace(base_url, process_base_url(base_url)[0] + '/')

                        # Check if persistent connection
                        if data.find("Connection:"):
                            conn_header_start = data.find("Connection:")
                            conn_header_end = data.find("\r\n", conn_header_start) + 2
                            data = data.replace(data[conn_header_start: conn_header_end], "")
                        if data.find("Keep-Alive:"):
                            ka_header_start = data.find("Keep-Alive:")
                            ka_header_end = data.find("\r\n", ka_header_start) + 2
                            data = data.replace(data[ka_header_start: ka_header_end], "")

                        proxy(process_base_url(base_url)[0], process_base_url(base_url)[1], s, data.encode())
                    except Exception as e:
                        print(e)
                        pass
                else:

                    # Remove the disconnected client
                    connections.remove(s)

                    # Close the socket
                    s.close()
    except KeyboardInterrupt:
        print("\nexit")
        srv.close()
        sys.exit()
