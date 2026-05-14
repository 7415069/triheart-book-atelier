#!/bin/bash
# build_universal_pex.sh
# 使用 uv 创建隔离干净环境打包，避免当前 venv 污染，并锁定 Python 版本

set -e  # 遇到错误立即退出

cd "$(dirname "$0")" || exit

# ────────────────────────────────────────────
# 配置区 — 改这里即可
# ────────────────────────────────────────────
APP_NAME="thba"
OUTPUT_HOME="$(pwd)/dist"
OUTPUT_PEX="${OUTPUT_HOME}/${APP_NAME}_local.pex"
BUILD_DIR="/tmp/pex_tmp_${APP_NAME}_$$"
CLEAN_VENV_DIR="/tmp/pex_clean_venv_${APP_NAME}_$$"

# ★ 只需改这一行来切换 Python 版本（如 3.10 / 3.11 / 3.12）
PYTHON_VERSION="3.11"

# ────────────────────────────────────────────
# 检查 uv 是否安装
# ────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
  echo "✗ 未找到 uv，请先安装："
  echo ""
  echo "  Linux / macOS : curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "  Windows       : powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
  echo "  pip           : pip install uv"
  echo ""
  echo "安装后重新执行本脚本即可。"
  exit 1
fi

echo ">>> uv 版本 : $(uv --version)"

# ────────────────────────────────────────────
# 清理旧产物
# ────────────────────────────────────────────
rm -rf "${BUILD_DIR}" "${CLEAN_VENV_DIR}"
mkdir -p "${BUILD_DIR}"
rm -rf "${OUTPUT_HOME}"
mkdir -p "${OUTPUT_HOME}"

# ────────────────────────────────────────────
# 用 uv 创建指定版本的干净 venv
# uv 会自动下载对应 Python 版本（如本机没有）
# ────────────────────────────────────────────
echo ">>> 正在创建隔离干净环境（Python ${PYTHON_VERSION}）..."
uv venv --python "${PYTHON_VERSION}" "${CLEAN_VENV_DIR}"
source "${CLEAN_VENV_DIR}/bin/activate"

ACTUAL_VERSION=$(python --version 2>&1)
echo ">>> 实际解释器 : ${ACTUAL_VERSION}"

echo ">>> 正在安装 pex..."
uv pip install pex

echo ">>> pex 版本 : $(pex --version)"

# ────────────────────────────────────────────
# 核心打包命令
#
# 版本控制关键参数：
#   --python                  构建时使用的解释器（明确路径）
#   --python-shebang          产物 shebang 行（运行时用哪个 python）
#   --interpreter-constraint  运行时版本门控，不符合直接报错
#
# 隔离 / 体积关键参数：
#   --no-inherit-path         运行时不继承宿主 sys.path（防污染最关键）
#   --resolver-version        现代 pip resolver，依赖解析更准确
#   --no-compile              不打包 .pyc，减小体积 10-20%
# ────────────────────────────────────────────
PYTHON_BIN_PATH="$(which python)"
echo ">>> 正在打包（Python ${PYTHON_VERSION}，隔离环境）..."

# 1. 先创建一个临时源码目录，只放代码，不放杂物
CLEAN_SRC_DIR="${BUILD_DIR}/src_only"
mkdir -p "${CLEAN_SRC_DIR}"

echo ">>> 正在提取纯净业务代码..."
cp -r .env app main.py "${CLEAN_SRC_DIR}/"

echo ">>> 正在从隔离环境启动打包..."

pex \
  -v \
  -r requirements.txt \
  -o "${OUTPUT_PEX}" \
  --sources-directory "${CLEAN_SRC_DIR}" \
  --entry-point main \
  --python="${PYTHON_BIN_PATH}" \
  --python-shebang="/usr/bin/env python${PYTHON_VERSION}" \
  --interpreter-constraint="CPython==${PYTHON_VERSION}.*" \
  --resolver-version pip-2020-resolver \
  --no-compile \
  --strip-pex-env \
  --tmpdir="${BUILD_DIR}"

# 干净 venv 使命完成，删除
deactivate
rm -rf "${CLEAN_VENV_DIR}" "${BUILD_DIR}"

# ────────────────────────────────────────────
# 验证产物
# ────────────────────────────────────────────
if [ ! -f "${OUTPUT_PEX}" ]; then
  echo "✗ 打包失败，产物不存在。"
  exit 1
fi

PEX_SIZE=$(du -sh "${OUTPUT_PEX}" | cut -f1)
echo "================================================"
echo "✓ 打包成功！"
echo "  Python 版本 : ${ACTUAL_VERSION}"
echo "  产物路径    : ${OUTPUT_PEX}"
echo "  产物大小    : ${PEX_SIZE}"
echo "================================================"

# ────────────────────────────────────────────
# 整理发布包
# ────────────────────────────────────────────
RELEASE_DATE=$(date +%Y%m%d)
RELEASE_DIR="${OUTPUT_HOME}/release_${APP_NAME}_${RELEASE_DATE}"
ZIP_NAME="release_${APP_NAME}_${RELEASE_DATE}.zip"

echo ">>> 正在整理发布包到: ${RELEASE_DIR} ..."
mkdir -p "${RELEASE_DIR}"/{bin,lib,var}

# 1. 复制 PEX 可执行文件
PEX_FILENAME="${APP_NAME}_local.pex"
cp "${OUTPUT_PEX}" "${RELEASE_DIR}/lib/"

# 2. 复制静态资源和配置文件
cp -r fixtures static "${RELEASE_DIR}/" 2>/dev/null \
  || echo "警告: 静态目录 (fixtures/static) 不存在，跳过。"
cp .env "${RELEASE_DIR}/" 2>/dev/null \
  || echo "警告: .env 文件不存在，跳过。"

# 3. 生成启动脚本（自动加载 .env）
cat > "${RELEASE_DIR}/bin/start.sh" << STARTEOF
#!/bin/bash
# 自动加载 .env 并启动 ${APP_NAME}
# 需要目标机器安装 Python ${PYTHON_VERSION}
SCRIPT_DIR="\$(cd "\$(dirname "\$0")/.." && pwd)"
if [ -f "\${SCRIPT_DIR}/.env" ]; then
  set -a && source "\${SCRIPT_DIR}/.env" && set +a
fi
exec python${PYTHON_VERSION} "\${SCRIPT_DIR}/lib/${PEX_FILENAME}" "\$@"
STARTEOF
chmod +x "${RELEASE_DIR}/bin/start.sh"

# 4. 生成版本信息文件，方便运维核查
cat > "${RELEASE_DIR}/BUILD_INFO" << INFOEOF
App        : ${APP_NAME}
Build Date : $(date '+%Y-%m-%d %H:%M:%S')
Python     : ${ACTUAL_VERSION}
Constraint : CPython==${PYTHON_VERSION}.*
PEX Size   : ${PEX_SIZE}
INFOEOF

# 5. 压缩
echo ">>> 正在生成 ZIP 压缩包..."
cd "${OUTPUT_HOME}" || exit
zip -r "${ZIP_NAME}" "$(basename "${RELEASE_DIR}")"

if [ -f "${ZIP_NAME}" ]; then
  ZIP_SIZE=$(du -sh "${ZIP_NAME}" | cut -f1)
  echo "================================================"
  echo "✓ 所有发布任务完成！"
  echo "  Python 版本 : ${ACTUAL_VERSION}"
  echo "  PEX 大小    : ${PEX_SIZE}"
  echo "  ZIP 路径    : ${OUTPUT_HOME}/${ZIP_NAME}"
  echo "  ZIP 大小    : ${ZIP_SIZE}"
  echo "================================================"
else
  echo "✗ ZIP 压缩失败，请确认系统是否安装了 'zip' 命令。"
  exit 1
fi