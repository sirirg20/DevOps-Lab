FROM jenkins/jenkins:lts-jdk17

# Unattended mode: skip the interactive setup wizard. The init script in
# init.groovy.d creates the admin user, so Jenkins is never left open.
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY --chown=jenkins:jenkins init.groovy.d/ /usr/share/jenkins/ref/init.groovy.d/
