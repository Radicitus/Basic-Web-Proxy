import select
import socket
import sys


def log(num, red, mob, cli_ip, cli_prt, req_f_cli, ua_f_cli, dst_dmn,
        dst_prt, req_t_dst, ua_t_dst, stat_dst, mime_type, mime_size):
    line1 = str(num) + " [" + red + "] Redirection [" + mob + "] Mobile\n"
    line2 = "[CLI connected to " + str(cli_ip) + ":" + str(cli_prt) + "]\n"
    line3 = "[CLI ==> PRX --- SRV]\n"
    line4 = "> " + req_f_cli + "\n"
    line5 = "> " + ua_f_cli + "\n"
    line6 = "[SRV connected to " + dst_dmn + ":" + str(dst_prt) + "]\n"
    line7 = "[CLI --- PRX ==> SRV]\n"
    line8 = "> " + req_t_dst + "\n"
    line9 = "> " + ua_t_dst + "\n"
    line10 = "[CLI --- PRX <== SRV]\n"
    line11 = "> " + stat_dst + "\n"
    line12 = "> " + mime_type + " " + mime_size + "bytes\n"
    line13 = "[CLI <== PRX --- SRV]\n"
    line14 = "> " + stat_dst + "\n"
    line15 = "> " + mime_type + " " + mime_size + "bytes\n"
    line16 = "[CLI disconnected]\n"
    line17 = "[SRV disconnected]\n"
    line18 = "-------------------------------------------------------"
    print(line1 + line2 + line3 + line4 + line5 + line6 + line7 + line8 + line9 +
          line10 + line11 + line12 + line13 + line14 + line15 + line16 + line17 + line18)


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
    # print("Proxy Start: ", "URL: ", url, " Port: ", port, " Data: ", data)
    prx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    prx.settimeout(100)
    try:
        prx.connect((url, port))
        prx.send(data)

        first_reply = None
        while 1:
            try:
                reply = prx.recv(1024)
                # print(" REPLY PART: ", reply)
                if len(reply) > 0:
                    if not first_reply:
                        first_reply = reply
                    conn.send(reply)
                    chk_hdr = reply.decode(errors='ignore')
                    if chk_hdr.find("404") > 0 or chk_hdr.find("400") > 0:
                        break
                else:
                    break
            except Exception as tm:
                print("Inner Proxy: ", tm, " Data: ", data)
                break
        prx.close()

        if not first_reply:
            raise Exception("Reply was empty.")

        # Print logs
        decode_reply = first_reply.decode(encoding='utf-8', errors='ignore')

        req_frm_cli = "GET " + orig_url
        ua_frm_cli = orig_ua

        if redirect:
            req_to_dst = "GET " + redirect_url
        else:
            req_to_dst = req_frm_cli

        if mobile:
            ua_to_dst = "Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0"
        else:
            ua_to_dst = ua_frm_cli

        stat_code_dst_start = decode_reply.find(" ") + 1
        stat_code_dst_end = decode_reply.find("\r\n", stat_code_dst_start)
        stat_code_dst = decode_reply[stat_code_dst_start:stat_code_dst_end]

        if decode_reply.find("Content-Type:") > 0:
            mime_typ_start = decode_reply.find("Content-Type: ") + 14
            mime_typ_end = decode_reply.find("\r\n", mime_typ_start)
            mime_typ = decode_reply[mime_typ_start:mime_typ_end].split(";")[0]
        else:
            mime_typ = "None"

        if decode_reply.find("Content-Length:") > 0:
            mime_sz_start = decode_reply.find("Content-Length: ") + 16
            mime_sz_end = decode_reply.find("\r\n", mime_sz_start)
            mime_sz = decode_reply[mime_sz_start:mime_sz_end]
        else:
            mime_sz = "0"

        log(request_counter, "O" if redirect else "X", "O" if mobile else "X", address[0], address[1],
            req_frm_cli, ua_frm_cli, url, port, req_to_dst, ua_to_dst, stat_code_dst, mime_typ, mime_sz)

    except Exception as prx_error:
        print("Proxy: ", prx_error)
        prx.close()


# Take Port # from cli arguments
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
print("-------------------------------------------------------")

# Client vars
connections = [srv]
request_counter = 0
redirect = False
redirect_url = ""
orig_url = ""
mobile = False
orig_ua = ""

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
                            redirect = False
                            redirect_url = ""
                            orig_url = ""
                        if start_mobile_feat != -1:
                            mobile = True
                        if stop_mobile_feat != -1:
                            mobile = False
                            orig_ua = ""

                        # Check redirect
                        orig_url = base_url
                        if redirect:
                            old_base_url = base_url
                            old_url = process_base_url(base_url)[0]
                            base_url = redirect_url
                            data = data.replace(old_base_url, base_url)
                            data = data.replace(old_url, base_url)

                        # Check mobile
                        user_agent_start = data.find("User-Agent:") + 12
                        user_agent_end = data.find("\r\n", user_agent_start) + 1
                        orig_ua = data[user_agent_start:user_agent_end - 1]
                        if mobile:
                            data = data.replace(data[user_agent_start:user_agent_end],
                                                'Mozilla/5.0 (Android 7.0; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0\r')
                            data = data.replace(base_url, process_base_url(base_url)[0] + '/')

                        # Check if persistent connection
                        if data.find("Connection:") > 0:
                            conn_header_start = data.find("Connection:")
                            conn_header_end = data.find("\r\n", conn_header_start)
                            data = data.replace(data[conn_header_start: conn_header_end], "Connection: close")
                        if data.find("Keep-Alive:") > 0:
                            ka_header_start = data.find("Keep-Alive:")
                            ka_header_end = data.find("\r\n", ka_header_start) + 2
                            data = data.replace(data[ka_header_start: ka_header_end], "")

                        proxy(process_base_url(base_url)[0], process_base_url(base_url)[1], s, data.encode())
                        request_counter += 1
                    except Exception as e:
                        print("Server: ", e)
                        pass
                else:

                    # Remove the disconnected client
                    connections.remove(s)

                    # Close the socket
                    s.close()
    except:
        print("[SRV disconnected]")
        srv.close()
        sys.exit()
