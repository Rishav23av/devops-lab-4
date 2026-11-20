import jenkins.model.Jenkins
import jenkins.model.JenkinsLocationConfiguration
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import hudson.plugins.git.GitSCM

def instance=Jenkins.get()
def realm=new HudsonPrivateSecurityRealm(false)
realm.createAccount('rishav',new File('/run/secrets/jenkins-admin-password').text.trim())
instance.setSecurityRealm(realm)
def auth=new FullControlOnceLoggedInAuthorizationStrategy()
auth.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(auth)
instance.setNumExecutors(1)
instance.setLabelString('ubuntu2404')
instance.setSystemMessage('Rishav | Roll no. 2301730245 | DevOps Lab 4')
JenkinsLocationConfiguration.get().setUrl('http://localhost:8089/')
def job=instance.getItem('devops-lab-4') ?: instance.createProject(WorkflowJob,'devops-lab-4')
def scm=new GitSCM('https://github.com/Rishav23av/devops-lab-4.git')
scm.branches=[new hudson.plugins.git.BranchSpec('*/main')]
def definition=new CpsScmFlowDefinition(scm,'security/Jenkinsfile')
definition.setLightweight(true)
job.setDefinition(definition)
job.save()
instance.save()
