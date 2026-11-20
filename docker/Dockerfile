FROM python:3.12-alpine
WORKDIR /srv
RUN addgroup -S appuser && adduser -S -G appuser -u 10001 appuser
COPY app/ ./app/
USER appuser
EXPOSE 8080
CMD ["python", "-m", "app.server"]
