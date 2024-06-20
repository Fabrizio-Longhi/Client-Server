#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
from connection import Connection
from constants import *
import threading


class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print("Serving %s on %s:%s." % (directory, addr, port))
        # FALTA: Crear socket del servidor, configurarlo, asignarlo
        # a una dirección y puerto, etc.

        # Crear socket del servidor
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Configurar socket del servidor
        self.server_socket.bind((addr, port))
        # Permitir una conexión a la vez
        self.server_socket.listen(5)
        # Guarda el directorio compartido
        self.directory = directory

    def handle_connection(self, client_socket, client_address):
        """
        Atiende una conexión de un cliente.
        """
        conn = Connection(client_socket, self.directory)
        conn.handle()  # Atiende la conexión
        print("Connection closed")
        # Cierra el socket del cliente
        client_socket.close()

    def serve(self):
        """
        Atiende conexiones de clientes entrantes. Crea hilos para cada cliente.
        """
        while True:
            # Connection para la conexión y atenderla hasta que termine.
            print("Waiting for connection")
            # client_socket es el socket del cliente, client_address es su dirección
            # Acepta una conexión del cliente
            client_socket, client_address = self.server_socket.accept()
            print("Connection from %s:%s" % client_address)
            # Crear un hilo para atender la conexión
            client_thread = threading.Thread(
                target=self.handle_connection, args=(client_socket, client_address))
            # Iniciar el hilo
            client_thread.start()


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    main()
