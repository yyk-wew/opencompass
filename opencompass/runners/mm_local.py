import os.path as osp
import subprocess
from typing import Any, Dict, List, Tuple

import mmengine

from opencompass.registry import RUNNERS

from .base import BaseRunner


@RUNNERS.register_module()
class MMLocalRunner(BaseRunner):
    """Local runner. Start tasks by local python.

    Args:
        task (ConfigDict): Task type config.
        max_num_workers (int): Max number of workers to run in parallel.
            Defaults to 32.
        retry (int): Number of retries if the job failed. Defaults to 2.
        partition (str): Slurm partition name. Defaults to None.
        quotatype (str): Slurm quota type. Defaults to None.
        debug (bool): Whether to run in debug mode. Defaults to False.
        lark_bot_url (str): Lark bot url. Defaults to None.
        gpus_per_task (int): How many gpus used to run each task.
            Defaults to 8.
    """

    def __init__(self, retry: int = 2, gpus_per_task: int = 8):
        super().__init__(task=None, lark_bot_url=None)
        self.retry = retry
        self.gpus_per_task = gpus_per_task

    def __call__(self, tasks: List[str], args):
        """Launch multiple tasks and summarize the results."""
        tasks = [(task, args) for task in tasks]
        status = self.launch(tasks)
        self.summarize(status)

    def launch(self, tasks: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """Launch multiple tasks.

        Args:
            tasks (list[dict]): A list of task configs, usually generated by
                Partitioner.

        Returns:
            list[tuple[str, int]]: A list of (task name, exit code).
        """
        status = [self._launch(task) for task in tasks]
        return status

    def _launch(self, task) -> int:
        config_file, args = task

        command = (f'NCCL_SOCKET_IFNAME=eth0 '
                   f'bash opencompass/multimodal/inference_local.sh '
                   f'{config_file} {self.gpus_per_task}')
        args.work_dir = args.work_dir if args.work_dir is not None \
                else './work_dirs'
        out_path = osp.join(
            args.work_dir, f'{osp.splitext(osp.basename(config_file))[0]}.out')
        task_name = f'{osp.splitext(osp.basename(config_file))[0]}'
        mmengine.mkdir_or_exist(osp.split(out_path)[0])
        err_path = out_path.replace('.out', '.err')
        mmengine.mkdir_or_exist(osp.split(err_path)[0])
        stdout = open(out_path, 'w')
        stderr = open(err_path, 'w')
        result = subprocess.run(command,
                                shell=True,
                                text=True,
                                stdout=stdout,
                                stderr=stderr)

        retry = self.retry
        while result.returncode != 0 and retry > 0:
            retry -= 1
            result = subprocess.run(command,
                                    shell=True,
                                    text=True,
                                    stdout=stdout,
                                    stderr=stderr)
        return task_name, result.returncode
