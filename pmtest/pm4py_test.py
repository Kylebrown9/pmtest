from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY,\
    PARAMETER_CONSTANT_TIMESTAMP_KEY

from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.visualization.petrinet import factory as pn_vis_factory

from .parse import parse_directory_logs

from collections import defaultdict
import copy


def execute_script():
    logs = defaultdict(list)

    for label, case in parse_directory_logs("./data/DayTrader"):
        if len(case) < 1000:
            logs[label].append(case)

    print(f"Finished parsing, found {len(logs)} labels")

    for label, cases in logs.items():
        print(f"Label={label}, num_cases={len(cases)}")

        for activity_key in ["dest_class", 'dest_class_func']:
            mine_log(copy.deepcopy(cases), label, activity_key)


def mine_log(cases, label, activity_key):
    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }
    net, i_m, f_m = alpha_miner.apply(cases, parameters=miner_params,
                                      variant="plus")

    print(f"Process Mined")

    viz_params = {"format": "svg", "debug": True}
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters=viz_params)

    print(f"Visualized")

    file_name = f"./results/{label}/{activity_key}.svg"

    import os
    if not os.path.exists(f'./results/{label}'):
        os.makedirs(f'./results/{label}')

    pn_vis_factory.save(gviz, file_name)

    print(f"Saved")


if __name__ == "__main__":
    execute_script()
