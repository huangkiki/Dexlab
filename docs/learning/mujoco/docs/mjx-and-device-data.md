# MJX 与设备数据：后端身份、批量轴和编译边界

本课覆盖 A8/B6 的设备数据与 JIT 主线。先读[CPU 批量](cpu-batching.md)、[状态与时间](state-and-time.md)和[接触/积分](solvers-and-integration.md)。MuJoCo/MJX 使用固定 3.15.0 树；JAX 的语言与随机 API 另以 0.7.2 固定提交阅读，见[外部来源清单](external-sources.json)。**这不是经运行验证的 MuJoCo–JAX 依赖锁。** 本轮没有安装、import、JIT、设备拷贝或仿真执行。

## 1. 名称相似不等于实现相同

| 层 | 本课核对的身份 | 必须单独记录的内容 |
|---|---|---|
| 原生 MuJoCo | C 核心与 `mujoco` Python 绑定 | 核心/绑定版本、构建精度、模型与 option |
| `mujoco-mjx` | 固定 MuJoCo 树内的 MJX 包，版本3.15.0 | package版本、`impl`、JAX/JAXlib配置 |
| MJX JAX | `_src` 中 JAX array 上的物理实现 | 支持分支、dtype、静态shape/JIT配置 |
| MJX Warp | JAX 入口经 FFI 调用树内 vendored MuJoCo Warp | vendored提交身份、Warp runtime、设备/容量/graph模式 |
| 外部学习栈 | 用户的 task/policy/optimizer/replay buffer | 自身版本、reward/reset/seed契约；不是 MuJoCo 核心 |

MJX 的 pyproject 对 JAX/JAXlib 没有固定版本，而 Warp extra 写的是 `warp-lang==1.17.0`。Warp 入口导入 `mujoco.mjx.third_party.mujoco_warp`；该内嵌目录的 pyproject 仍标3.14.0。故“MuJoCo3.15 + MJX Warp”不能简写成已验证的独立 `mujoco-warp` 发布版，也不能沿用 Newton 项目报告里的 Warp1.18.0。[MJX依赖](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/pyproject.toml#L1-L70)、[实际导入](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/warp/__init__.py#L19-L43)、[内嵌元数据](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/pyproject.toml#L1-L55)。

`put_model` 默认通常选择 JAX；CUDA 上只有 `MJX_GPU_DEFAULT_WARP=true` 且 Warp 已安装时才默认切到 Warp。为可审计配置应显式选 `impl='jax'` 或 `'warp'`。此树也有 CPP 的 I/O 枚举/分支，但 `forward`/`step` 没有把它实现为第三种完整步进后端。[默认选择](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L60-L139)、[实际步进分派](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L488-L530)。Warp 解析器接受 CUDA 或 CPU；这不等于每个设备上所有组合都已做运行验收。

## 2. 从可变原生对象到 pytree

原生 `mjModel/mjData` 是含连续 buffer 和派生缓存的可变对象。MJX 的 `Model/Data` 是冻结 dataclass：`replace` 返回新对象；被声明为 JAX array 的字段作为 pytree leaves，其余字段作为 metadata。NumPy 结构字段参与哈希/相等比较，从而决定 JIT 的结构身份。[dataclass实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/dataclasses.py#L30-L143)。

例如 `jnt_limited` 是 NumPy 结构字段，而 `jnt_range` 是 JAX array。前者改变可能改变约束结构并触发重编译；后者在相同 shape 下可以作为动态数值输入。区别来自字段类型和执行路径，不是“名字看起来是参数”。替换任意数组也不保证相关派生量已经更新。[字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/types.py#L680-L706)、[官方结构/数值说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/mjx.rst#L371-L405)。

设单世界状态为 x、模型参数为 θ，单步是函数形式：

$$
x'=F_h(\theta,x,u).
$$

这里的函数形式不表示碰撞处处光滑，也不表示各种后端有相同梯度支持。可微限制要结合[E3](solvers-and-integration.md)和具体实现；不能因为外层接受 `jax.jit` 就把任何求解、离散分支或 FFI 内核都视为可端到端求导。 本固定树的vendored Warp forward模块还显式设置`enable_backward=False`；该路径不能仅凭JAX外壳推断提供物理反向梯度。[Warp模块设置](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/forward.py#L50-L55)。

## 3. vmap 的轴是世界，时间仍有依赖

`vmap` 用 `in_axes` 指定哪些参数按一个轴展开：`None` 表示所有世界共享一个参数，`0` 表示输入第一维按世界切片。若 B 个世界共享模型，应该共享结构与参数；若某些参数按世界随机化，应按支持的布局让它们有 batch 轴，而非盲目给每个 metadata 字段加一维。[JAX vmap API](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L918-L1010)。

$$
x_{b,t+1}=F_h(\theta_b,x_{b,t},u_{b,t}),\quad b=0,\ldots,B-1.
$$

同一 t 上不同 b 可以独立计算；同一 b 上 t+1 依赖 t。`vmap` 不会把时间依赖变成独立样本，也不自动进行多GPU分片。批量数 B、worker数、设备数、时间长度 T 是四个不同量。

下面仅展示已兼容 **JAX backend** 对象的一步/选择接口；模型编译、初始化、JIT和执行均未在本轮进行。`reset_data` 必须具有相同结构，终态观测应在外部先保存，不能用这个选择函数代替完整学习环境。

```python
import jax
from mujoco import mjx


def step_one(model, data, control):
    return mjx.step(model, data.replace(ctrl=control))


def select_one(terminal_data, reset_data, done):
    # done is scalar inside vmap; terminal observation is saved before this call.
    return terminal_data.where(done, reset_data)


step_batch = jax.jit(jax.vmap(step_one, in_axes=(None, 0, 0)))
select_batch = jax.jit(jax.vmap(select_one, in_axes=(0, 0, 0)))
```

`Data.where` 在 JAX 分支直接对 leaves 做 `jp.where(done, other, self)`，没有把 `(B,)` mask 自动 reshape 为每个字段适合的 rank。直接在整棵 batched Data 上传 `(B,)`，遇到 `(B,nq)` 时可能报广播错误；若 B 恰好等于 nq，还可能沿错轴选择而不报错。在 `vmap` 内使用单世界 scalar done 可以避免这一层广播误解。Warp 分支另有共享池字段保留规则，因此该 JAX 片段不是对两个后端全部内部字段的通用 reset。[where实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/types.py#L1176-L1206)。

## 4. JIT、dtype 和同步分别解决什么

JIT 跟踪函数、构建并缓存编译结果。Python side effect 可能只在跟踪时发生；shape、dtype 或静态参数改变可以产生新编译。若每次循环都新建 lambda 并 JIT，会损害缓存复用；应把固定计算函数放在循环外。首次编译耗时与稳定调用不同，二者不能混成“单步耗时”。[纯函数/跟踪](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/docs/jit-compilation.md#L56-L73)、[编译与缓存](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/docs/jit-compilation.md#L123-L136)、[静态参数和缓存](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/docs/jit-compilation.md#L197-L248)。

JAX 默认 `jax_enable_x64=False`，默认数值数组通常是32位；原生 CPU模型是FP64不保证 `mjx.make_data` 也为FP64。X64设置应在创建数组/编译前作为全局配置记录。MJX Warp 的 `make_data` 还明确把 qpos 等转换为 float32，不能靠 JAX X64 开关改变所有后端精度。[JAX dtype说明](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/docs/default_dtypes.md#L19-L82)、[Warp初始化](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L755-L812)。

`jax.device_put` 可以异步提交传输，内存是否可 alias/donate 还有自己的参数；不要把“Python函数返回”当成设备已经算完。`block_until_ready` 等待结果就绪；`device_get` 将数组取到 host，包含另一个数据移动边界。启用 donation 后被捐献的 buffer 不应继续作为有效旧值使用。[put](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L2643-L2696)、[get](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L2894-L2937)、[等待](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L3096-L3135)、[donation](https://github.com/jax-ml/jax/blob/94233144f5469af28c065aa4263a6849338eeaa1/jax/_src/api.py#L214-L231)。这里只解释边界，没有以异步返回时间报告性能。

## 5. host/device 两份模型不会自动同步

典型的数据流是 native model → `put_model` → 设备 model；native data → `put_data`，或按后端的 `make_data` 创建设备 data；然后在设备上连续推进，仅按需要读取日志或显示样本。修改 host 的 `body_mass` 不会神奇改变已上传的 device model。[模型上传](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L537-L581)。

`get_data_into` 会先 `jax.device_get(data)`，再重建原生数据字段；`get_data` 还会分配一份或多份原生 `MjData`。每步把整个 B 世界取回只为查看一个标量，会把传输、分配与物理计算耦合起来。日志应挑所需数组，viewer选择一个世界并注明采样阶段；“没有打开窗口”也不等于没有读回。[设备到原生](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L1596-L1645)。

`mjx.get_state/set_state` 提供与原生 state mask 对应的打包接口，但实现对选中字段做 flatten。单世界契约下正确的 Nstate，不能直接套到整棵 batched Data 后再假设每行仍为独立状态；按世界用 `vmap` 处理。State mask 的名字相同也不能补上某后端没有实现的物理或隐状态。[state API](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L1712-L1812)。

## 6. Warp 的批量池和图模式

MJX Warp 通过 custom-vmap 规则把批量维交给 FFI；内核按 world ID 访问数据。部分 contact 缓冲是共享池，不是简单的 `(B,...)` 独立叶子，`Data.__getitem__` 和 `where` 都必须考虑不参与普通 vmap 的字段。[step FFI](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/warp/forward.py#L5550-L5560)、[批量参数转换](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/warp/ffi.py#L411-L475)、[池字段](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/warp/types.py#L552-L580)。

对 vendored Warp 直接模型，`batch_sizes` 只接受支持批量的字段；默认前导长度为1。内核常以 `worldid % field.shape[0]` 选择参数，故长度1为共享参数，长度B可为逐世界参数，更短的参数库会循环复用。它不表示可以混放任意拓扑机器人。[分配规则](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/io.py#L215-L240)、[实际索引](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/forward.py#L60-L82)。

| 容量 | 实际范围 | 不能混淆的含义 |
|---|---|---|
| `naconmax` | 所有世界的 contact 总池 | 不是每世界都独享同样数量 |
| `nconmax`（vendored接口） | 用于估算总池，通常乘 nworld | 某世界可超过此数，只要总池容得下 |
| `naccdmax` | 所有世界 CCD 池 | 需与 contact 总容量匹配 |
| `njmax` | 每世界约束容量 | 增大contact池不自动增大它 |
| `nvmax`（MJX接口） | 每世界 active DOF 容量 | 与总世界数不同 |

容量是执行有效性条件。溢出或截断不能解释成“这个世界没有接触”，更不能为了让结果好看而从记录中去掉 warning。[MJX make_data参数](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L862-L919)、[vendored容量定义](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/third_party/mujoco_warp/_src/io.py#L1655-L1751)。MJX Warp 的 `make_data` 还要求原生 `MjModel` 来创建底层数据，并非所有后端都允许只拿 `mjx.Model` 初始化。

Graph模式也不同：WARP模式可能因XLA buffer地址变化重新捕获；WARP_STAGED使用稳定staging buffer并发生复制；WARP_STAGED_EX把相关复制放到图捕获之外。选择由实际设备、内存和调用模式决定；“使用graph”不等于无复制。[图模式说明](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/doc/mjx.rst#L155-L224)。

## 7. 支持矩阵要读到实际执行分支

本版 JAX 上传路径明确拒绝 flex，并对部分 contact sensor、碰撞和 margin 组合有限制；PGS不在该后端求解器枚举中。`IntegratorType` 即使含DISCRETE，JAX `step` 当前只分派Euler/RK4/implicitfast，其他值报错。不能把CPU课程五类积分器照搬到MJX。[上传检查](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/io.py#L310-L439)、[枚举](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/types.py#L125-L139)、[solver枚举](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/types.py#L214-L223)、[执行分支](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L515-L530)。

另一个版本陷阱是 history：JAX Data 有 history数组，也能通过state接口复制；但本树 `_advance` 不推进原生history，actuation直接使用ctrl，sensor路径也不实现CPU3.15的delay/interval机制。**有同名存储不证明有同样时序。** 需按实际后端设计观测与回放，不能给MJX轨迹套CPUhistory契约。[advance](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L373-L398)、[actuation](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/forward.py#L150-L169)、[sensor实现](https://github.com/google-deepmind/mujoco/blob/9ea3cdfcae93bf2cc4dc0e1a1627c5a39a1e06e5/mjx/mujoco/mjx/_src/sensor.py#L54-L86)。

## 8. 带答案阅读练习

1. **CPU使用FP64，MJX就相同吗？** 不保证；记录JAX X64与实际array dtype，Warp还存在明确float32转换。
2. **`vmap(step)` 同时推进多个时刻吗？** 它映射独立batch轴；一条轨迹后续时刻依赖前一状态。
3. **模型参数上传后改host质量，device模型会改变吗？** 不会自动同步，需按后端更新参数及派生量。
4. **给 batched Data.where 传 `(B,)` done为什么危险？** leaf rank各异，NumPy/JAX从末轴广播；可能错轴或失败。示例在vmap内用scalar。
5. **模型包含DISCRETE枚举，说明JAX后端支持吗？** 不说明；还要核对step分派，本版会拒绝该路径。
6. **需要渲染一个世界，为什么避免每步get_data整个batch？** 整棵data会device_get并重建CPU对象；只取所需世界/数组更能明确传输与资源边界，但实际性能仍需测量。
7. **nconmax=100意味着每世界最多100接触吗？** vendored Warp接口中它用于总池预算；硬边界要看naconmax和其他容量。
8. **MJX包依赖里没有锁JAX版本，这份JAX0.7.2源码引用能当安装锁吗？** 不能，它只是本课固定API阅读基线，兼容性与运行环境另需验证。

下一课：[学习与随机化](learning-and-randomization.md)。完整插件、flex/IPC及后端内部扩展仍由E6展开。
