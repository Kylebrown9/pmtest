from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY,\
    PARAMETER_CONSTANT_TIMESTAMP_KEY

from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.visualization.petrinet import factory as pn_vis_factory

from .parse import parse_directory_logs

LABELS = ['Unknown', 'login', 'trade-account', 'trade-quotes-buy',
          'trade-home-glossary', 'trade-account-glossary'
          'trade-account-updateprofile', 'trade-marketsummary-glossary',
          'trade-portfolio-sell', 'trade-logoff', 'init']


MAX_INFO = {
    'source_fmt': {'package': True, 'class_name': True, 'func_name': True},
    'event_type': True,
    'dest_fmt': {'package': True, 'class_name': True, 'func_name': True}
}

MED_INFO = {
    'source_fmt': {'class_name': True, 'func_name': True},
    'event_type': True,
    'dest_fmt': {'class_name': True, 'func_name': True}
}

MIN_INFO = {
    'dest_fmt': {'class_name': True, 'func_name': True}
}


def execute_script():
    label = "trade-portfolio-sell"
    log_iter = parse_directory_logs("./data/DayTrader", label=label)
    log = [
        [
            {
                PARAMETER_CONSTANT_TIMESTAMP_KEY: record.time,
                PARAMETER_CONSTANT_ACTIVITY_KEY: record.format(**MED_INFO)
            }
            for record in case
        ]
        for case in log_iter
    ]
    # log = [case for case in log_iter if len(case) < 1000]

    print(f"Parsed logs, size={len(log)}")
    print(log[0])

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: PARAMETER_CONSTANT_TIMESTAMP_KEY,
        PARAMETER_CONSTANT_ACTIVITY_KEY: PARAMETER_CONSTANT_ACTIVITY_KEY
    }
    net, i_m, f_m = alpha_miner.apply(log, parameters=miner_params)

    print(f"Mined")

    viz_params = {"format": "svg", "debug": True}
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters=viz_params)

    print(f"Visualized")

    pn_vis_factory.view(gviz)

    print(f"Viewed")


if __name__ == "__main__":
    execute_script()
