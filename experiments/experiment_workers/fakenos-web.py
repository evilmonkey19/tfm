import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from fakenos import FakeNOS

inventory = {
    "hosts": {
        "OLT": {
            "username": "admin",
            "password": "admin",
            "port": 9000,
            "platform": "huawei_smartax",
            "configuration_file": os.environ.get("CONFIGURATION_FILE", "configuration.yaml.j2")
        }
    }
}

net = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global net
    net = FakeNOS(inventory=inventory)
    net.start()
    print(net)
    try:
        yield
    finally:
        net.stop()

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/api/hosts")
async def root():
    hosts = list(net.hosts)
    return {"hosts": [{host: {
        "username": net.hosts[host].username,
        "password": net.hosts[host].password,
        "port": net.hosts[host].port,
        "platform": net.hosts[host].platform,
        "running": net.hosts[host].running
    }} for host in hosts]}


@app.get("/api/hosts/{host}/start")
async def start(host: str):
    net.start(host)
    return {"host": host, "status": "starting"}

@app.get("/api/hosts/{host}/shutdown")
async def shutdown(host: str):
    net.stop(host)
    return {"host": host, "status": "shutting down"}

@app.get("/api/hosts/{host}/list_onts")
async def list_onts(host: str):
    onts = []
    for port in net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]["ports"]:
        onts += port
    return {"onts": onts}

@app.get("/api/hosts/{host}/unregister_ont/{ont_sn}")
async def unregister_ont(host: str, ont_sn: str):
    onts = []
    for port in net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]["ports"]:
        onts += port
    for ont in onts:
        if ont["sn"] == ont_sn:
            previously_registered = ont["registered"]
            ont["registered"] = False
            return {"host": host, "ont_sn": ont_sn, "previous_state": previously_registered, "status": "unregistering"}
    return {"host": host, "ont_sn": ont_sn, "status": "not found"}

@app.get("/", response_class=HTMLResponse)
async def hosts(request: Request):
    hosts = list(net.hosts)
    hosts = {host: net.hosts[host] for host in hosts}
    print(hosts)
    return templates.TemplateResponse(
        request=request, name="hosts.html", context={"hosts": hosts}
    )

@app.post("/hosts/{host}/shutdown")
async def shutdown_host(request: Request, host: str):
    net.stop(host)
    return RedirectResponse(url="/", status_code=303)

@app.post("/hosts/{host}/start")
async def start_host(request: Request, host: str):
    net.start(host)
    return RedirectResponse(url="/", status_code=303)