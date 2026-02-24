#!/bin/bash
# build_universal_pex.sh
cd $(dirname "$0") || exit

if ! command -v pex &> /dev/null
then
    echo "pex 未安装，正在尝试安装..."
    pip install pex
else
    echo "pex 已安装。"
fi

OUTPUT_HOME="$(pwd)/dist"
APP_NAME="thba"
OUTPUT_PEX="${OUTPUT_HOME}/${APP_NAME}_local.pex"
BUILD_DIR="/home/huangyun/pex_tmp_local"
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

rm -rf ${OUTPUT_HOME}
mkdir -p ${OUTPUT_HOME}

echo "正在将本地代码与依赖合并打包..."

# 核心修改点：
# 1. 删掉 -c main.py
# 2. 增加 . 表示包含当前目录下的所有 .py 文件
# 3. 增加 --entry-point main (假设你的启动逻辑在 main.py 的 if __name__ == "__main__" 里)
#    或者如果不确定入口，可以先不加入口，运行用 python3 xxx.pex main.py

pex -v \
    -r requirements.txt \
    -o "${OUTPUT_PEX}" \
    -D . \
    --entry-point main \
    --python-shebang='/usr/bin/env python3' \
    #--disable-cache \
    --tmpdir="${BUILD_DIR}"

if [ -f "${OUTPUT_PEX}" ]; then
    echo "================================================"
    echo "打包成功！祝贺！"
    echo "产物路径: ${OUTPUT_PEX}"
    echo "================================================"
else
    echo "最后一步打包归档失败。"
    exit 1
fi


RELEASE_DIR="$(pwd)/dist/release_${APP_NAME}_$(date +%Y%m%d)"
ZIP_NAME="release_${APP_NAME}_$(date +%Y%m%d).zip"

echo "正在整理发布包资源到: $RELEASE_DIR ..."
mkdir -p "${RELEASE_DIR}"/{bin,lib,var}

# 1. 复制 PEX 可执行文件
cp "${OUTPUT_PEX}" "${RELEASE_DIR}"/lib/

# 2. 复制静态资源和配置文件
# 注意：这里使用 cp -r 的时候要确保源目录存在
cp -r fixtures static "${RELEASE_DIR}/" 2>/dev/null || echo "警告: 静态目录不存在，跳过。"
cp .env "${RELEASE_DIR}/" 2>/dev/null || echo "警告: .env 文件不存在，跳过。"

# 3. 创建简单的启动脚本 (可选，方便运维直接运行)
cat <<EOF > "${RELEASE_DIR}/bin/start.sh"
#!/bin/bash
# 自动加载 .env 并启动应用
python3 lib/$(basename "${OUTPUT_PEX}")
EOF
chmod +x "${RELEASE_DIR}/bin/start.sh"

# 4. 执行压缩
echo "正在生成 ZIP 压缩包..."
cd "$(pwd)/dist" || exit
zip -r "$ZIP_NAME" "$(basename "${RELEASE_DIR}")"

if [ -f "$ZIP_NAME" ]; then
    echo "================================================"
    echo "所有发布任务完成！"
    echo "最终发布包: $(pwd)/$ZIP_NAME"
    echo "================================================"
else
    echo "ZIP 压缩失败，请确认系统是否安装了 'zip' 命令。"
fi
