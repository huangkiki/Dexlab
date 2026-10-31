# Poke RoboAPI adapter / Poke RoboAPI 适配层

[English](#english) · [简体中文](#简体中文)

## English

This demo provides a dependency-free adapter for [Poke RoboAPI](https://developers.pokebot.com/zh/docs/roboapi/latest). DexLab task runners can query models, create a session, submit one wrist RGB image and an 8-value flange state, and parse the returned action chunk without installing the OpenAI SDK.

The API key is read only from `POKE_ROBOAPI_KEY`; it is never written to output, config files, or repository records.

```bash
export POKE_ROBOAPI_KEY='...'

PYTHONPATH=src python demos/roboapi-poke/poke_cli.py models
PYTHONPATH=src python demos/roboapi-poke/poke_cli.py schema --model poke-aurora-preview
PYTHONPATH=src python demos/roboapi-poke/poke_cli.py infer \
  --model poke-aurora-preview \
  --instruction 'Pick up the red block' \
  --image input.png \
  --state state.json
```

`state.json` is a JSON array of eight finite values: `[x, y, z, qx, qy, qz, qw, gripper]`. `infer` performs one policy call, prints the parsed actions, and reports `executed_steps: 0, status: interrupted` before closing the session. It does not control a robot.

Implemented:

- `src/dexlab/roboapi_poke.py`: standard-library HTTP client, input/output validation, action parsing, and `PokeSession` turn/feedback state.
- `demos/roboapi-poke/poke_cli.py`: read-only CLI for model/schema/one-shot inference.
- `tests/test_roboapi_poke.py`: local mock-server contract tests with no network or real API key.

Not yet implemented: a robot/simulator-specific observation provider and action executor for every DexLab task. The detailed sim2real, sensor, OVRTX, solver, and threshold matrix is in [the adapter documentation](../../docs/roboapi-poke.md).

## 简体中文

这个 demo 提供不依赖 `openai` SDK 的 [Poke RoboAPI](https://developers.pokebot.com/zh/docs/roboapi/latest) 适配层。DexLab 任务可以查询模型、创建会话、发送一张腕部 RGB 图像和 8 维法兰状态，并解析返回的动作块。

API key 只从 `POKE_ROBOAPI_KEY` 读取，不会写入输出、配置或仓库记录。

```bash
export POKE_ROBOAPI_KEY='...'

PYTHONPATH=src python demos/roboapi-poke/poke_cli.py models
PYTHONPATH=src python demos/roboapi-poke/poke_cli.py schema --model poke-aurora-preview
PYTHONPATH=src python demos/roboapi-poke/poke_cli.py infer \
  --model poke-aurora-preview \
  --instruction '把红色方块拿起来' \
  --image input.png \
  --state state.json
```

`state.json` 是 8 个有限数值的 JSON 数组：`[x, y, z, qx, qy, qz, qw, gripper]`。`infer` 只调用一次策略，打印解析后的动作，并以 `executed_steps: 0, status: interrupted` 关闭会话；它不会控制机器人。

已实现：

- `src/dexlab/roboapi_poke.py`：纯标准库 HTTP 客户端、输入输出校验、动作解析，以及 `PokeSession` 的轮次/回执状态。
- `demos/roboapi-poke/poke_cli.py`：模型查询、schema 查询和单次推理 CLI。
- `tests/test_roboapi_poke.py`：使用本地 mock server 的协议测试，不联网、不需要真实 key。

尚未实现：每个 DexLab 任务各自的仿真观测提供器和动作执行器。详细的 sim2real、传感器、OVRTX、solver 和阈值矩阵见[适配层文档](../../docs/roboapi-poke.zh-CN.md)。
