import os
import argparse
import json
import glob
import argparse

from typing import Dict, Any, List, Union
import pandas as pd
from tqdm import tqdm


_CUR_DIR = os.path.dirname(os.path.realpath(__file__))


def _create_placeholder_eval_result_dict() -> Dict[str, Dict[str, Any]]:
    # 
    # Create pdict for mapping results generated by inference routine to the final
    # result dictionay for evaluation
    #
    pdict = {}

    _resp_status = "TO_BE_EVALUATED"

    # DRCD
    data = json.load(open(f'{_CUR_DIR}/../data/DRCD_Test/preprocessed_DRCD_test.json'))
    pdict['DRCD'] = {str(k): {"response": _resp_status} for k, v in data.items()}

    # FGC
    data = json.load(open(f'{_CUR_DIR}/../data/FGC_Test/preprocessed_FGC_official_final.json'))
    pdict['FGC'] = {str(k): {"response": _resp_status} for k, v in data.items()}

    # TTQA
    data = json.load(open(f'{_CUR_DIR}/../data/TTQA/TTQA_mc.json'))
    pdict['TTQA'] = {str(k): {"response": _resp_status} for k, v in data.items()}

    # XSum_TC
    df = pd.read_csv(f'{_CUR_DIR}/../data/XSum_TC_5k/test_sub5000.csv')
    pdict['XSum_TC_5k'] = {str(i): {"response": _resp_status} for i, row in df.iterrows()}

    # IMDB
    df = pd.read_csv(f'{_CUR_DIR}/../data/IMDB_TC/test.csv')
    pdict['IMDB_TC'] = {str(i): {"response": _resp_status} for i, row in df.iterrows()}

    # BigBench
    data = json.load(open(f'{_CUR_DIR}/../data/PenguinsInTable_TC/data.json'))
    pdict['PenguinsInTable_TC'] = {str(k): {"response": _resp_status} for k, v in data.items()}

    # TMMLU
    tmmlu_dirs = glob.glob(f"{_CUR_DIR}/../data/TMMLU/subjects/*")
    subjects = [d.split('/')[-1] for d in tmmlu_dirs]
    for s, d in zip(subjects, tmmlu_dirs):
        df = pd.read_csv(f"{d}/data.csv")
        pdict[f"TMMLU/{s}"] = {str(i): {"response": _resp_status} for i, row in df.iterrows()}
    
    # TMMLU+
    tmmlu_dirs = glob.glob(f"{_CUR_DIR}/../data/TMMLU_plus/subjects/*")
    subjects = [d.split('/')[-1] for d in tmmlu_dirs]
    for s, d in zip(subjects, tmmlu_dirs):
        df = pd.read_csv(f"{d}/data.csv")
        pdict[f"TMMLU_plus/{s}"] = {str(i): {"response": _resp_status} for i, row in df.iterrows()}
    
    return pdict


class ResultAggregator:
    # The class is for aggregating inference results for evaluation
    def __init__(self, model_name):
        self._model_name = model_name
        self._pdict = ResultAggregator.create_result_placerholder_dict()

    @staticmethod
    def create_result_placerholder_dict():
        return _create_placeholder_eval_result_dict()

    def merge_result(self, result_json: Union[dict, str]):
        r"""
        Assuming the data format in the json is
        ```
        {
            "$dataset_name": [
                {'id': $id_num,
                 'response': $response
                }, ...
            ]
        }
        ```
        """
        jdata = result_json
        if isinstance(result_json, str):
            jdata = json.load(open(result_json, "r"))
        ds_name = list(jdata.keys())[0]

        # Place results into result dict
        for s in jdata[ds_name]:
            idx_str = str(s['id'])
            self._pdict[ds_name][idx_str]['response'] = s['response']
            self._pdict[ds_name][idx_str]['query'] = s['query']
            self._pdict[ds_name][idx_str]['references'] = s['references']

    def to_eval_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        # Convert result dict to final output format
        rdict = {}
        for dname, vals in self._pdict.items():
            final_results = [dict(id=idx, **resp) for idx, resp in vals.items()]
            rdict[dname] = final_results

        return rdict

    def save_agg_result_dict(self, agg_result_dir = None):
        rdict = self.to_eval_dict()
        outputs = {'name': self._model_name, "results": rdict}
        
        # Save to result folder
        dest = f"{_CUR_DIR}/../results/{self._model_name}_result.json"
        if agg_result_dir is not None:
            dest = f"{agg_result_dir}/{self._model_name}_result.json"
        json.dump(outputs, open(dest, "w"), indent=2, ensure_ascii=False)
        # print(f".... dump aggregated results to {dest}")


    def aggregate_inference_results_for_evaluation(self, inference_results_dir):
        r"""
        input:
            result_dir: where the result.json generated in the inference routine lies
            model_name: the name of the model that generated the result.json
        
        output:
            eval_json_path: path to the ${model_name}_results.json that stores the evaluation result

        The `result.json` is expected to have the following format

        """
        # Fill the results back to pdict
        result_jpath = glob.glob(f"{inference_results_dir}/**/result.json", recursive=True)

        for jpath in tqdm(result_jpath):
            self.merge_result(jpath)

        self.save_agg_result_dict(inference_results_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--result_dir", default=None, type=str)
    parser.add_argument("--model_name", default=None, type=str)
    args = parser.parse_args()

    result_dir = args.result_dir
    model_name = args.model_name
    agg = ResultAggregator(model_name)
    agg.aggregate_inference_results_for_evaluation(result_dir)
