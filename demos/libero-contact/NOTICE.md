# LIBERO evidence provenance / 来源说明

This evidence package contains DexLab observations and scores, source demonstration actions and initial/reference state arrays for the selected cream-cheese task, and derived native model XML. It does not include the original HDF5 file, camera observations from that file, or upstream mesh/texture binaries. Model XML asset locations are replaced by portable source-relative identifiers; candidate parameter changes and native/export hashes are recorded separately. All comparisons retain the original task predicate.

证据包包含 DexLab 新采集的观测与评分、所选 cream-cheese 示范的动作及初始／参考状态数组，以及派生模型 XML。未重发原始 HDF5 文件、其中的相机观测或上游网格／纹理二进制。XML 仅把资产位置改为可移植的上游相对标识；候选参数变化、原始及导出哈希单独保存。源示范数组与新仿真观测不能混同。

- **LIBERO:** [Lifelong Robot Learning source](https://github.com/Lifelong-Robot-Learning/LIBERO/tree/8f1084e3132a39270c3a13ebe37270a43ece2a01), MIT; original copyright and license in `licenses/LIBERO-MIT.txt`.
- **robosuite 1.4.0:** [ARISE Initiative source](https://github.com/ARISE-Initiative/robosuite/tree/v1.4.0), MIT; original copyright and license in `licenses/robosuite-MIT.txt`.
- **LIBERO Datasets:** [yifengzhu-hf dataset](https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/tree/f13aa24a3da8c43c7225569f28c562979fa0e35a), revision `f13aa24a3da8c43c7225569f28c562979fa0e35a`; the pinned dataset card declares Apache-2.0. The card and Apache-2.0 text are included in `licenses/dataset-card.md` and `licenses/Apache-2.0.txt`. This card label differs from the pinned source README declaration described below. Only selected action/state arrays are retained; the manifest identifies the original task file and SHA-256.

## Dataset declarations / 数据集声明

The [pinned LIBERO source README](https://github.com/Lifelong-Robot-Learning/LIBERO/blob/8f1084e3132a39270c3a13ebe37270a43ece2a01/README.md#license) lists the datasets as **CC BY 4.0**, while the [pinned Hugging Face card](https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/blob/f13aa24a3da8c43c7225569f28c562979fa0e35a/README.md) declares **Apache-2.0**. These are two upstream declarations, not evidence that either overrides the other or that dual licensing has been established. The `dataset_license` field in `dataset-index.json` records the card label only. This package preserves both source links and does not relicense upstream data or assets. The differing declarations and any clarification remain tracked in [#185](https://github.com/huangkiki/Dexlab/issues/185).

冻结版本的 LIBERO 源码 README 将数据集列为 **CC BY 4.0**，同一批数据的固定 Hugging Face 数据卡声明 **Apache-2.0**。本包并列保留两项上游声明，不据此认定其中一项覆盖另一项或已经建立双重许可。`dataset-index.json` 的 `dataset_license` 只记录数据卡标签，不代表这一差异已经解决；上游数据与资产不因收录而改变许可。来源差异及后续澄清由 [#185](https://github.com/huangkiki/Dexlab/issues/185) 跟踪。

LIBERO attribution: Bo Liu, Yifeng Zhu, Chongkai Gao, Yihao Feng, Qiang Liu, Yuke Zhu and Peter Stone, [LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning](https://arxiv.org/abs/2306.03310). DexLab's full-task input inventory records all 130 task/file identities and derived demonstration counts. Downloaded official HDF5 files remain local inputs and are not added to this repository; this inventory does not change the scope of the historical cream-cheese evidence package described above.

LIBERO 作者及成果见上述引用。全任务输入清单保存 130 项任务／文件身份和派生示范计数；下载的官方 HDF5 是本地输入，不加入本仓库。该清单不改写上文历史 cream-cheese 证据包的内容范围。

DexLab source is provided under the repository Apache-2.0 license; the complete license text is included above.

Third-party materials retain their original licenses. These notices do not relicense upstream assets. DexLab's analysis, configuration changes and rendered views are derived work; neither the authors nor this package claim official LIBERO benchmark scores or upstream endorsement.
