// Creates the admin account from environment variables and locks Jenkins down:
// only logged-in users can do anything, and anonymous read is off.
import jenkins.model.Jenkins
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm

def env = System.getenv()
def adminUser = env['JENKINS_ADMIN_USER'] ?: 'admin'
def adminPassword = env['JENKINS_ADMIN_PASSWORD']

if (!adminPassword) {
    // With the setup wizard disabled, a missing password would leave Jenkins open.
    throw new IllegalStateException('JENKINS_ADMIN_PASSWORD is not set; refusing to start unsecured')
}

def jenkins = Jenkins.get()
def realm = new HudsonPrivateSecurityRealm(false)

if (realm.getUser(adminUser) == null) {
    realm.createAccount(adminUser, adminPassword)
    println("01-admin-user: created account '${adminUser}'")
} else {
    println("01-admin-user: account '${adminUser}' already exists, leaving it unchanged")
}
jenkins.setSecurityRealm(realm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
jenkins.setAuthorizationStrategy(strategy)

jenkins.save()
