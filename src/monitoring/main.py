import signal
import socket
from json import loads
from queue import Queue
from threading import Thread, Lock
from time import sleep

from flask import Flask, render_template
from loguru import logger

app = Flask(__name__)
RUN = True


class GraphDataMaker:
    def __init__(self):
        self.nodes = []
        self.links = []
        self._knowclients = set()
        self._lock = Lock()
        self.i = 1

    def add(self, hostname, db):
        with self._lock:
            if hostname in self._knowclients:
                return

            self._knowclients.add(hostname)
            self.nodes.append({
                "id": hostname,
                "group": self.i
            })
            self.i += 1
            for client in db:
                self.links.append({
                    "source": hostname,
                    "target": client["name"],
                    "value": 1
                })

    def dump(self) -> dict:
        with self._lock:
            return {"nodes": self.nodes, "links": self.links}


graph_data_maker = GraphDataMaker()


def wait_clients(sock, queue: Queue):
    while RUN:
        hostname, addr = sock.recvfrom(1024 * 10)
        logger.info(f"find bot {addr[0]}")
        logger.info(addr[0])
        queue.put((hostname.decode("utf-8"), addr[0]))


def send_brodcast(ip, queue):
    broadcast_ip = ".".join(ip.split('.')[:-1]) + ".255"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((ip, 6666))
    wait = Thread(target=wait_clients, args=(sock, queue))
    wait.start()
    while RUN:
        sock.sendto(b"metrics", (broadcast_ip, 5005))
        logger.info(f"wait metrics {ip}")
        sleep(10)
    wait.join()


def find_clients(queue):
    interfaces = socket.getaddrinfo(
        host=socket.gethostname(), port=None, family=socket.AF_INET
    )
    all_ips = {ip[-1][0] for ip in interfaces}
    tasks = []
    for ip in all_ips:
        tasks.append(Thread(target=send_brodcast, args=(ip, queue)))
        tasks[-1].start()

    while RUN:
        sleep(10)

    for task in tasks:
        task.join()


def main():
    clients = Queue(maxsize=1000)
    task = Thread(target=find_clients, args=(clients,))
    task.start()

    while RUN:
        if clients.empty():
            continue
        hostname, client = clients.get()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((client, 8888))
        sock.send(b"get db\n")
        db, _ = sock.recvfrom(1024 * 10)
        db = loads(db)
        graph_data_maker.add(hostname, db)
        logger.info(graph_data_maker.links)


@app.route("/")
def page():
    logger.info(graph_data_maker.dump())
    return render_template("index.html", data=graph_data_maker.dump())


main_t = Thread(target=main)
app_t = Thread(target=lambda: app.run(host="0.0.0.0", port=80, debug=False, use_reloader=False))


def stop(*args, **kwargs):
    global RUN
    RUN = False
    main_t.join()
    app_t.join()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    main_t.start()
    app_t.start()

    while RUN:
        sleep(10)
