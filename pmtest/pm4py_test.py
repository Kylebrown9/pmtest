from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY,\
    PARAMETER_CONSTANT_TIMESTAMP_KEY

from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.visualization.petrinet import factory as pn_vis_factory

from .parse import parse_directory_logs


def execute_script():
    label = "trade-portfolio-sell"
    log = list(parse_directory_logs("./data/DayTrader", label=label))
    print(f"Parsed logs, size={len(log)}")
    log = [case for case in log if len(case) < 1000]
    print(f"Filtered logs, size={len(log)}")

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: "destination_name"
    }
    net, i_m, f_m = alpha_miner.apply(log, parameters=miner_params,
                                      variant="plus")

    print(f"Process Mined")

    viz_params = {"format": "svg", "debug": True}
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters=viz_params)

    print(f"Visualized")

    import time
    pn_vis_factory.save(gviz, "./results/" + str(time.time()) + ".svg")


if __name__ == "__main__":
    execute_script()
