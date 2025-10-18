FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /backend
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./backend ./backend
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]