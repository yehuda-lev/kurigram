#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import logging
from typing import Optional, Type

from .transport import TCP, TCPAbridged

log = logging.getLogger(__name__)


class Connection:
    MAX_CONNECTION_ATTEMPTS = 3

    def __init__(
        self,
        dc_id: int,
        server_address: str,
        port: int,
        test_mode: bool,
        ipv6: bool,
        proxy: dict,
        media: bool = False,
        protocol_factory: Type[TCP] = TCPAbridged,
        crypto_executor_workers: int = 1,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        self.dc_id = dc_id
        self.server_address = server_address
        self.port = port
        self.test_mode = test_mode
        self.ipv6 = ipv6
        self.proxy = proxy
        self.media = media
        self.protocol_factory = protocol_factory
        self.crypto_executor_workers = crypto_executor_workers

        self.protocol: Optional[TCP] = None

        if isinstance(loop, asyncio.AbstractEventLoop):
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

        # Temporary workaround
        if self.test_mode:
            self.port = 80

            if self.ipv6:
                if self.dc_id == 1:
                    self.server_address = "2001:b28:f23d:f001::e"
                elif self.dc_id == 2:
                    self.server_address = "2001:67c:4e8:f002::e"
                elif self.dc_id == 3:
                    self.server_address = "2001:b28:f23d:f003::e"
            else:
                if self.dc_id == 1:
                    self.server_address = "149.154.175.10"
                elif self.dc_id == 2:
                    self.server_address = "149.154.167.40"
                elif self.dc_id == 3:
                    self.server_address = "149.154.175.117"

    async def connect(self) -> None:
        for i in range(Connection.MAX_CONNECTION_ATTEMPTS):
            self.protocol = self.protocol_factory(ipv6=self.ipv6, proxy=self.proxy, crypto_executor_workers=self.crypto_executor_workers, loop=self.loop)

            try:
                log.info("Connecting...")
                await self.protocol.connect((self.server_address, self.port))
            except OSError as e:
                log.warning("Unable to connect due to network issues: %s", e)
                await self.protocol.close()
                await asyncio.sleep(1)
            else:
                log.info("Connected! %s DC%s%s - IPv%s",
                         "Test" if self.test_mode else "Production",
                         self.dc_id,
                         " (media)" if self.media else "",
                         "6" if self.ipv6 else "4")
                break
        else:
            log.warning("Connection failed! Trying again...")
            raise ConnectionError

    async def close(self) -> None:
        await self.protocol.close()
        log.info("Disconnected")

    async def send(self, data: bytes) -> None:
        await self.protocol.send(data)

    async def recv(self) -> Optional[bytes]:
        return await self.protocol.recv()
