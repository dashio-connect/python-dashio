import asyncio

class ProcServer:
    async def _transfer(self, src, dest):
        while True:
            data = await src.read(1024)
            if data == b'':
                break
            dest.write(data)

    async def _handle_client(self, r, w):
        loop = asyncio.get_event_loop()
        print(f'Connection from {w.get_extra_info("peername")}')
        child = await asyncio.create_subprocess_exec(
            *TARGET_PROGRAM, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE)
        sock_to_child = loop.create_task(self._transfer(r, child.stdin))
        child_to_sock = loop.create_task(self._transfer(child.stdout, w))
        await child.wait()
        sock_to_child.cancel()
        child_to_sock.cancel()
        w.write(b'Process exited with status %d\n' % child.returncode)
        w.close()

    async def start_serving(self):
        await asyncio.start_server(self._handle_client,
                                   '0.0.0.0', SERVER_PORT)

SERVER_PORT    = 6666
TARGET_PROGRAM = ['./test']

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = ProcServer()
    loop.run_until_complete(server.start_serving())
    loop.run_forever()