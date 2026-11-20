#!/bin/sh
set -eu
mkdir -p "$JENKINS_HOME/plugins" "$JENKINS_HOME/init.groovy.d"
cp -n /opt/jenkins/plugins/* "$JENKINS_HOME/plugins/" || true
cp /opt/jenkins/init.groovy "$JENKINS_HOME/init.groovy.d/lab4.groovy"
git config --global user.name Rishav
git config --global user.email 174773787+Rishav23av@users.noreply.github.com
git config --global init.defaultBranch main
git config --global --add safe.directory /workspace
exec java -Djenkins.install.runSetupWizard=false -jar /opt/jenkins/jenkins.war --httpPort=8080
