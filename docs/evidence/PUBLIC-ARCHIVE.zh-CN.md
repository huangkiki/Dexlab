# 历史布料证据：独立复算

[English](PUBLIC-ARCHIVE.md)

<!-- repository-only:start -->
下载[固定版本证据包](https://github.com/huangkiki/Dexlab/releases/download/v0.19.1/dexlab-historical-evidence-v1.tar.gz).

<!-- repository-only:end -->
本包补齐此前缺失的两组原始记录：105 条材料／布料记录和 1 条机器人夹布记录，保留全部所选失败。冻结的历史评分器得到布料 52 条通过、53 条失败，机器人夹布为 `geometry_review_required`。这是历史离线复算，不是新动力学实验或最新稳定版准入。

<!-- repository-only:start -->
解压回读后 106 条记录全部字段一致；[验证报告](public-archive-verification.json)。归档大小：655,361,853 字节。

SHA-256: `8871b11be5d84901dac048447c7570f665bc60f60217468de3def51903b43466`

<!-- repository-only:end -->
## 无需仓库和额外机器人资产即可运行

将归档解压到 `dexlab-historical-evidence-v1`，在其上级目录执行：

```bash
uv venv --python 3.12 .offline
uv pip install --python .offline/bin/python -r dexlab-historical-evidence-v1/requirements.txt
.offline/bin/python dexlab-historical-evidence-v1/reproduce.py \
  dexlab-historical-evidence-v1 --output historical-reproduction
```

环境和输出必须放在解压目录之外。脚本拒绝缺失、变更、未声明文件和符号链接，检查精确历史依赖版本，然后只使用包内评分代码，不启动仿真。只有全部 106 条记录对象与冻结参考一致才成功退出，比较包含指标、检查、失败和采样覆盖。`verification.json` 保存结果；发现差异会失败，不覆盖参考。无需 API key、UniLab 或额外机器人资产。精确旧版 MuJoCo 用于读取历史二进制模型，不是对新实验的版本建议。

## 公开分发做了什么变换

轨迹、接触记录、科学参数和源码快照保留原始字节。JSON 中删除部署命令、本地安装来源和本地协议文件名；复制的批次记录明确改绑公开文件哈希。仓库内原历史报告不变。

机器人二进制模型含资产绝对路径。公开副本仅替换原生路径表字符串，长度与偏移不变；路径表之外全部字节一致，官方历史加载器读回的数值数组逐字节一致。这修改的是模型记录，不是 MuJoCo 源码或二进制，也不改变几何、接触参数及已录制状态。

`manifest.json` 列明公开哈希、原始哈希与变换。原始哈希提供来源记录，但没有私有原件的读者不能独立证明被删除的内容。公开归档哈希绑定实际分发包。机器人几何沿用包内 OpenArm Apache-2.0、Wuji MIT 许可及声明，不包含苹果资产。

## 限制

评分源码快照匹配历史报告中 61 个源码哈希，使用记录的 NumPy、SciPy、MuJoCo 版本。后续机器人夹布评分要求额外地面证据，旧记录没有这些数据。复现历史结论不代表通过新版协议；新修复开发场景及其限制是另一个结果。这些记录不能证明物性标定、真机精度或引擎优越性。
