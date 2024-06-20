# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import re
import os
from constants import *
from base64 import b64encode, b64decode


class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta que termina la conexión.
    """

    def __init__(self, socket, directory):
        self.socket = socket
        self.connected = True
        self.directory = directory
        self.buffer = ''
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while self.connected:
            data = self.socket.recv(4096).decode("utf-8")
            if not data:
                self.socket.close()
                break
            self.buffer += data
            self._process_buffer()

        self._close_connection()

    def process_command(self, data):
        command_parts = data.split()
        command_name = command_parts[0]

        if re.findall(r"\n(?!\r)", data):
            response = send_status(BAD_EOL)
            self._send_status(response)
            self.connected = False
        try:
            if command_name == "quit":
                self._handle_quit(command_parts)
            elif command_name == "get_file_listing":
                self._handle_get_file_listing(command_parts)
            elif command_name == "get_metadata":
                self._handle_get_metadata(command_parts)
            elif command_name == "get_slice":
                self._handle_get_slice(command_parts)
            else:
                response = send_status(INVALID_COMMAND)
                self._send_status(response)
        except Exception as e:
            response = send_status(INTERNAL_ERROR)
            self._send_status(response)

    def _handle_quit(self, command_parts):
        if len(command_parts) == 1:
            response = send_status(CODE_OK)
            self.connected = False
        else:
            response = send_status(INVALID_ARGUMENTS)

        self._send_status(response)

    def _handle_get_file_listing(self, command_parts):
        if len(command_parts) == 1:
            response = send_status(CODE_OK)
            files = [f for f in os.listdir(self.directory) if os.path.isfile(
                os.path.join(self.directory, f))]
            for file in files:
                response += f"{file}{EOL}"
            response += f"{EOL}"
        else:
            response = send_status(INVALID_ARGUMENTS)

        self._send_status(response)

    def _handle_get_metadata(self, command_parts):
        if len(command_parts) == 2:
            file_name = command_parts[1]
            file = os.path.join(self.directory, file_name)
            if os.path.exists(file):
                response = send_status(CODE_OK)
                response += f"{os.path.getsize(file)}{EOL}"
            else:
                response = send_status(FILE_NOT_FOUND)
        else:
            response = send_status(INVALID_ARGUMENTS)

        self._send_status(response)

    def _handle_get_slice(self, command_parts):
        if len(command_parts) == 4 and command_parts[2].isdigit() and command_parts[3].isdigit():
            offset = int(command_parts[2])
            size = int(command_parts[3])
            file = os.path.join(self.directory, command_parts[1])

            file_size = os.path.getsize(file)

            if offset > file_size or offset < 0 or size > file_size - offset:
                response = send_status(BAD_OFFSET)
            elif not os.path.exists(file):
                response = send_status(FILE_NOT_FOUND)
            else:
                with open(file, "rb") as file:
                    file_data = file.read()

                file_data = file_data[offset: offset + size]
                encoded_data = b64encode(file_data)

                response = send_status(CODE_OK)
                response += f"{encoded_data.decode('utf-8')}{EOL}"
        else:
            response = send_status(INVALID_ARGUMENTS)

        self._send_status(response)

    def _close_connection(self):
        self.socket.close()

    def _process_buffer(self):
        eol_index = self.buffer.find(EOL)
        while eol_index != -1:
            line = self.buffer[:eol_index]
            self.process_command(line)
            self.buffer = self.buffer[eol_index + len(EOL):]
            eol_index = self.buffer.find(EOL)

    def _send_status(self, response):
        self.socket.send(response.encode("utf-8"))
