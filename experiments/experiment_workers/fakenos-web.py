import os
import random
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
            "configuration_file": os.environ.get(
                "CONFIGURATION_FILE", "site_1.yaml.j2"
            )
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
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    return {"onts": onts}


@app.get("/api/hosts/{host}/unregister_ont/{ont_sn}")
async def unregister_ont(host: str, ont_sn: str):
    try:
        onts = []
        ont_to_unregister = None
        for port_index, port in enumerate(
            net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
            ["ports"]
        ):
            ont_to_unregister = next(
                (ont for ont in port if ont["sn"] == ont_sn),
                None
            )
            if not ont_to_unregister:
                continue
            for ont in port:
                ont["fsp"] = f"0/0/{port_index}"
                onts.append(ont)
            break
        ont_to_unregister["registered"] = False
        move_onts = [
            ont
            for ont in onts
            if ont["registered"]
            and int(ont["ont_id"]) > int(ont_to_unregister["ont_id"])
        ]
        for ont in move_onts:
            ont["ont_id"] = int(ont["ont_id"]) - 1
        return {"host": host, "ont_sn": ont_sn, "status": "unregistering"}
    except (Exception,):
        return {"host": host, "ont_sn": ont_sn, "status": "not found"}


@app.get("/api/hosts/{host}/change_board_state")
async def board_failure(host: str):
    board = net.hosts[host].nos.device.configurations["frames"][0]["slots"][4]
    if board["status"] == "Standby_active":
        board["status"] = "Standby_failed"
    else:
        board["status"] = "Standby_active"
    return {"host": host, "board_id": 4, "status": board["status"]}


@app.get("/api/hosts/{host}/ont/{ont_sn}/set_high_voltage")
async def set_high_voltage(host: str, ont_sn: str):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_voltage = ont["voltage_v"]
    ont["voltage_v"] = round(random.uniform(3.6, 3.8), 2)
    return {
        "host": host,
        "ont_sn": ont_sn,
        "previous_voltage": previous_voltage,
        "new_voltage": ont["voltage_v"]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/set_low_voltage")
async def set_low_voltage(host: str, ont_sn: str):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_voltage = ont["voltage_v"]
    ont["voltage_v"] = round(random.uniform(2.8, 3.0), 2)
    return {
        "host": host,
        "ont_sn": ont_sn,
        "previous_voltage": previous_voltage,
        "new_voltage": ont["voltage_v"]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/set_normal_voltage")
async def set_normal_voltage(host: str, ont_sn: str):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_voltage = ont["voltage_v"]
    ont["voltage_v"] = round(random.uniform(3.2, 3.4), 2)
    return {
        "host": host,
        "ont_sn": ont_sn,
        "previous_voltage": previous_voltage,
        "new_voltage": ont["voltage_v"]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/set_gemport_0/{gemport}")
async def set_gemport_0(host: str, ont_sn: str, gemport: int):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_gemport = ont["gemports"][0]
    print(ont)
    ont["gemports"][0] = gemport
    return {
        "host": host,
        "ont_sn": ont_sn,
        "previous_gemport": previous_gemport,
        "new_gemport": ont["gemports"][0]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/port_eth/{port_id}/c__vlan/{vlan}")
async def set_c_vlan(host: str, ont_sn: str, port_id: int, vlan: int):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_vlan = ont["ports"]["eth"][port_id]["c__vlan"]
    ont["ports"]["eth"][port_id]["c__vlan"] = vlan
    return {
        "host": host,
        "ont_sn": ont_sn,
        "port_id": port_id,
        "previous_vlan": previous_vlan,
        "new_vlan": ont["ports"]["eth"][port_id]["c__vlan"]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/port_eth/{port_id}/s__vlan/{vlan}")
async def set_s_vlan(host: str, ont_sn: str, port_id: int, vlan: int):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_vlan = ont["ports"]["eth"][port_id]["s__vlan"]
    ont["ports"]["eth"][port_id]["s__vlan"] = vlan
    return {
        "host": host,
        "ont_sn": ont_sn,
        "port_id": port_id,
        "previous_vlan": previous_vlan,
        "new_vlan": ont["ports"]["eth"][port_id]["s__vlan"]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/port_eth/{port_id}/change_vlan__type")
async def set_vlan_type(host: str, ont_sn: str, port_id: int):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_vlan_type = ont["ports"]["eth"][port_id]["vlan__type"]
    if previous_vlan_type == "QINQ":
        ont["ports"]["eth"][port_id]["vlan__type"] = "Translation"
    else:
        ont["ports"]["eth"][port_id]["vlan__type"] = "QINQ"
    return {
        "host": host,
        "ont_sn": ont_sn,
        "port_id": port_id,
        "previous_vlan_type": previous_vlan_type,
        "new_vlan_type": ont["ports"]["eth"][port_id]["vlan__type"]
    }


@app.get("/api/hosts/{host}/ont/{ont_sn}/snmp_profile/{profile_id}")
async def set_snmp_profile(host: str, ont_sn: str, profile_id: int):
    onts = []
    for port in (
        net.hosts[host].nos.device.configurations["frames"][0]["slots"][0]
        ["ports"]
    ):
        onts += port
    ont = next(ont for ont in onts if ont["sn"] == ont_sn)
    previous_profile = ont["snmp_profile_id"]
    ont["snmp_profile_id"] = profile_id
    ont["snmp_profile_name"] = f"snmp-profile_{profile_id}"
    return {
        "host": host,
        "ont_sn": ont_sn,
        "previous_profile": previous_profile,
        "new_profile": ont["snmp_profile_id"]
    }


@app.get("/api/hosts/{host}/services")
async def list_services(host: str):
    services = net.hosts[host].nos.device.configurations["services"]
    return {"host": host, "services": services}


@app.get("/api/hosts/{host}/change_service_state/{service_name}")
async def change_service_state(host: str, service_name: str):
    service = (
        net.hosts[host]
        .nos.device.configurations["services"]
        [service_name]
    )
    previous_state = service["state"]
    if previous_state == "enable":
        service["state"] = "disable"
    else:
        service["state"] = "enable"
    return {
        "host": host,
        "service_name": service_name,
        "previous_state": previous_state,
        "new_state": service["state"]
    }


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
