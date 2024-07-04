import asyncio, asyncssh, sys, logging

logging.basicConfig() 
# asyncssh.set_log_level('DEBUG')
asyncssh.set_debug_level(3)

credential = {
    "host": "localhost",
    "username": "admin",
    "password": "admin",
    "client_keys": None,
    "known_hosts": None,
    "port": 6000
}

async def get_prompt(proc):
    prompt: str = ''
    while True:
        data = await proc.stdout.read(1)
        prompt = prompt + data if data != '\n' else ''
        if data.endswith((">", "#", "$")):
            prompt.strip()
            break

    print("Prompt received:", prompt)
    return prompt

async def send_command(proc, command: str, prompt: str):
    proc.stdin.write(command + "\r\n")
    await proc.stdin.drain()
    command_sent: str = ''
    output: str = ''
    while True:
        data = await proc.stdout.read(1)
        command_sent += data
        if command_sent == command + '\r\n':
            break
    while True:
        output += await proc.stdout.read(1)
        if output.endswith(prompt):
            output = output.replace(f'\n{prompt}', '')
            break
    return output

async def run_client() -> None:
    async with asyncssh.connect(**credential) as conn:
        async with conn.create_process(term_type="Dumb") as proc:
            prompt = await get_prompt(proc)
            output = await send_command(proc, "show clock", prompt)
            print(output)


try:
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run_client())
except (OSError, asyncssh.Error) as exc:
    sys.exit('SSH connection failed: ' + str(exc))