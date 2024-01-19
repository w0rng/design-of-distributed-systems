import signal
import socket
from json import loads
from queue import Queue
from threading import Thread, Lock
from time import sleep
from collections import defaultdict

from flask import Flask, render_template
from loguru import logger

app = Flask(__name__)
RUN = True


class GraphDataMaker:
    def __init__(self):
        self.db = defaultdict(list)
        self.client_statuses = dict()
        self.client_time = dict()
        self._lock = Lock()

    def delete(self):
        with self._lock:
            self.db = defaultdict(list)
            self.client_statuses = dict()
            self.client_time = dict()

    def add(self, hostname, db):
        with self._lock:
            for client in db:
                self.db[hostname].append(client["name"])
                if client['name'] in self.client_time:
                    if client['time'] > self.client_time[client['name']]:
                        self.client_time[client['name']] = client['time']
                        self.client_statuses[client['name']] = client['active']
                else:
                    self.client_time[client['name']] = client['time']
                    self.client_statuses[client['name']] = client['active']

    def dump(self) -> dict:
        with self._lock:
            return {"nodes": self._nodes(), "links": self._links()}

    def _get_client_status(self, client: str) -> bool:
        return self.client_statuses.get(client, False)

    def _nodes(self):
        result = []
        for i, client in enumerate(self._active_clients()):
            result.append({
                "id": client,
                "group": i
            })
        return result


    def _active_clients(self):
        return [client for client in self.db if self._get_client_status(client)]

    def _links(self):
        result = []
        active_clients = self._active_clients()
        for client in active_clients:
            for target in self.db[client]:
                if target not in active_clients:
                    continue
                if client == target:
                    continue
                result.append({
                    "source": client,
                    "target": target,
                    "value": 1,
                })
        return result


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
        logger.info(f"wait metrics {broadcast_ip}")
        sleep(3)
        graph_data_maker.delete()
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
