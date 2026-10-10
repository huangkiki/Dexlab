# LIBERO evidence provenance / 来源说明

This evidence package contains DexLab observations and scores, source demonstration actions and initial/reference state arrays for the selected cream-cheese task, and derived native model XML. It does not include the original HDF5 file, camera observations from that file, or upstream mesh/texture binaries. Model XML asset locations are replaced by portable source-relative identifiers; candidate parameter changes and native/export hashes are recorded separately. All comparisons retain the original task predicate.

证据包包含 DexLab 新采集的观测与评分、所选 cream-cheese 示范的动作及初始／参考状态数组，以及派生模型 XML。未重发原始 HDF5 文件、其中的相机观测或上游网格／纹理二进制。XML 仅把资产位置改为可移植的上游相对标识；候选参数变化、原始及导出哈希单独保存。源示范数组与新仿真观测不能混同。

- **LIBERO:** [Lifelong Robot Learning source](https://github.com/Lifelong-Robot-Learning/LIBERO/tree/8f1084e3132a39270c3a13ebe37270a43ece2a01), MIT; original copyright and license in `licenses/LIBERO-MIT.txt`.
- **robosuite 1.4.0:** [ARISE Initiative source](https://github.com/ARISE-Initiative/robosuite/tree/v1.4.0), MIT; original copyright and license in `licenses/robosuite-MIT.txt`.
- **LIBERO Datasets:** [yifengzhu-hf dataset](https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/tree/f13aa24a3da8c43c7225569f28c562979fa0e35a), revision `f13aa24a3da8c43c7225569f28c562979fa0e35a`; the pinned dataset card declares Apache-2.0. The card and full license are included in `licenses/dataset-card.md` and `licenses/Apache-2.0.txt`. Only selected action/state arrays are retained; the manifest identifies the original task file and SHA-256.

DexLab source is provided under the repository Apache-2.0 license; the complete license text is included above.

Third-party materials retain their original licenses. These notices do not relicense upstream assets. DexLab's analysis, configuration changes and rendered views are derived work; neither the authors nor this package claim official LIBERO benchmark scores or upstream endorsement.
