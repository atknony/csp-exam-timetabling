FROM python:3.10

# 1. Set up a non-root user as required by Hugging Face Spaces security policies
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements first and install them (granting permissions to the user)
# This optimizes the Docker build cache
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the project files into the container
COPY --chown=user . /app

# 5. Expose the mandatory Hugging Face port
EXPOSE 7860

# 6. Start the FastAPI application
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]