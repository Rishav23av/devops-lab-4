ARG TOOLING_IMAGE=rishav-lab4-tooling:local
FROM ${TOOLING_IMAGE} AS tooling
FROM ubuntu:24.04
ARG TARGETARCH
ENV DEBIAN_FRONTEND=noninteractive HOME=/var/jenkins_home JENKINS_HOME=/var/jenkins_home
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 curl ca-certificates openjdk-21-jre-headless fontconfig \
    && if [ "$TARGETARCH" = arm64 ]; then editor_arch=arm64; else editor_arch=x64; fi \
    && curl -fL "https://update.code.visualstudio.com/latest/linux-deb-${editor_arch}/stable" -o /tmp/code.deb \
    && apt-get install -y --no-install-recommends /tmp/code.deb \
    && rm /tmp/code.deb && rm -rf /var/lib/apt/lists/*
COPY --from=tooling /usr/local/bin/docker /usr/local/bin/docker
COPY --from=tooling /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins
COPY --from=tooling /usr/share/jenkins/jenkins.war /opt/jenkins/jenkins.war
COPY --from=tooling /usr/share/jenkins/ref/plugins /opt/jenkins/plugins
COPY jenkins/init.groovy /opt/jenkins/init.groovy
COPY jenkins/start.sh /opt/jenkins/start.sh
RUN chmod +x /opt/jenkins/start.sh
EXPOSE 8080
ENTRYPOINT ["/opt/jenkins/start.sh"]
