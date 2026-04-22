import datetime, time
from display_driver import read_operstate, wifi_is_up, get_network_state

# Estado local (sem globals)
_net = {"lan": False, "wifi": False, "last_check": 0.0}

def make_background(net_interval=5.0, clock_phase=4.0, ip_phase=True):
    """
    Retorna um callable(hw) usado pelo servidor como tarefa de fundo.
    Alterna entre relógio e exibição de IP.
    """
    state = {"phase": "clock", "phase_start": time.monotonic(),
             "colon": True, "last_net": 0.0,
             "lan": False, "wifi": False}

    def tick(hw):
        t = time.monotonic()

        # Atualiza estado de rede periodicamente
        if t - state["last_net"] > net_interval:
            state["lan"]      = read_operstate("eth0")
            state["wifi"]     = wifi_is_up()
            state["last_net"] = t

        now = datetime.datetime.now()
        state["colon"] = (now.second % 2 == 0)

        hw.show_clock(
            hour=now.hour, minute=now.minute,
            colon_on=state["colon"],
            lan_on=state["lan"], wifi_on=state["wifi"]
        )

    return tick