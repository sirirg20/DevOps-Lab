// Runs once at startup. Creates the admin account from environment variables and
// locks Jenkins down: only logged-in users can do anything, no anonymous read.
import jenkins.model.Jenkins
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm

def env = System.getenv()
def adminUser = env['JENKINS_ADMIN_USER'] ?: 'admin'
def adminPassword = env['JENKINS_ADMIN_PASSWORD']

if (!adminPassword) {
    // Refuse to continue silently: with the setup wizard disabled, Jenkins would
    // otherwise start without any authentication.
    throw new IllegalStateException('JENKINS_ADMIN_PASSWORD is not set; refusing to start unsecured')
}

def jenkins = Jenkins.get()
def realm = new HudsonPrivateSecurityRealm(false)

// Idempotent: the account lives in the persisted home directory, so on later
// restarts it already exists and is left alone (changing the env var does not
// change an existing password; do that in the UI).
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
