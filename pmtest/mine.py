import copy
import os
import shutil

from pm4py.objects.log.importer.xes import factory as xes_import_factory
from pm4py.util.constants import PARAMETER_CONSTANT_ACTIVITY_KEY,\
    PARAMETER_CONSTANT_TIMESTAMP_KEY

from pm4py.visualization.petrinet import factory as pn_vis_factory

XES_PATH = os.path.join(".", "data", "xes")


def process_each():
    clean_folder("./results")

    for filename in os.listdir(XES_PATH):
        label = filename.split(".")[0]
        filepath = os.path.join(XES_PATH, filename)

        log = xes_import_factory.apply(filepath)

        process_log(log, label)


def process_combined():
    clean_folder("./results")

    print("Combining all log files:")
    combined_log = None

    for filename in os.listdir(XES_PATH):
        filepath = os.path.join(XES_PATH, filename)
        print(f"Processing '{filepath}'")

        log = xes_import_factory.apply(filepath)
        if combined_log:
            for trace in log:
                combined_log.append(trace)
        else:
            combined_log = log

    print(f"Finished combining, total length is {len(combined_log)}")
    print()

    process_log(log, "combined")


def process_log(log, label):
    for activity_key in ["dest_class", 'dest_class_func']:
        print(f"label={label}, activity_key={activity_key}")

        folder = f"./results/{label}/{activity_key}"
        make_folder(folder)

        print("Running Alpha")
        alpha = run_alpha(log, label, activity_key)
        export_petri_net(f"{folder}/alpha_classic.svg", alpha)

        print("Running Alpha-Plus")
        alpha_plus = run_alpha(log, label, activity_key,
                               variant="plus")
        export_petri_net(f"{folder}/alpha_plus.svg", alpha_plus)

        print("Running IMDFb")
        imdfb = run_imdfb(log, label, activity_key)
        export_petri_net(f"{folder}/imdfb.svg", imdfb)

        print("Running Heuristic Miner (Config A)")
        heuristic_a = run_heuristic(log, label, activity_key)
        export_petri_net(f"{folder}/heuristic_a.svg", heuristic_a)

        print("Running Heuristic Miner (Config B)")
        heuristic_b_params = {
            "dependency_thresh": 0,
            "and_measure_thresh": 0,
            "min_act_count": 1,
            "min_dfg_occurrences": 1,
            "dfg_pre_cleaning_noise_thresh": 0.1
        }
        heuristic_b = run_heuristic(log, label, activity_key,
                                    parameters=heuristic_b_params)
        export_petri_net(f"{folder}/heuristic_b.svg", heuristic_b)

        print()
        print()


def run_alpha(log, label, activity_key, variant="classic"):
    from pm4py.algo.discovery.alpha import factory as alpha_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }

    return alpha_miner.apply(copy.deepcopy(log), parameters=miner_params,
                             variant=variant)


def run_imdfb(log, label, activity_key):
    from pm4py.algo.discovery.inductive import factory as inductive_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }

    return inductive_miner.apply(log, parameters=miner_params)


def run_heuristic(log, label, activity_key, parameters={}):
    from pm4py.algo.discovery.heuristics import factory as heuristics_miner

    miner_params = {
        PARAMETER_CONSTANT_TIMESTAMP_KEY: "time",
        PARAMETER_CONSTANT_ACTIVITY_KEY: activity_key
    }

    for key in parameters:
        miner_params[key] = parameters[key]

    return heuristics_miner.apply(log, parameters=miner_params)


def export_petri_net(path, output):
    net, i_m, f_m = output

    viz_params = {"format": "svg", "debug": True}
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters=viz_params)
    pn_vis_factory.save(gviz, path)


def clean_folder(path):
    make_folder(path)

    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)


def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


if __name__ == "__main__":
    import sys
    if "combined" in sys.argv:
        process_combined()
    else:
        process_each()
