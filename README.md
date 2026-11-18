# dsh-cad-workflow

> 把模糊的 3D 建模想法，通过「先定大方向、后逐步细化」的逐级确认流程，收敛成可交给拓竹（Bambu Lab）H2D 打印的模型——以成熟建模软件为执行引擎、DSH Agent 为编排大脑、规格文件为唯一事实源。

一套给 [DeepSeek Harness (DSH)](https://github.com/deepseek-ai) 用的 **CAD 建模协作工作流包**：6 个 skill + 2 个 MCP bundle + 5 个路径无关脚本 + 规格/确认门模板。双引擎：**Blender**（造型件）/ **FreeCAD**（功能件、精确 B-rep + STEP）。支持从带尺寸标注的**三视图工程图**精确重建 3D 模型，含真实 CAD **DWG 逆向**实战（见 [三视图原型](docs/三视图重建原型.md) 与 [DWG 逆向实战](docs/DWG三视图逆向实战.md)）。

---

## 0. 先看结论：重启 / 跨工作区是否可用？

这是本包设计的核心约束，直接回答：

| 组件 | 装在哪 | DSH 重启后 | 换工作区 | 备注 |
|---|---|---|---|---|
| 6 个 skill | `~/.dsh/skills/<name>/SKILL.md`（全局） | ✅ 保留 | ✅ 可用 | 与工作区无关 |
| 2 个 MCP bundle | `~/.dsh/profiles/<profile>/node_modules/@local/`（profile 级） | ✅ 保留、自动拉起 | ✅ 可用 | 只依赖本机软件路径 |
| 脚本 / 模板 / 证据 | 本包内，路径无关（相对脚本定位 + 环境变量） | ✅ | ✅ 产物写到当前位置 | 无硬编码旧工作区 |
| Blender MCP 服务端 | Blender GUI 插件（localhost:9876） | ⚠️ 需手动点一次 Start Server | ✅ | 唯一需重启后手动的步骤 |
| FreeCAD MCP 实时服务端 | FreeCAD GUI addon（127.0.0.1:9875） | ⚠️ 需手动点一次 Start RPC Server | ✅ | headless 路线无需此步 |
| FreeCAD headless（推荐路线） | `FreeCADCmd.exe` 独立进程 | ✅ 无需 GUI | ✅ | 功能件日常走这条 |

**一句话**：skill、bundle、脚本全部持久且跨工作区可用；只有两个 GUI 的「Start Server」按钮在重启软件后需要各点一次（headless 路线可完全绕开）。

---

## 1. 能做什么

- **逐级收敛**：L0 大方向 → L1 结构分解 → L2 特征 → L3 参数，每层经你确认才深入，可回退、有检查点。
- **双引擎路由**：造型/手办 → Blender；功能件/装配/公差 → FreeCAD。
- **三视图重建**：带尺寸标注的工程图 / 真实 CAD DWG → 读尺寸 → params → 精确 3D（`cad-three-view`，见 [原型](docs/三视图重建原型.md) 与 [DWG 逆向实战](docs/DWG三视图逆向实战.md)）。
- **多通道建模**：Blender MCP 实时 / bpy 后台；FreeCAD headless 代码即模型（推荐）/ MCP headless / MCP 实时。
- **打印性校验**：水密、法线朝向、体积为正三道自动门槛（trimesh），壁厚交人工核验，绝不伪造 PASS。
- **可打印交付**：STL / 3MF / FreeCAD 独有的 STEP，最终进 Bambu Studio 切片送 H2D。

## 2. 目录结构

```
dsh-cad-workflow/
├── README.md                     ← 本文件（使用手册入口）
├── LICENSE                       MIT
├── docs/
│   ├── 普适化使用方案.md          安装、跨工作区、换机器、多用户
│   ├── 持久化与迁移.md             重启/迁移行为与故障排查
│   ├── 架构说明.md                 六层栈、确认门、状态机
│   ├── 三视图重建原型.md            带尺寸三视图→3D 的最小原型与实测结果
│   └── DWG三视图逆向实战.md         真实 CAD DWG → 3D 的完整逆向案例（part.dwg）
├── skills/                       6 个 skill 源（安装到 ~/.dsh/skills/）
│   ├── cad-spec-driver/
│   ├── cad-confirm-gate/
│   ├── cad-blender-ops/
│   ├── cad-freecad-ops/
│   ├── cad-verify/
│   └── cad-three-view/             三视图工程图→参数→精确 3D
├── bundles/                      2 个 DSH MCP bundle（配置式，无需入口文件）
│   ├── blender-mcp/
│   └── freecad-mcp/
├── scripts/                      路径无关的建模/校验 runner
│   ├── build_from_params.py          Blender 后台 spec→STL
│   ├── build_freecad_from_params.py  FreeCAD headless spec→STL+STEP
│   ├── build_mobius_freecad.py       FreeCAD 莫比乌斯生成器（示例）
│   ├── mobius_ring.py                Blender 莫比乌斯生成器（示例）
│   └── verify_stl.py                 trimesh 打印性校验
├── templates/                    spec / params / 确认门协议模板
│   ├── model-spec.template.md
│   ├── params.template.json
│   └── confirm-gate-protocol.md
├── examples/                     可直接跑的示例
│   ├── example-spec.md
│   ├── example-params.json
│   ├── washer-test.json
│   └── three-view/                三视图重建示例
│       ├── flange-3view.*         带尺寸 SVG + spec + params（台阶法兰）
│       └── dwg-case/              真实 DWG 逆向案例（转换/解析/校验脚本 + spec + params）
├── my-env.example.json           本机路径配置模板（复制为 my-env.json 填写）
└── install/
    ├── configure.ps1             用 my-env.json 渲染 bundle 里的本机绝对路径
    ├── install.ps1               安装 skill（复制）+ bundle（dsh plugin add）
    └── doctor.ps1                环境体检/安装校验
```

> `my-env.json`、`_rendered/`、`output/` 已在 `.gitignore` 中（含个人路径，不入库）。

## 3. 快速开始（Windows）

前置：DSH、Blender（任意近期版）、FreeCAD（可选，功能件需要）、Python + `trimesh`、uv/uvx。

```powershell
# 1) 克隆本包（放到任意位置，无硬编码路径）
git clone <你的仓库URL> dsh-cad-workflow
cd dsh-cad-workflow

# 2) 填本机路径：复制模板后按你的机器改（uvx / FreeCADCmd / DSH_HOME / profile）
copy my-env.example.json my-env.json
notepad my-env.json

# 3) 体检：确认源文件、路径、trimesh 依赖
powershell -ExecutionPolicy Bypass -File install\doctor.ps1

# 4) 渲染 bundle（把本机绝对路径写进 cordis.patch.yml 模板）
powershell -ExecutionPolicy Bypass -File install\configure.ps1

# 5) 安装：skill 复制到全局；bundle 经 `dsh plugin add` 注册（自动建 link/Junction）
powershell -ExecutionPolicy Bypass -File install\install.ps1

# 6) 完全退出并重启 DSH（skill/bundle 重新加载）
#    需要 MCP 实时时，在 Blender GUI 启用 "Interface: MCP for Blender" 插件并 Start MCP Server
#    FreeCAD headless 路线无需 GUI。
#    验证：DSH 里调用 mcp__blender__get_addon_status / mcp__freecad__get_rpc_status
```

详细分步、Linux/macOS、换机器、多工作区隔离见 [docs/普适化使用方案.md](docs/普适化使用方案.md)。

## 4. 最小闭环演示

```
你：我想做一个带孔垫片，外径30、孔6.4、厚3mm
→ cad-spec-driver 建 model-spec.md 的 L0-L3，先问你 L0 大方向
→ 你确认 L0 → 锁层 → 进 L1 … 每层经确认门
→ 路由到功能件 → cad-freecad-ops（headless）生成 STL+STEP + 证据
→ cad-verify 校验 → AUTO_PASS
→ 导入 Bambu Studio 切片 → H2D
```

命令行直接跑（不经过 DSH 也能验证）：

```powershell
$env:CAD_PARAMS = ".\examples\washer-test.json"
$env:CAD_OUT    = ".\output"
& "D:\Program Files\FreeCAD 27.1\bin\FreeCADCmd.exe" ".\scripts\build_freecad_from_params.py"
python .\scripts\verify_stl.py .\output\washer-test-freecad.stl 0.4
```

## 5. 设计原则

1. **事实源唯一**：`model-spec.md` + `params.json` 是模型真相；工程文件是派生。
2. **确认门硬规则**：没有用户确认，不进下一层。
3. **可回退**：每锁一层存检查点，推翻已锁层显式回退。
4. **证据优先**：几何真伪用数据（面数/非流形边/体积）说话，不用"看起来对"。
5. **路径无关**：脚本相对自身定位，参数走环境变量/CLI，配置集中校准——这是跨工作区/重启可用的基础。
6. **不伪造 PASS**：自动能测的才自动判，测不了的（壁厚）明确标注 MANUAL_REQUIRED。

## 6. 许可

MIT。第三方 MCP 组件（blender-mcp / freecad-mcp addon）版权归各自作者，本包只提供配置与工作流，不修改其源码。
