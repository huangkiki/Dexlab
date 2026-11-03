# Local OVRTX rendering / 本机 RTX 渲染

The claw machine can stream its live MuJoCo poses to **NVIDIA OVRTX** on a local RTX GPU. Physics, controls, scoring and solver comparison remain in the browser. The service imports the actual textured scene, renders the requested snapshot, and returns one timestamped image containing every solver view. It never advances or edits physics. There is at most one frame in flight.

抓娃娃机可以把实时 MuJoCo 位姿发给本机 **NVIDIA OVRTX**。浏览器继续负责物理、操作、计分和求解器对比；服务只导入带贴图的实际场景并返回画面。三路画面使用同一个请求中的状态和时间戳，不积压旧帧，也不修改物理状态。

## Start / 启动

Use an NVIDIA RTX GPU and a driver supported by [OVRTX](https://nvidia-omniverse.github.io/ovrtx/). The optional NVIDIA runtime is separately licensed and is not included in this repository. Python 3.12 is the tested interpreter. Reuse a compatible environment when available.

需要 NVIDIA RTX 显卡和 [OVRTX 支持的驱动](https://nvidia-omniverse.github.io/ovrtx/)。NVIDIA 运行库使用独立许可，不随仓库分发；这里使用 Python 3.12。有兼容环境时可以直接复用。

```bash
python3.12 -m venv /path/to/ovrtx-env
/path/to/ovrtx-env/bin/pip install -r web/ovrtx/requirements.txt
/path/to/ovrtx-env/bin/python web/ovrtx/server.py --work-dir /path/to/render-cache
```

In another terminal / 另开终端：

```bash
cd web
npm ci
npm run dev -- --host 127.0.0.1 --port 8877
```

Open `http://127.0.0.1:8877/lab/?lang=en&renderer=ovrtx` (Chinese: `lang=zh`). The **Renderer** control switches between WebGL and OVRTX. The bridge only binds to loopback port 8879 and accepts browser origins on local ports 8877/8878. It serves one client at a time. Stop it with Ctrl+C to release the GPU.

打开 `http://127.0.0.1:8877/lab/?lang=zh&renderer=ovrtx`。**画面渲染**选项可切换 WebGL / OVRTX。服务只监听本机 8879 端口，只接受本机 8877/8878 页面的连接，一次服务一个页面；Ctrl+C 停止后释放显卡。

## What the mode means / 渲染范围

- OVRTX uses real-time path tracing, textured triangle meshes, nonmetallic rough fabric, metallic claw parts, area lights, and native HDR output followed by fixed exposure and ACES/sRGB display mapping. This is an artistic material setup, not measured textile scattering or deformable fur. Both viewers use rough, nonmetallic PBR fabric with embedded base-color textures.
- All three solver views are assembled before a frame is displayed. The timestamp is the simulated time of that image; render time is shown separately. It is not simulation throughput or an engine accuracy score.
- Public GitHub Pages runs WebGL. OVRTX needs the local native service; Pages does not host GPUs. A disconnected or stale renderer is explicitly labeled and the live WebGL view remains usable.
- OVRTX 使用实时路径追踪、带贴图的三角网格、粗糙非金属织物、金属夹爪和面光源。原生 HDR 经固定曝光、ACES/sRGB 转为显示画面。这是美术材质，不是实测布料散射、毛发或软体仿真；两种渲染器都使用带内嵌颜色贴图的粗糙非金属 PBR 材质。
- 三路全部渲染完才一起显示；画面时间戳和渲染耗时分别标注，不能当成仿真吞吐或引擎准确率。
- 公共 GitHub Pages 使用 WebGL，本机服务才提供 OVRTX。连接失败或画面过期会明确提示，并继续显示 WebGL。

`latest-1-views.jpg`, `latest-3-views.jpg` and `latest.json` in the work directory are diagnostic readbacks, overwritten periodically. Temporary scene conversion files are removed when the client disconnects. / 工作目录的这些文件是周期覆盖的诊断画面；断开连接后会清理临时场景转换文件。
