# 资产来源

[English](ASSETS.md) | [简体中文](ASSETS.zh-CN.md)

根目录的 [Apache-2.0 许可证](../LICENSE)适用于 DexLab 项目代码。第三方资产保留原有条款，本项目不对其重新授权。演示图片和视频包含这些资产，并不因此赋予底层模型或纹理 Apache-2.0 许可。

| 资产 | 来源与本地修改 | 署名与条款 |
|---|---|---|
| OpenArm V20 与 Wuji Hand 2 Beta1 | [Project SuperDex](https://github.com/unilabsim/project_superdex)，参考提交 `f216dace36464d70f224caa4253074ec365ed14f` | OpenArm：[Apache-2.0](asset-licenses/openarm-arm-LICENSE)、[声明](asset-licenses/openarm-arm-NOTICE)；Wuji：[MIT](asset-licenses/wuji-hand-LICENSE)、[声明](asset-licenses/wuji-hand-NOTICE)。下载包中保留原始声明 |
| 机器人安装与显示几何 | 裁剪的 OpenArm 安装板、固定安装变换和用于显示的 OBJ 转换；无 ZGWS 躯干或腿部 | 本地修改记录在 [NOTICE](../NOTICE) 中 |
| 苹果与梗 | 由 NVIDIA Isaac Sim 5.1 的 `Apple.usd` 和纹理转换，包含碰撞网格与刚体 SDF 输入 | [原始 URL 和 SHA256 哈希](../demos/apple-stem-grasp/assets/apple/sources.json)、[Isaac Sim 许可说明](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/common/legal.html) |

参考机器人与苹果的文件哈希记录在 [asset-sha256.json](../demos/apple-stem-grasp/evidence/asset-sha256.json) 中。SuperDex 和 MuJoCo 从官方 PyPI 发行包安装，DexLab 不分发它们的原生二进制。MuJoCo 提供其中一个动力学后端，并负责两个后端的渲染；两个引擎均无需修改源码。

## 分发

大型机器人资产从 `apple-stem-assets-v1` GitHub Release 下载。压缩包保留经验证的原始文件以及许可和署名声明。[assets.json](../demos/apple-stem-grasp/assets.json) 固定压缩包 SHA-256 和各安装文件的哈希。

Release 不镜像苹果纹理。下载器仅按原始 URL 和 SHA-256 直接从 NVIDIA 获取本演示需要的基础色纹理。NVIDIA 来源条款继续适用；来源记录不等于取得再分发授权。现有小型任务专用派生苹果网格保留在 Git 中，未因资产包迁移而改变。

## 语言与原始声明

项目文档维护英文和简体中文版本。原始许可证与第三方声明保留原文，翻译说明不替代原始条款。根目录 [NOTICE](../NOTICE) 记录项目署名和资产本地修改。
