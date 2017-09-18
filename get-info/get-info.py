import minishift

# Creates a bespoke scc and assigns it to a user

s1 = minishift.startup()

# Log in as admin
minishift.login_as_root(s1)

# Get a clusterrole
s1.send('oc get clusterrole')
# Describe a specific clusterrole
s1.send('oc describe clusterrole view')

# Get a clusterrolebinding, showing users/roles/groups associated with it
s1.send('oc get clusterrolebinding registry-registry-role')
# Above info, + verbs, resources api groups etc
s1.send('oc describe clusterrolebinding registry-registry-role')
# Ditto for admin
s1.send('oc describe clusterrolebinding admin')

# Find out who can perform a specific action
s1.send('oc adm policy who-can list roles')
# Find out who can perform a specific action all over the cluster
s1.send('oc adm policy who-can list roles --all-namespaces')

# Project level
