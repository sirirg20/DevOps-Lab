FROM jenkins/jenkins:lts-jdk17

# Unattended setup: no wizard; the init script creates the admin user.
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

# Lab only: the sample repository is a read-only bind mount owned by your host
# user, which git would otherwise reject as "dubious ownership".
USER root
RUN git config --system --add safe.directory '*'
USER jenkins

COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY --chown=jenkins:jenkins init.groovy.d/ /usr/share/jenkins/ref/init.groovy.d/
