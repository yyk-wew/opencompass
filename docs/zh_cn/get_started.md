# 安装

1. 准备 OpenCompass 运行环境：

```bash
conda create --name opencompass python=3.10 pytorch torchvision pytorch-cuda -c nvidia -c pytorch -y
conda activate opencompass
```

如果你希望自定义 PyTorch 版本或相关的 CUDA 版本，请参考 [官方文档](https://pytorch.org/get-started/locally/) 准备 PyTorch 环境。需要注意的是，OpenCompass 要求 `pytorch>=1.13`。

2. 安装 OpenCompass：

```bash
git clone https://github.com/InternLM/opencompass.git
cd opencompass
pip install -e .
```

3. 安装 humaneval（可选）：

如果你需要**在 humaneval 数据集上评估模型代码能力**，请执行此步骤，否则忽略这一步。

<details>
<summary><b>点击查看详细</b></summary>

```bash
git clone https://github.com/openai/human-eval.git
cd human-eval
pip install -r requirements.txt
pip install -e .
cd ..
```

请仔细阅读 `human_eval/execution.py` **第48-57行**的注释，了解执行模型生成的代码可能存在的风险，如果接受这些风险，请取消**第58行**的注释，启用代码执行评测。

</details>

# 数据集准备

OpenCompass 支持的数据集主要包括两个部分：

1. Huggingface 数据集： [Huggingface Dataset](https://huggingface.co/datasets) 提供了大量的数据集，这部分数据集运行时会**自动下载**。

2. 自建以及第三方数据集：OpenCompass 还提供了一些第三方数据集及自建**中文**数据集。运行以下命令**手动下载解压**。

在 OpenCompass 项目根目录下运行下面命令，将数据集准备至 '${OpenCompass}/data' 目录下：

```bash
wget https://github.com/InternLM/opencompass/releases/download/0.1.0/OpenCompassData.zip
unzip OpenCompassData.zip
```

OpenCompass 已经支持了大多数常用于性能比较的数据集，具体支持的数据集列表请直接在 `configs/datasets` 下进行查找。

# 快速上手

OpenCompass 的评测以配置文件为中心，必须包含 `datasets` 和 `models` 字段，配置需要评测的模型以及数据集，使用入口 'run.py' 启动。

我们会以测试 [OPT-125M](https://huggingface.co/facebook/opt-125m) 以及 [OPT-350M](https://huggingface.co/facebook/opt-350m) 预训练基座模型在 [SIQA](https://huggingface.co/datasets/social_i_qa) 和 [Winograd](https://huggingface.co/datasets/winogrande) 上的性能为例，带领你熟悉 OpenCompass 的一些基本功能。
本次的测试的配置文件为[configs/eval_demo.py](https://github.com/InternLM/opencompass/blob/main/configs/eval_demo.py)。

运行前确保已经安装了 OpenCompass，本实验可以在单张 _GTX-1660-6G_ 显卡上成功运行。
更大参数的模型，如 Llama-7B, 可参考 [configs](https://github.com/InternLM/opencompass/tree/main/configs) 中其他例子。

使用以下命令在本地启动评测任务(运行中需要联网自动下载数据集和模型，模型下载较慢)：

```bash
python run.py configs/eval_demo.py
```

运行 demo 期间，我们来仔细解本案例中的配置内容以及启动选项。

## 步骤详解

<details>
<summary><b>数据集列表`datasets`</b></summary>

```python
from mmengine.config import read_base                # 使用 mmengine 的 config 机制

with read_base():
    # 直接从预设数据集配置中读取需要的数据集配置
    from .datasets.winograd.winograd_ppl import winograd_datasets
    from .datasets.siqa.siqa_gen import siqa_datasets

datasets = [*siqa_datasets, *winograd_datasets]       # 最后 config 需要包含所需的评测数据集列表 datasets
```

[configs/datasets](https://github.com/InternLM/OpenCompass/blob/main/configs/datasets) 包含各种数据集预先定义好的配置文件；
部分数据集文件夹下有 'ppl' 和 'gen' 两类配置文件，表示使用的评估方式，其中 `ppl` 表示使用判别式评测， `gen` 表示使用生成式评测。
[configs/datasets/collections](https://github.com/InternLM/OpenCompass/blob/main/configs/datasets/collections) 存放了各类数据集集合，方便做综合评测。

更多信息可查看 [配置数据集](./user_guides/dataset_prepare.md)

</details>

<details>
<summary><b>模型列表`models`</b></summary>

HuggingFace 中的 'facebook/opt-350m' 以及 'facebook/opt-125m' 支持自动下载权重，所以不需要额外下载权重：

```python
from opencompass.models import HuggingFaceCausalLM    # 提供直接使用 HuggingFaceCausalLM 模型的接口

# OPT-350M
opt350m = dict(
       type=HuggingFaceCausalLM,
       # 以下参数为 HuggingFaceCausalLM 的初始化参数
       path='facebook/opt-350m',
       tokenizer_path='facebook/opt-350m',
       tokenizer_kwargs=dict(
           padding_side='left',
           truncation_side='left',
           proxies=None,
           trust_remote_code=True),
       model_kwargs=dict(device_map='auto'),
       max_seq_len=2048,
       # 下参数为各类模型都有的参数，非 HuggingFaceCausalLM 的初始化参数
       abbr='opt350m',                    # 模型简称，用于结果展示
       max_out_len=100,                   # 最长生成 token 数
       batch_size=64,                     # 批次大小
       run_cfg=dict(num_gpus=1),          # 运行配置，用于指定资源需求
    )

# OPT-125M
opt125m = dict(
       type=HuggingFaceCausalLM,
       # 以下参数为 HuggingFaceCausalLM 的初始化参数
       path='facebook/opt-125m',
       tokenizer_path='facebook/opt-125m',
       tokenizer_kwargs=dict(
           padding_side='left',
           truncation_side='left',
           proxies=None,
           trust_remote_code=True),
       model_kwargs=dict(device_map='auto'),
       max_seq_len=2048,
       # 下参数为各类模型都有的参数，非 HuggingFaceCausalLM 的初始化参数
       abbr='opt125m',                # 模型简称，用于结果展示
       max_out_len=100,               # 最长生成 token 数
       batch_size=128,                # 批次大小
       run_cfg=dict(num_gpus=1),      # 运行配置，用于指定资源需求
    )

models = [opt350m, opt125m]
```

</details>

<details>
<summary><b>启动评测</b></summary>

首先，我们可以使用 debug 模式启动任务，以检查模型加载、数据集读取是否出现异常，如未正确读取缓存等。

```shell
python run.py configs/eval_demo.py -w outputs/demo --debug
```

但 `--debug` 模式下只能逐一序列执行任务，因此检查无误后，可关闭 `--debug` 模式，使程序充分利用多卡资源

```shell
python run.py configs/eval_demo.py -w outputs/demo
```

以下是一些与评测相关的参数，可以帮助你根据自己的环境情况配置更高效的推理任务。

- `-w outputs/demo`: 评测日志及结果保存目录
- `-r`: 重启上一次（中断的）评测
- `--mode all`: 指定进行某一阶段的任务
  - all: 进行全阶段评测，包括推理和评估
  - infer: 仅进行各个数据集上的推理
  - eval: 仅基于推理结果进行评估
  - viz: 仅展示评估结果
- `--max-partition-size 2000`: 数据集拆分尺寸，部分数据集可能比较大，利用此参数将其拆分成多个子任务，能有效利用资源。但如果拆分过细，则可能因为模型本身加载时间过长，反而速度更慢
- `--max-num-workers 32`: 最大并行启动任务数，在 Slurm 等分布式环境中，该参数用于指定最大提交任务数；在本地环境中，该参数用于指定最大并行执行的任务数，注意实际并行执行任务数受制于 GPU 等资源数，并不一定为该数字。

如果你不是在本机进行评测，而是使用 slurm 集群，可以指定如下参数：

- `--slurm`: 使用 slurm 在集群提交任务
- `--partition(-p) my_part`: slurm 集群分区
- `--retry 2`: 任务出错重试次数

The entry also supports submitting tasks to Alibaba Deep Learning Center (DLC), and more customized evaluation strategies. Please refer to [Launching an Evaluation Task](./user_guides/experimentation.md#launching-an-evaluation-task) for details.

```{tip}
这个脚本同样支持将任务提交到阿里云深度学习中心（DLC）上运行，以及更多定制化的评测策略。请参考 [评测任务发起](./user_guides/experimentation.md#评测任务发起) 了解更多细节。
```

</details>

## 评测结果

评测完成后，会打印评测结果表格如下：

```text
dataset    version    metric    mode      opt350m    opt125m
---------  ---------  --------  ------  ---------  ---------
siqa       e78df3     accuracy  gen         21.55      12.44
winograd   b6c7ed     accuracy  ppl         51.23      49.82
```

所有过程的日志，预测，以及最终结果会默认放在`outputs/default/`目录下。目录结构如下所示：

```text
outputs/default/
├── 20200220_120000
├── 20230220_183030   # 一次实验
│   ├── configs       # 可复现 config
│   ├── logs          # 日志
│   │   ├── eval
│   │   └── infer
│   ├── predictions   # 推理结果，每一条数据推理结果
│   └── results       # 评估结论，一个评估实验的数值结论
├── ...
```

其中，每一个时间戳文件夹代表一次实验中存在以下内容：

- 'configs':用于存放可复现配置文件；
- 'logs':用于存放**推理**和**评测**两个阶段的日志文件
- 'predicitions':用于存放推理结果，格式为json；
- 'results': 用于存放评测最终结果总结。

## 更多教程

想要更多了解 OpenCompass, 可以点击下列链接学习。

- [如何配置数据集](./user_guides/dataset_prepare.md)
- [如何定制模型](./user_guides/models.md)
- [深入了解启动实验](./user_guides/experimentation.md)
- [如何调Prompt](./prompt/overview.md)
