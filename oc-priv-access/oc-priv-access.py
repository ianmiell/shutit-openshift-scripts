import minishift

# Creates a bespoke scc and assigns it to a user

s1 = minishift.startup()

# Log in as admin
minishift.login_as_root(s1)

# Cleanup
s1.send('oc delete scc cluster-admin-scc || true')
s1.send('oc delete sa myclusteradminsa || true')
s1.send('oc delete is bespokescc -n bespokesccprj || true')
s1.send('oc delete bc bespokescc -n bespokesccprj || true')
s1.send('oc delete dc bespokescc -n bespokesccprj || true')
s1.send('oc delete project bespokesccprj || true')
# Wait until project has def gone.
s1.send_until("oc project 2> /dev/null | grep bespokesccprj | wc -l | awk '{print $1}'",'0')
# Create project
s1.send("oc adm new-project bespokesccprj --admin='developer'")
s1.send("oc project bespokesccprj")

# Create custom SCC - this is restricted
# Looked at privileged scc with 'oc edit scc privileged' and took groups item
s1.send_file('/tmp/scc.yaml',"""allowHostDirVolumePlugin: false
allowHostIPC: false
allowHostNetwork: false
allowHostPID: false
allowHostPorts: false
allowPrivilegedContainer: false
allowedCapabilities: []
apiVersion: v1
defaultAddCapabilities: []
fsGroup:
  type: MustRunAs
kind: SecurityContextConstraints
metadata:
  annotations:
    kubernetes.io/description: restricted denies access to all host features and requires
      pods to be run with a UID, and SELinux context that are allocated to the namespace.  This
      is the most restrictive SCC and it is used by default for authenticated users.
  creationTimestamp: 2017-09-15T15:13:40Z
  name: cluster-admin-scc
  resourceVersion: "275"
  selfLink: /api/v1/securitycontextconstraints/restricted
  uid: 74894f31-9a28-11e7-a15a-3e46e2387245
priority: null
readOnlyRootFilesystem: false
requiredDropCapabilities:
- KILL
- MKNOD
- SYS_CHROOT
- SETUID
- SETGID
runAsUser:
  type: MustRunAsRange
seLinuxContext:
  type: MustRunAs
supplementalGroups:
  type: RunAsAny
volumes:
- configMap
- downwardAPI
- emptyDir
- persistentVolumeClaim
- projected
- secret""")
s1.send('oc create -f /tmp/scc.yaml')

# Create a service account.
s1.send('oc create sa myclusteradminsa')
# Add the new custom SCC to this service account.
s1.send('oc adm policy add-scc-to-user cluster-admin-scc -z myclusteradminsa')
# Bind this sa (which is tied to this project) to the cluster-admin role.
# TODO: make the permissions more granular.
s1.send('oc adm policy add-cluster-role-to-user cluster-admin cluster-admin system:serviceaccount:bespokesccprj:myclusteradminsa')

# Log in as developer
minishift.login_as_developer(s1)

# Enter project.
s1.send("oc project bespokesccprj")

# TODO: Add the python libraries (pip) to the client
# Create an image stream from centos base that 
# TODO: remove need for kubectl by using sa secrets that are certs.
s1.send("""oc new-build --dockerfile 'FROM centos:7
RUN curl -L -s https://github.com/openshift/origin/releases/download/v3.6.0/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit.tar.gz | tar -zxvf - && cp */oc /usr/local/bin
RUN curl -L -s https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl > /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl
RUN mkdir /.kube && chmod 777 /.kube
CMD sleep 999999' --to bespokescc:latest""")
s1.send_until("oc get --no-headers is bespokescc 2> /dev/null | grep '^bespokescc ' | grep latest | wc -l | awk '{print $1}'",'1')
s1.send('oc new-app --image-stream=bespokescc')
s1.send("""oc patch dc bespokescc -p '{"spec":{"template":{"spec":{"serviceAccountName": "myclusteradminsa"}}}}'""")
s1.send_until("""oc get --no-headers pods | grep -v build | grep Running | grep bespokescc | wc -l | awk '{print $1}'""",'1')
s1.login('''oc exec -ti $(oc get --no-headers pods | grep -v build | grep Running | grep bespokescc | awk '{print $1}') bash''')
s1.send('kubectl config set-credentials myclusteradminsa --token $(cat /var/run/secrets/kubernetes.io/serviceaccount/token) --user myclusteradminsa')
s1.pause_point('logged in with cluster privileges!')
s1.logout()
