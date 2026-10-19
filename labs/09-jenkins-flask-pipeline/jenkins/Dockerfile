FROM jenkins/jenkins:lts-jdk17

# Unattended setup: no wizard; the init script creates the admin user.
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# Build tooling lives in the image, not installed by hand into a running container,
# so it survives rebuilds: Python with venv and pip for the pipeline's Build stage.
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 # Lab only: the repository is a read-only bind mount owned by your host user,
 # which git would otherwise reject as "dubious ownership".
 && git config --system --add safe.directory '*'
USER jenkins

COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY --chown=jenkins:jenkins init.groovy.d/ /usr/share/jenkins/ref/init.groovy.d/
