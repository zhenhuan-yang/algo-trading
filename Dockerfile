FROM python:3.11-slim

WORKDIR /app

# 从官方镜像复制 uv 二进制，速度快、镜像小
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先装依赖（利用 Docker 层缓存，代码改动不会重装包）
# --no-install-project：跳过安装项目本身，src/ 通过 PYTHONPATH 直接访问
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 复制源码
COPY src/ ./src/
COPY scripts/ ./scripts/

# algo_trading 包在 src/ 下
ENV PYTHONPATH=/app/src

CMD ["uv", "run", "python", "scripts/run_rsi_divergence.py"]
